"""
Changes API endpoints.

This module provides endpoints for querying change logs.
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import Optional
from src.app.models.change_log import ChangeLog
from src.app.crawler.storage import BookStorage
from src.app.utils.db import get_database
from src.app.api.auth import verify_api_key
from src.app.api.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta, timezone


router = APIRouter(prefix="/changes", tags=["Changes"])


@router.get(
    "",
    response_model=dict,
    summary="Get recent changes",
    description="Retrieve recent changes with optional filtering.",
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_changes(
    request: Request,
    # Authentication
    api_key: str = Depends(verify_api_key),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Number of items per page"),
    # Filtering
    change_type: Optional[str] = Query(
        None,
        description="Filter by change type (new_book, price_change, availability_change, rating_change, other_change)",
    ),
    days: Optional[int] = Query(
        None, ge=1, le=365, description="Filter changes from last N days"
    ),
    # Database
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get recent changes with filtering and pagination.

    Authentication: Requires API key in X-API-Key header

    Rate Limit: 100 requests per hour

    Example:
    GET /changes?change_type=price_change&days=7&page=1&page_size=50
    """
    storage = BookStorage(db)

    # Build query
    query = {}

    if change_type:
        query["change_type"] = change_type

    if days:
        # Filter by date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        query["detected_at"] = {"$gte": cutoff_date.isoformat()}

    # Calculate skip for pagination
    skip = (page - 1) * page_size

    # Execute query
    changes = []
    cursor = (
        storage.changes_collection.find(query)
        .sort("detected_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    async for doc in cursor:
        try:
            changes.append(ChangeLog(**doc))
        except Exception as e:
            print(f"Error loading change log: {e}")

    # Get total count
    total = await storage.changes_collection.count_documents(query)
    total_pages = (total + page_size - 1) // page_size

    return {
        "data": [change.model_dump() for change in changes],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
        "filters": {"change_type": change_type, "days": days},
    }
