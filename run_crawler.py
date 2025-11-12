import asyncio
from src.app.utils.db import Database
from src.app.crawler.scraper import BookScraper
from src.app.crawler.storage import BookStorage


async def main():
    print("\n" + "-" * 70)
    print("BOOKS CRAWLER - STARTING UP")
    print("-" * 70 + "\n")

    try:
        # Step 1: Connect to database
        print("Connecting to MongoDB...")
        await Database.connect()
        db = Database.get_db()

        # Step 2: Initialize storage and create indexes
        storage = BookStorage(db)
        await storage.ensure_indexes()

        # Step 3: Run crawler
        scraper = BookScraper()
        books = await scraper.crawl_all_books()

        if not books:
            print("No books were crawled!")
            return

        # Step 4: Save to database
        await storage.insert_many_books(books)

        # Step 5: Verify saved data
        total_in_db = await storage.count_books()
        print(f"Total books in database: {total_in_db}\n")

        # Show sample book
        if books:
            print("Sample book:")
            sample = books[0]
            print(f"   Title: {sample.name}")
            print(f"   Category: {sample.category}")
            print(f"   Price: £{sample.price_incl_tax}")
            print(f"   Rating: {sample.rating}")
            print(f"   URL: {sample.source_url}")

        print("\n" + "-" * 70)
        print("CRAWLER COMPLETED SUCCESSFULLY")
        print("-" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\nCrawler interrupted by user")

    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await Database.close()


if __name__ == "__main__":
    asyncio.run(main())
