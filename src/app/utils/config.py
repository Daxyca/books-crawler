from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_url: str = "mongodb://admin:password123@localhost:27017"
    mongodb_db_name: str = "books_db"

    # Crawler Configuration
    base_url: str = "https://books.toscrape.com"
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 2

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
