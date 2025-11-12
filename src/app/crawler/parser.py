from bs4 import BeautifulSoup
from typing import Optional
import re
from src.app.models.book import Book
from datetime import datetime, timezone
from urllib.parse import urljoin


class BookParser:
    def __init__(self, base_url: str = "https://books.toscrape.com"):
        self.base_url = base_url

    def parse_book_page(self, html: str, url: str) -> Optional[Book]:
        try:
            soup = BeautifulSoup(html, "lxml")

            name = self._extract_title(soup)
            description = self._extract_description(soup)
            category = self._extract_category(soup)
            currency, price_excl_tax = self._extract_currency_and_price_excl_tax(soup)
            price_incl_tax = self._extract_price_incl_tax(soup)
            availability = self._extract_availability(soup)
            num_reviews = self._extract_num_reviews(soup)
            rating = self._extract_rating(soup)
            image_url = self._extract_image_url(soup, url)

            book = Book(
                name=name,
                description=description,
                category=category,
                price_excl_tax=price_excl_tax,
                currency=currency,
                price_incl_tax=price_incl_tax,
                availability=availability,
                num_reviews=num_reviews,
                rating=rating,
                image_url=image_url,
                source_url=url,
                crawl_timestamp=datetime.now(timezone.utc),
                crawl_status="success",
                raw_html=html,
            )

            return book

        except Exception as e:
            print(f"Error parsing book page {url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        h1 = soup.find("h1")
        if not h1:
            raise ValueError("Title not found")
        return h1.text.strip()

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        desc_header = soup.find("div", id="product_description")
        if not desc_header:
            return None

        desc_p = desc_header.find_next_sibling("p")
        if desc_p and desc_p.text.strip():
            return desc_p.text.strip()
        return None

    def _extract_category(self, soup: BeautifulSoup) -> str:
        breadcrumb = soup.find("ul", class_="breadcrumb")
        if not breadcrumb:
            raise ValueError("Category breadcrumb not found")

        links = breadcrumb.find_all("a")
        if len(links) >= 3:
            # Third link is the category (Home > Books > Category)
            return links[2].text.strip()

        raise ValueError("Category not found in breadcrumb")

    def _extract_currency_and_price_excl_tax(
        self, soup: BeautifulSoup
    ) -> tuple[str, float]:
        currency, price = self._extract_currency_and_price_from_table(
            soup, "Price (excl. tax)"
        )
        return currency, price

    def _extract_price_incl_tax(self, soup: BeautifulSoup) -> float:
        _, price = self._extract_currency_and_price_from_table(
            soup, "Price (incl. tax)"
        )
        return price

    def _extract_currency_and_price_from_table(
        self, soup: BeautifulSoup, label: str
    ) -> tuple[str, float]:
        table = soup.find("table", class_="table-striped")
        if not table:
            raise ValueError("Product information table not found")

        # Find the row with matching label
        for row in table.find_all("tr"):
            th = row.find("th")
            if th and label in th.text:
                td = row.find("td")
                if td:
                    # Extract number from text
                    price_text: str = td.text.strip()
                    price_str = re.sub(r"[^\d.]", "", price_text)
                    currency = price_text.split(price_str)[0].strip()
                    return currency, float(price_str)

        raise ValueError(f"Price '{label}' not found in table")

    def _extract_availability(self, soup: BeautifulSoup) -> str:
        avail = soup.find("p", class_="availability")
        if not avail:
            raise ValueError("Availability not found")

        return avail.text.strip().replace("\n", " ").replace("  ", " ")

    def _extract_num_reviews(self, soup: BeautifulSoup) -> int:
        table = soup.find("table", class_="table-striped")
        if not table:
            return 0

        for row in table.find_all("tr"):
            th = row.find("th")
            if th and "Number of reviews" in th.text:
                td = row.find("td")
                if td:
                    return int(td.text.strip())

        return 0

    def _extract_rating(self, soup: BeautifulSoup) -> str:
        rating_p = soup.find("p", class_="star-rating")
        if not rating_p:
            raise ValueError("Rating not found")

        # The rating is in the class name (ex. "star-rating Three")
        classes = rating_p.get("class")
        if not isinstance(classes, list):
            classes = []
        for cls in classes:
            if cls in ["One", "Two", "Three", "Four", "Five"]:
                return cls

        raise ValueError("Rating class not found")

    def _extract_image_url(self, soup: BeautifulSoup, current_url: str) -> str:
        img = soup.find("img")
        if not img or not img.get("src"):
            raise ValueError("Image not found")

        img_src = img["src"]
        if not isinstance(img_src, str):
            raise TypeError("Expected src to be a string")

        return urljoin(current_url, img_src)

    def parse_catalogue_page(self, html: str, current_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        book_urls = []

        articles = soup.find_all("article", class_="product_pod")

        for article in articles:
            h3 = article.find("h3")
            if h3:
                a = h3.find("a")
                if a and a.get("href"):
                    relative_url = a["href"]
                    if not isinstance(relative_url, str):
                        continue
                    book_url = urljoin(current_url, relative_url)
                    book_urls.append(book_url)

        return book_urls

    def get_next_page_url(self, html: str, current_url: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")

        # Find "next" page item
        next_item = soup.find("li", class_="next")
        if not next_item:
            return None

        a = next_item.find("a")
        if not a or not a.get("href"):
            return None

        next_relative = a["href"]
        if not isinstance(next_relative, str):
            return None

        return urljoin(current_url, next_relative)
