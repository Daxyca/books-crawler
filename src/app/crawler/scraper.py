import httpx
import asyncio
from typing import Optional, List
from src.app.crawler.parser import BookParser
from src.app.models.book import Book
from src.app.utils.config import get_settings
import time


class BookScraper:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.base_url
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay
        self.timeout = settings.request_timeout
        self.max_concurrent = settings.max_concurrent_requests

        # Create parser instance
        self.parser = BookParser(base_url=self.base_url)

        # Semaphore to limit concurrent requests
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

        # Statistics
        self.stats = {
            "pages_crawled": 0,
            "books_found": 0,
            "books_crawled": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    async def fetch_with_retry(
        self, client: httpx.AsyncClient, url: str
    ) -> Optional[str]:
        for attempt in range(self.max_retries):
            try:
                # Use semaphore to limit concurrent requests
                async with self.semaphore:
                    response = await client.get(
                        url, timeout=self.timeout, follow_redirects=True
                    )
                    response.raise_for_status()  # Raise error for 4xx/5xx
                    return response.text

            except httpx.HTTPStatusError as e:
                print(f"    HTTP {e.response.status_code} for {url}")
                if e.response.status_code >= 500:
                    # Server error (5xx) - retry with backoff
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (
                            2**attempt if attempt < 4 else 16
                        )
                        print(
                            f"    Retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                else:
                    # Client error (4xx) - don't retry
                    break

            except (httpx.RequestError, httpx.TimeoutException) as e:
                print(f"    Request error for {url}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2**attempt if attempt < 4 else 16)
                    print(
                        f"    Retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue

            except Exception as e:
                print(f"    Unexpected error for {url}: {e}")
                break

        # All retries failed
        self.stats["errors"] += 1
        return None

    async def get_all_book_urls(self, client: httpx.AsyncClient) -> List[str]:
        all_book_urls = []
        current_url = f"{self.base_url}/catalogue/page-1.html"
        page_num = 1

        print("\nDiscovering all book URLs...")

        while current_url:
            print(f"  Crawling catalogue page {page_num}...")

            # Fetch catalogue page
            html = await self.fetch_with_retry(client, current_url)
            if not html:
                print(f"    Failed to fetch page {page_num}")
                break

            # Extract book URLs from this page
            book_urls = self.parser.parse_catalogue_page(html, current_url)
            all_book_urls.extend(book_urls)
            self.stats["pages_crawled"] += 1

            print(f"    Found {len(book_urls)} books on page {page_num}")

            # Check for next page
            next_url = self.parser.get_next_page_url(html, current_url)
            current_url = next_url
            page_num += 1

            await asyncio.sleep(0.5)

        self.stats["books_found"] = len(all_book_urls)
        print(
            f"\nDiscovered {len(all_book_urls)} total books across {page_num - 1} pages\n"
        )

        return all_book_urls

    async def crawl_book(self, client: httpx.AsyncClient, url: str) -> Optional[Book]:
        html = await self.fetch_with_retry(client, url)
        if not html:
            return None

        book = self.parser.parse_book_page(html, url)

        if book:
            self.stats["books_crawled"] += 1
        else:
            self.stats["errors"] += 1

        return book

    async def crawl_all_books(self) -> List[Book]:
        self.stats["start_time"] = time.time()

        print("\n" + "-" * 70)
        print("STARTING WEB CRAWLER")
        print("-" * 70)
        print(f"Target: {self.base_url}")
        print(f"Max concurrent requests: {self.max_concurrent}")
        print(f"Max retries per request: {self.max_retries}")
        print("-" * 70 + "\n")

        # Create async HTTP client
        async with httpx.AsyncClient() as client:
            book_urls = await self.get_all_book_urls(client)

            if not book_urls:
                print("No book URLs found!")
                return []

            print(f"Starting concurrent crawl of {len(book_urls)} books...")
            print(f"  (Processing {self.max_concurrent} books at a time)")

            tasks = [self.crawl_book(client, url) for url in book_urls]

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            books = [book for book in results if isinstance(book, Book)]

        self.stats["end_time"] = time.time()
        self._print_stats()

        return books

    def _print_stats(self):
        duration = self.stats["end_time"] - self.stats["start_time"]

        print("\n" + "-" * 70)
        print("CRAWLING STATISTICS")
        print("-" * 70)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Catalogue pages crawled: {self.stats['pages_crawled']}")
        print(f"Books discovered: {self.stats['books_found']}")
        print(f"Books successfully crawled: {self.stats['books_crawled']}")
        print(f"Errors: {self.stats['errors']}")

        if duration > 0:
            rate = self.stats["books_crawled"] / duration
            print(f"Crawling rate: {rate:.2f} books/second")

        print("-" * 70 + "\n")
