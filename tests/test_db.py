import pytest
from src.app.utils.db import Database, get_database


@pytest.mark.asyncio
async def test_get_db_raises_runtime_error_when_not_connected():
    expected_error_message = "Database not connected. Call connect() first."

    with pytest.raises(RuntimeError) as excinfo:
        Database.get_db()

    assert str(excinfo.value) == expected_error_message


@pytest.mark.asyncio
async def test_db_connect_and_close():
    await Database.connect()
    db = Database.get_db()
    assert db.name is not None
    await Database.close()


@pytest.mark.asyncio
async def test_get_database():
    await Database.connect()
    db = await get_database()
    assert db.name is not None
    await Database.close()
