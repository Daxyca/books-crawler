import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from motor.motor_asyncio import AsyncIOMotorClient
from src.app.utils.config import get_settings
from src.app.crawler.storage import BookStorage
from src.app.crawler.parser import BookParser
from src.app.crawler.scraper import BookScraper


@pytest.fixture
def settings():
    return get_settings()


@pytest_asyncio.fixture
async def mongo_client():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    yield client
    await client.drop_database("test_books_db")
    client.close()


@pytest.fixture
def mock_collection():
    collection = AsyncMock()
    return collection


@pytest.fixture
def storage(mongo_client, mock_collection):
    db = mongo_client["test_books_db"]
    storage_instance = BookStorage(db)
    storage_instance.books_collection = mock_collection
    return storage_instance


@pytest.fixture
def parser():
    return BookParser(base_url="https://books.toscrape.com")


@pytest.fixture
def scraper():
    return BookScraper()


@pytest.fixture
def sample_book_html():
    return """
    <html>
    <head><title>Test Book</title></head>
    <body>
    <h1>Test Book Name</h1>
    <div id="product_description"></div>
    <p>This is a test book description.</p>
    <ul class="breadcrumb">
    <li><a href="/">Home</a></li>
    <li><a href="/books">Books</a></li>
    <li><a href="/books/fiction">Fiction</a></li>
    </ul>
    <table class="table-striped">
    <tr><th>Price (excl. tax)</th><td>£10.00</td></tr>
    <tr><th>Price (incl. tax)</th><td>£12.00</td></tr>
    <tr><th>Number of reviews</th><td>5</td></tr>
    </table>
    <p class="availability">In stock</p>
    <p class="star-rating Three"></p>
    <img src="media/image.jpg"/>
    </body>
    </html>
    """


@pytest.fixture
def sample_catalogue_html():
    return """
    <html>
    <body>
    <article class="product_pod">
    <h3><a href="book1.html">Book 1</a></h3>
    </article>
    <article class="product_pod">
    <h3><a href="book2.html">Book 2</a></h3>
    </article>
    <li class="next"><a href="page2.html">next</a></li>
    </body>
    </html>
    """
