import asyncio
import argparse
from src.app.utils.db import Database
from src.app.scheduler.scheduler import CrawlerScheduler


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run scheduled crawler")
    parser.add_argument(
        "--cron", type=str, help='Cron expression (e.g., "0 2 * * *" for daily at 2 AM)'
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run crawler immediately before starting schedule",
    )
    parser.add_argument(
        "--test", action="store_true", help="Test mode: run every 2 minutes"
    )
    args = parser.parse_args()

    print("\n" + "-" * 70)
    print("BOOKS CRAWLER SCHEDULER")
    print("-" * 70 + "\n")

    try:
        # Connect to database
        print("Connecting to MongoDB...")
        await Database.connect()

        # Initialize scheduler
        scheduler = CrawlerScheduler()

        # Run immediately
        if args.now:
            print("Running crawler immediately...\n")
            await scheduler.run_once_now()

        # Determine cron expression
        if args.test:
            # Every 2 minutes for testing
            cron = "*/2 * * * *"
            print("TEST MODE: Crawler will run every 2 minutes")
        elif args.cron:
            cron = args.cron
            print(f"Custom schedule: {cron}")
        else:
            # Default: Daily at 2 AM
            cron = "0 2 * * *"
            print("Default schedule: Daily at 2:00 AM UTC")

        # Start scheduler
        scheduler.start(cron)
        print("Scheduler is running. Press Ctrl+C to stop.\n")

        # Keep the script alive
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("\n\nStopping scheduler...")
        scheduler.stop()

    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await Database.close()
        print("Bye!\n")


if __name__ == "__main__":
    asyncio.run(main())
