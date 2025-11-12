import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from motor.motor_asyncio import AsyncIOMotorClient
from src.app.utils.config import get_settings
from src.app.crawler.storage import BookStorage


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
    storage_instance.collection = mock_collection
    return storage_instance
