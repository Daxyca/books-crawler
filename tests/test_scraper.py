import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from src.app.crawler.scraper import BookScraper
from src.app.models.book import Book


@pytest.fixture
def scraper():
    return BookScraper()


@pytest.mark.asyncio
async def test_fetch_with_retry_success(scraper):
    mock_response = Mock()
    mock_response.text = "OK"
    mock_response.raise_for_status.return_value = None
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    text = await scraper.fetch_with_retry(mock_client, "https://example.com")
    assert text == "OK"
    assert scraper.stats["errors"] == 0


@pytest.mark.asyncio
async def test_fetch_with_retry_failure(scraper):
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("Network error")

    text = await scraper.fetch_with_retry(mock_client, "https://example.com")
    assert text is None
    assert scraper.stats["errors"] == 1


@pytest.mark.asyncio
async def test_get_all_book_urls(scraper, sample_catalogue_html):
    mock_client = AsyncMock()

    with patch.object(
        scraper, "fetch_with_retry", side_effect=[sample_catalogue_html, None]
    ):
        urls = await scraper.get_all_book_urls(mock_client)
        assert "https://books.toscrape.com/catalogue/book1.html" in urls
        assert scraper.stats["pages_crawled"] == 1
        assert scraper.stats["books_found"] == 2


@pytest.mark.asyncio
async def test_crawl_book_success(scraper, sample_book_html):
    mock_client = AsyncMock()
    with patch.object(scraper, "fetch_with_retry", return_value=sample_book_html):
        book = await scraper.crawl_book(mock_client, "https://example.com/book1")
        assert isinstance(book, Book)
        assert scraper.stats["books_crawled"] == 1


@pytest.mark.asyncio
async def test_crawl_book_failure(scraper):
    mock_client = AsyncMock()
    with patch.object(scraper, "fetch_with_retry", return_value="<html></html>"):
        book = await scraper.crawl_book(mock_client, "https://example.com/book1")
        assert book is None
        assert scraper.stats["errors"] == 1


@pytest.mark.asyncio
async def test_crawl_all_books(scraper):
    with (
        patch.object(
            scraper, "get_all_book_urls", return_value=["https://example.com/book1"]
        ),
        patch.object(
            scraper,
            "crawl_book",
            return_value=Book(
                name="Test Book",
                description="Desc",
                category="Fiction",
                price_excl_tax=10.0,
                currency="£",
                price_incl_tax=12.0,
                availability="In stock",
                num_reviews=5,
                rating="Three",
                image_url="https://example.com/image.jpg",
                source_url="https://example.com/book1",
                crawl_timestamp=datetime.now(timezone.utc),
                crawl_status="success",
                raw_html="<html></html>",
            ),
        ),
    ):
        books = await scraper.crawl_all_books()
        assert len(books) == 1
