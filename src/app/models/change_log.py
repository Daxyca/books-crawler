from pydantic import BaseModel, ConfigDict, Field, field_serializer
from typing import Optional, Any
from datetime import datetime, timezone
from enum import Enum


class ChangeType(str, Enum):
    NEW_BOOK = "new_book"
    PRICE_CHANGE = "price_change"
    AVAILABILITY_CHANGE = "availability_change"
    RATING_CHANGE = "rating_change"
    OTHER_CHANGE = "other_change"


class ChangeLog(BaseModel):
    book_name: str = Field(..., description="Name of the book")
    book_url: str = Field(..., description="Source URL of the book")

    change_type: ChangeType = Field(..., description="Type of change")
    field_name: Optional[str] = Field(None, description="Name of field that changed")
    old_value: Optional[Any] = Field(None, description="Previous value")
    new_value: Optional[Any] = Field(None, description="New value")

    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When change was detected",
    )

    summary: Optional[str] = Field(None, description="Human-readable summary")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "book_name": "A Light in the Attic",
                "book_url": "https://books.toscrape.com/catalogue/...",
                "change_type": "price_change",
                "field_name": "price_incl_tax",
                "old_value": 51.77,
                "new_value": 45.99,
                "detected_at": "2024-01-15T10:30:00",
                "summary": "Price decreased from £51.77 to £45.99",
            }
        }
    )

    @field_serializer("detected_at")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class ChangeReport(BaseModel):
    report_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When report was generated",
    )

    total_changes: int = Field(..., description="Total number of changes")
    new_books: int = Field(0, description="Number of new books added")
    price_changes: int = Field(0, description="Number of price changes")
    availability_changes: int = Field(0, description="Number of availability changes")
    rating_changes: int = Field(0, description="Number of rating changes")
    other_changes: int = Field(0, description="Number of other changes")

    changes: list[ChangeLog] = Field(
        default_factory=list, description="List of all changes"
    )

    @field_serializer("report_date")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()
