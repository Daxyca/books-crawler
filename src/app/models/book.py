from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime, timezone


class Book(BaseModel):
    name: str = Field(..., description="Book title")
    description: Optional[str] = Field(None, description="Book description")
    category: str = Field(..., description="Book category")

    currency: str = Field(..., description="Price currency")
    price_excl_tax: float = Field(..., description="Price excluding tax", gt=0)
    price_incl_tax: float = Field(..., description="Price including tax", gt=0)

    availability: str = Field(..., description="Stock availability status")
    num_reviews: int = Field(..., description="Number of reviews", ge=0)
    rating: str = Field(..., description="Star rating (One to Five)")

    image_url: str = Field(..., description="URL of book cover image")
    source_url: str = Field(..., description="URL of the book page")

    crawl_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this book was crawled",
    )
    crawl_status: str = Field(
        default="success", description="Status of the crawl (success/failed)"
    )

    # Fallback
    raw_html: Optional[str] = Field(None, description="Raw HTML of the book page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "A Light in the Attic",
                "description": "A collection of poetry...",
                "category": "Poetry",
                "currency": "£",
                "price_excl_tax": 51.77,
                "price_incl_tax": 51.77,
                "availability": "In stock (22 available)",
                "num_reviews": 0,
                "rating": "Three",
                "image_url": "https://books.toscrape.com/media/cache/...",
                "source_url": "https://books.toscrape.com/catalogue/...",
                "crawl_timestamp": "2024-01-15T10:30:00",
                "crawl_status": "success",
            }
        },
    )

    @field_serializer("crawl_timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()
