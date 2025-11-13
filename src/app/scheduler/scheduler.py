from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.app.utils.config import get_settings
from src.app.utils.db import Database
from src.app.crawler.scraper import BookScraper
from src.app.crawler.storage import BookStorage
from src.app.scheduler.change_detector import ChangeDetector
from datetime import datetime, timezone


class CrawlerScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def crawl_and_detect_changes(self):
        print("\n" + "-" * 70)
        print(f"SCHEDULED CRAWL STARTED - {datetime.now(timezone.utc).isoformat()}")
        print("-" * 70 + "\n")

        try:
            db = Database.get_db()
            storage = BookStorage(db)
            detector = ChangeDetector()

            # Run crawler
            scraper = BookScraper()
            new_books = await scraper.crawl_all_books()

            if not new_books:
                print("No books were crawled!")
                return

            # Detect changes
            print("\nDetecting changes...")
            all_changes = []
            stats = {"new_books": 0, "updated_books": 0, "unchanged_books": 0}

            for new_book in new_books:
                old_book = await storage.get_book_by_url(new_book.source_url)
                changes = detector.detect_changes(old_book, new_book)

                if changes:
                    all_changes.extend(changes)
                    if old_book is None:
                        stats["new_books"] += 1
                    else:
                        stats["updated_books"] += 1
                else:
                    stats["unchanged_books"] += 1

            print("Change detection complete:")
            print(f"  New books: {stats['new_books']}")
            print(f"  Updated books: {stats['updated_books']}")
            print(f"  Unchanged books: {stats['unchanged_books']}")
            print(f"  Total changes: {len(all_changes)}\n")

            if all_changes:
                print("Updating database...")

                # Only update changed/new books
                books_to_update = []
                for new_book in new_books:
                    old_book = await storage.get_book_by_url(new_book.source_url)
                    if old_book is None or detector.detect_changes(old_book, new_book):
                        books_to_update.append(new_book)

                if books_to_update:
                    await storage.insert_many_books(books_to_update)

                print("Logging changes...")
                await storage.log_changes(all_changes)

                print("Generating report...")
                report = detector.generate_report(all_changes)

                # Save reports
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

                json_report = detector.export_report_to_json(report)
                with open(f"logs/scheduled_report_{timestamp}.json", "w") as f:
                    f.write(json_report)

                csv_report = detector.export_report_to_csv(report)
                with open(f"logs/scheduled_report_{timestamp}.csv", "w") as f:
                    f.write(csv_report)

                print(f"Reports saved with timestamp: {timestamp}")

                # Send alert (optional)
                await self._send_alert(report)
            else:
                print("No changes detected - all data is current!")

            print("\n" + "-" * 70)
            print(
                f"SCHEDULED CRAWL COMPLETED - {datetime.now(timezone.utc).isoformat()}"
            )
            print("-" * 70 + "\n")

        except Exception as e:
            print(f"\nError in scheduled crawl: {e}")
            import traceback

            traceback.print_exc()

    async def _send_alert(self, report):
        if report.total_changes > 0:
            print(f"\nALERT: {report.total_changes} changes detected!")
            print(f"  New books: {report.new_books}")
            print(f"  Price changes: {report.price_changes}")
            print(f"  Availability changes: {report.availability_changes}")

    def start(self, cron_expression: Optional[str] = None):
        if self.is_running:
            print("Scheduler is already running!")
            return

        # Use provided cron or default from settings
        if cron_expression is None:
            # Default: Daily at configured hour
            settings = get_settings()
            hour = getattr(settings, "scheduler_hour", 2)
            minute = getattr(settings, "scheduler_minute", 0)
            cron_expression = f"{minute} {hour} * * *"

        # Parse cron expression
        trigger = CronTrigger.from_crontab("*/5 * * * *")
        self.scheduler.add_job(self.crawl_and_detect_changes, trigger=trigger)
        parts = cron_expression.split()
        if len(parts) == 5:
            minute, hour, day, month, day_of_week = parts

            trigger = CronTrigger(
                minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
            )
        else:
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        # Add job to scheduler
        self.scheduler.add_job(
            self.crawl_and_detect_changes,
            trigger=trigger,
            id="crawler_job",
            name="Scheduled Book Crawler",
            replace_existing=True,
        )

        # Start scheduler
        self.scheduler.start()
        self.is_running = True

        print(f"\nScheduler started with cron: {cron_expression}")
        print(f"  Next run: {self.scheduler.get_job('crawler_job').next_run_time}")  # type: ignore
        print("  Press Ctrl+C to stop\n")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("\nScheduler stopped\n")

    async def run_once_now(self):
        await self.crawl_and_detect_changes()
