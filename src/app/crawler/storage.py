from motor.motor_asyncio import AsyncIOMotorDatabase
from src.app.models.book import Book
from typing import List, Optional
from pymongo import ASCENDING, DESCENDING


class BookStorage:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["books"]

    async def ensure_indexes(self):
        print("Creating database indexes...")

        # Unique index on source_url (prevents duplicate books)
        await self.collection.create_index(
            [("source_url", ASCENDING)], unique=True, name="source_url_unique"
        )

        # Indexes for query patterns
        await self.collection.create_index(
            [("category", ASCENDING)], name="category_index"
        )
        await self.collection.create_index(
            [("price_incl_tax", ASCENDING)], name="price_index"
        )
        await self.collection.create_index(
            [("num_reviews", ASCENDING)], name="reviews_index"
        )
        await self.collection.create_index([("rating", ASCENDING)], name="rating_index")
        await self.collection.create_index(
            [("crawl_timestamp", DESCENDING)], name="timestamp_index"
        )

        print("Indexes created successfully\n")

    async def insert_book(self, book: Book) -> Optional[str]:
        try:
            # Convert Pydantic model to dict
            book_dict = book.model_dump(exclude={"id"})

            # Upsert: update if exists, insert if not
            result = await self.collection.update_one(
                {"source_url": book.source_url},
                {"$set": book_dict},
                upsert=True,
            )

            if result.upserted_id:
                return str(result.upserted_id)
            elif result.modified_count > 0:
                return "updated"
            else:
                return None

        except Exception as e:
            print(f"Error inserting book {book.name}: {e}")
            return None

    async def insert_many_books(self, books: List[Book]) -> None:
        stats = {"inserted": 0, "updated": 0, "errors": 0}

        print(f"\nSaving {len(books)} books to database...")

        for book in books:
            result = await self.insert_book(book)

            if result and result != "updated":
                stats["inserted"] += 1
            elif result == "updated":
                stats["updated"] += 1
            else:
                stats["errors"] += 1

        print("Saved to database:")
        print(f"  New books inserted: {stats['inserted']}")
        print(f"  Existing books updated: {stats['updated']}")
        print(f"  Errors: {stats['errors']}\n")

    async def get_book_by_url(self, url: str) -> Optional[Book]:
        doc = await self.collection.find_one({"source_url": url})
        if doc:
            # Convert MongoDB document to Pydantic model
            return Book(**doc)
        return None

    async def get_books(self, skip: int = 0, limit: int = 100) -> List[Book]:
        books = []
        cursor = self.collection.find({}).skip(skip).limit(limit)

        async for doc in cursor:
            try:
                books.append(Book(**doc))
            except Exception as e:
                print(f"Error loading book: {e}")

        return books

    async def get_books_paginated(self, page: int = 1, page_size: int = 20) -> dict:
        skip = (page - 1) * page_size
        books = await self.get_books(skip=skip, limit=page_size)
        total = await self.count_books()
        total_pages = (total + page_size - 1) // page_size

        return {
            "books": books,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def count_books(self) -> int:
        return await self.collection.count_documents({})

    async def clear_all_books(self):
        result = await self.collection.delete_many({})
        print(f"Deleted {result.deleted_count} books from database")
