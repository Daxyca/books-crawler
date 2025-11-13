# Books Crawler

## Overview

Books Crawler is a comprehensive web crawling and monitoring system for books.toscrape.com with change detection, scheduler, and RESTful API.

## Contents

1. [Features](#features)
   - [Robust Web Crawler](#robust-web-crawler)
   - [Change Detection \& Scheduling](#change-detection--scheduling)
   - [Secure RESTful API](#secure-restful-api)
1. [Requirements](#requirements)
   - [Dependencies](#dependencies)
   - [Development Dependencies](#development-dependencies)
1. [Setup Instructions](#setup-instructions)
1. [Usage](#usage)
   - [Run Basic Crawler](#run-basic-crawler)
   - [Run Scheduler with Change Detection](#run-scheduler-with-change-detection)
   - [Run API Server](#run-api-server)
1. [API Endpoints](#api-endpoints)
   - [Books Endpoints](#books-endpoints)
     - [`GET /books`](#get-books)
     - [`GET /books/{book_id}`](#get-booksbook_id)
   - [Changes Endpoints](#changes-endpoints)
     - [`GET /changes`](#get-changes)
1. [Sample Run Logs](#sample-run-logs)
   - [Crawler](#crawler)
   - [Scheduler](#scheduler)

## Features

### Robust Web Crawler

- Async concurrent crawling (10 requests at once)
- Automatic pagination handling (all 50 catalogue pages)
- Retry logic with exponential backoff
- MongoDB storage with indexing
- Raw HTML snapshots for fallback
- Pydantic data validation
- Comprehensive error handling

### Change Detection & Scheduling

- Smart change detection (only updates when data actually changes)
- Daily automated scheduling with APScheduler
- Log detected changes to MongoDB
- JSON & CSV report generation
- Summary statistics for detected change
- Configurable schedule (cron expressions)

### Secure RESTful API

- FastAPI with auto-generated Swagger docs
- API key authentication
- Rate limiting (100 requests/hour)
- Advanced filtering (category, price range, rating)
- Pagination
- Sorting (by price, rating, reviews)
- CORS support

## Requirements

- **Python**: 3.13+ (developed with 3.13.9)
- **Docker**: For MongoDB
- **UV**: Modern Python package manager (recommended) or pip

### Dependencies

| Package           | Version   |
| ----------------- | --------- |
| apscheduler       | >=3.11.1  |
| beautifulsoup4    | >=4.14.2  |
| fastapi           | >=0.121.1 |
| httpx             | >=0.28.1  |
| lxml              | >=6.0.2   |
| motor             | >=3.7.1   |
| pydantic          | >=2.12.4  |
| pydantic-settings | >=2.11.0  |
| python-dotenv     | >=1.2.1   |
| slowapi           | >=0.1.9   |
| uvicorn[standard] | >=0.38.0  |

### Development Dependencies

| Package        | Version |
| -------------- | ------- |
| pytest         | >=8.4.2 |
| pytest-asyncio | >=1.2.0 |
| pytest-cov     | >=7.0.0 |

## Setup Instructions

1. Clone Repository

   ```bash
   git clone [<repo-url>](https://github.com/Daxyca/books-crawler.git)
   cd books-crawler
   ```

1. Install Dependencies

   **Option A: Using UV (Recommended)**

   ```bash
   uv venv

   uv pip install -e ".[dev]"
   ```

   **Option B: Using pip**

   ```bash
   python -m venv .venv

   pip install -e ".[dev]"
   ```

1. Activate Virtual Environment

   ```bash
   .venv\Scripts\activate  # Windows Command Prompt
   source .venv/Scripts/activate  # Git Bash/Linux/Mac
   ```

1. Start MongoDB

   ```bash
   # Start MongoDB and Mongo Express (web UI)
   docker compose up -d mongodb mongo-express

   # Verify MongoDB is running
   # Open http://localhost:8081 in browser
   ```

1. Configure Environment

   ```bash
   # Copy example environment file
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac

   # Edit .env with your settings (defaults work for local development)
   ```

## Usage

### Run Basic Crawler

```bash
# Crawl all books and store in MongoDB
python run_crawler.py
```

### Run Scheduler with Change Detection

```bash
# Daily schedule (runs at 2 AM UTC by default)
python run_scheduler.py

# Custom schedule (every hour)
python run_scheduler.py --cron "0 * * * *"

# Test mode (every 2 minutes)
python run_scheduler.py --test

# Run immediately then start schedule
python run_scheduler.py --now
```

### Run API Server

```bash
# Start FastAPI server
python run_api.py
```

**Access API:**

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

**Authentication:**
Include `X-API-Key` header in all requests:

```bash
curl -H "X-API-Key: your-secret-api-key-change-in-production" \
     "http://localhost:8000/books?page=1&page_size=20"
```

## API Endpoints

### Books Endpoints

#### `GET /books`

Get books with filtering, sorting, and pagination.

**Query Parameters:**

- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `category` (string): Filter by category
- `min_price` (float): Minimum price
- `max_price` (float): Maximum price
- `rating` (string): Filter by rating (One, Two, Three, Four, Five)
- `sort_by` (string): Sort field (rating, price, reviews)
- `sort_order` (string): Sort direction (asc, desc)

**Example:**

```bash
GET /books?category=Poetry&min_price=10&max_price=50&sort_by=price&page=1
```

#### `GET /books/{book_id}`

Get detailed information about a specific book.

### Changes Endpoints

#### `GET /changes`

Get recent changes with filtering.

**Query Parameters:**

- `page` (int): Page number
- `page_size` (int): Items per page (default: 50, max: 200)
- `change_type` (string): Filter by type (new_book, price_change, etc.)
- `days` (int): Changes from last N days

## Sample Run Logs

### Crawler

```
----------------------------------------------------------------------
BOOKS CRAWLER - STARTING UP
----------------------------------------------------------------------

Connecting to MongoDB...
Connected to MongoDB: books_db
Creating database indexes...
Indexes created successfully


----------------------------------------------------------------------
STARTING WEB CRAWLER
----------------------------------------------------------------------
Target: https://books.toscrape.com
Max concurrent requests: 10
Max retries per request: 3
----------------------------------------------------------------------


Discovering all book URLs...
  Crawling catalogue page 1...
    Found 20 books on page 1
  Crawling catalogue page 2...
    Found 20 books on page 2
  ...
  Crawling catalogue page 50...
    Found 20 books on page 50

Discovered 1000 total books across 50 pages

Starting concurrent crawl of 1000 books...
  (Processing 10 books at a time)

----------------------------------------------------------------------
CRAWLING STATISTICS
----------------------------------------------------------------------
Duration: 89.41 seconds
Catalogue pages crawled: 50
Books discovered: 1000
Books successfully crawled: 1000
Errors: 0
Crawling rate: 11.19 books/second
----------------------------------------------------------------------


Saving 1000 books to database...
Saved to database:
  New books inserted: 1000
  Existing books updated: 0
  Errors: 0

Total books in database: 1000

Sample book:
   Title: A Light in the Attic
   Category: Poetry
   Price: £51.77
   Rating: Three
   URL: https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html

----------------------------------------------------------------------
CRAWLER COMPLETED SUCCESSFULLY
----------------------------------------------------------------------

Closed MongoDB connection
```

### Scheduler

```
----------------------------------------------------------------------
BOOKS CRAWLER SCHEDULER
----------------------------------------------------------------------

Connecting to MongoDB...
Connected to MongoDB: books_db
Default schedule: Daily at 2:00 AM UTC

Scheduler started with cron: 0 2 * * *
  Next run: 2025-11-14 02:00:00+08:00
  Press Ctrl+C to stop

Scheduler is running. Press Ctrl+C to stop.


----------------------------------------------------------------------
SCHEDULED CRAWL STARTED - 2025-11-13T10:00:00.011319+00:00
----------------------------------------------------------------------


----------------------------------------------------------------------
STARTING WEB CRAWLER
----------------------------------------------------------------------
Target: https://books.toscrape.com
Max concurrent requests: 10
Max retries per request: 3
----------------------------------------------------------------------


Discovering all book URLs...
  Crawling catalogue page 1...
    Found 20 books on page 1
  Crawling catalogue page 2...
    Found 20 books on page 2
  ...
  Crawling catalogue page 50...
    Found 20 books on page 50

Discovered 1000 total books across 50 pages

Starting concurrent crawl of 1000 books...
  (Processing 10 books at a time)

----------------------------------------------------------------------
CRAWLING STATISTICS
----------------------------------------------------------------------
Duration: 90.24 seconds
Catalogue pages crawled: 50
Books discovered: 1000
Books successfully crawled: 1000
Errors: 0
Crawling rate: 11.08 books/second
----------------------------------------------------------------------


Detecting changes...
Change detection complete:
  New books: 0
  Updated books: 0
  Unchanged books: 1000
  Total changes: 0

No changes detected - all data is current!

----------------------------------------------------------------------
SCHEDULED CRAWL COMPLETED - 2025-11-13T10:01:22.546212+00:00
----------------------------------------------------------------------

Default schedule: Daily at 2:00 AM UTC

Scheduler started with cron: 0 2 * * *
  Next run: 2025-11-14 02:00:00+08:00
  Press Ctrl+C to stop

Scheduler is running. Press Ctrl+C to stop.
```
