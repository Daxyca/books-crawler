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

    # Scheduler Configuration
    scheduler_hour: int = 2
    scheduler_minute: int = 0

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = "your_secret_api_key"
    rate_limit_requests: int = 100
    rate_limit_period: int = 3600

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
