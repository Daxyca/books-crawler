import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from src.app.models.book import Book

SAMPLE_BOOK = Book(
    name="Test Book",
    description="A test book",
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
)


@pytest.mark.asyncio
async def test_ensure_indexes(storage):
    await storage.ensure_indexes()
    assert storage.collection.create_index.call_count >= 1


@pytest.mark.asyncio
async def test_insert_book_new(storage):
    storage.collection.update_one.return_value.upserted_id = "abc123"
    storage.collection.update_one.return_value.modified_count = 0

    result = await storage.insert_book(SAMPLE_BOOK)
    assert result == "abc123"
    storage.collection.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_insert_book_updated(storage):
    storage.collection.update_one.return_value.upserted_id = None
    storage.collection.update_one.return_value.modified_count = 1

    result = await storage.insert_book(SAMPLE_BOOK)
    assert result == "updated"


@pytest.mark.asyncio
async def test_insert_book_none(storage):
    storage.collection.update_one.return_value.upserted_id = None
    storage.collection.update_one.return_value.modified_count = 0

    result = await storage.insert_book(SAMPLE_BOOK)
    assert result is None


@pytest.mark.asyncio
async def test_insert_many_books(storage):
    storage.insert_book = AsyncMock(side_effect=["1", "updated", None])
    books = [SAMPLE_BOOK, SAMPLE_BOOK, SAMPLE_BOOK]
    await storage.insert_many_books(books)
    assert storage.insert_book.call_count == 3


@pytest.mark.asyncio
async def test_get_book_by_url_found(storage):
    storage.collection.find_one.return_value = SAMPLE_BOOK.model_dump()
    book = await storage.get_book_by_url(SAMPLE_BOOK.source_url)
    assert book.name == SAMPLE_BOOK.name


@pytest.mark.asyncio
async def test_get_book_by_url_not_found(storage):
    storage.collection.find_one.return_value = None
    book = await storage.get_book_by_url("nonexistent")
    assert book is None


@pytest.mark.asyncio
async def test_get_books_paginated(storage):
    storage.get_books = AsyncMock(return_value=[SAMPLE_BOOK])
    storage.count_books = AsyncMock(return_value=10)

    result = await storage.get_books_paginated(page=1, page_size=5)
    assert result["total"] == 10
    assert result["books"] == [SAMPLE_BOOK]
    assert result["total_pages"] == 2


@pytest.mark.asyncio
async def test_count_books(storage):
    storage.collection.count_documents.return_value = 7
    total = await storage.count_books()
    assert total == 7


@pytest.mark.asyncio
async def test_clear_all_books(storage):
    storage.collection.delete_many.return_value.deleted_count = 3
    await storage.clear_all_books()
    storage.collection.delete_many.assert_called_once()
