from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from src.app.utils.config import get_settings


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls):
        try:
            settings = get_settings()
            # Create async MongoDB client
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,
            )

            # Get database instance
            cls.db = cls.client[settings.mongodb_db_name]

            # Test connection
            await cls.client.admin.command("ping")
            print(f"Connected to MongoDB: {settings.mongodb_db_name}")

        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()
            print("Closed MongoDB connection")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.db


async def get_database() -> AsyncIOMotorDatabase:
    return Database.get_db()
