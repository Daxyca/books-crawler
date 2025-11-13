"""
Books API endpoints.

This module provides endpoints for querying book data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from src.app.models.book import Book
from src.app.crawler.storage import BookStorage
from src.app.utils.db import get_database
from src.app.api.auth import verify_api_key
from src.app.api.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from motor.motor_asyncio import AsyncIOMotorDatabase


router = APIRouter(prefix="/books", tags=["Books"])


@router.get(
    "",
    response_model=dict,
    summary="Get books with filtering and pagination",
    description="Retrieve books with optional filters for category, price range, and rating.",
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_books(
    request: Request,
    # Authentication
    api_key: str = Depends(verify_api_key),
    # Pagination
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    # Filtering
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(
        None, ge=0, description="Minimum price (inclusive)"
    ),
    max_price: Optional[float] = Query(
        None, ge=0, description="Maximum price (inclusive)"
    ),
    rating: Optional[str] = Query(
        None, description="Filter by rating (One, Two, Three, Four, Five)"
    ),
    # Sorting
    sort_by: Optional[str] = Query(
        None,
        description="Sort by field (rating, price, reviews)",
        regex="^(rating|price|reviews)$",
    ),
    sort_order: Optional[str] = Query(
        "asc", description="Sort order (asc, desc)", regex="^(asc|desc)$"
    ),
    # Database
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get books with filtering, pagination, and sorting.

    Authentication: Requires API key in X-API-Key header

    Rate Limit: 100 requests per hour

    Example:
    GET /books?category=Poetry&min_price=10&max_price=50&sort_by=price&page=1&page_size=20
    """
    storage = BookStorage(db)

    # Build MongoDB query
    query = {}

    if category:
        query["category"] = category

    if min_price is not None or max_price is not None:
        query["price_incl_tax"] = {}
        if min_price is not None:
            query["price_incl_tax"]["$gte"] = min_price
        if max_price is not None:
            query["price_incl_tax"]["$lte"] = max_price

    if rating:
        query["rating"] = rating

    # Build sort criteria
    sort_criteria = []
    if sort_by:
        # Map user-friendly names to database fields
        field_map = {
            "rating": "rating",
            "price": "price_incl_tax",
            "reviews": "num_reviews",
        }

        field = field_map.get(sort_by, "name")
        direction = 1 if sort_order == "asc" else -1
        sort_criteria = [(field, direction)]

    # Calculate skip for pagination
    skip = (page - 1) * page_size

    # Execute query
    books = []
    cursor = storage.books_collection.find(query)

    if sort_criteria:
        cursor = cursor.sort(sort_criteria)

    cursor = cursor.skip(skip).limit(page_size)

    async for doc in cursor:
        try:
            # Remove raw_html from response (too large)
            doc.pop("raw_html", None)
            books.append(Book(**doc))
        except Exception as e:
            print(f"Error loading book: {e}")

    # Get total count for pagination metadata
    total = await storage.books_collection.count_documents(query)
    total_pages = (total + page_size - 1) // page_size

    return {
        "data": [book.model_dump(exclude={"raw_html"}) for book in books],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
        "filters": {
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "rating": rating,
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    }


@router.get(
    "/{book_id}",
    response_model=dict,
    summary="Get a specific book by ID",
    description="Retrieve detailed information about a specific book.",
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_book_by_id(
    request: Request,
    book_id: str,
    api_key: str = Depends(verify_api_key),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get a single book by its MongoDB ID.

    Authentication: Requires API key in X-API-Key header

    Rate Limit: 100 requests per hour

    Example:
    GET /books/507f1f77bcf86cd799439011
    """
    from bson import ObjectId
    from bson.errors import InvalidId

    storage = BookStorage(db)

    # Validate ObjectId format
    try:
        object_id = ObjectId(book_id)
    except InvalidId:
        raise HTTPException(
            status_code=400, detail=f"Invalid book ID format: {book_id}"
        )

    # Find book
    doc = await storage.books_collection.find_one({"_id": object_id})

    if not doc:
        raise HTTPException(
            status_code=404, detail=f"Book not found with ID: {book_id}"
        )

    # Convert to Book model
    try:
        book = Book(**doc)
        return {
            "data": book.model_dump(exclude={"raw_html"}),
            "raw_html_available": doc.get("raw_html") is not None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing book data: {str(e)}"
        )
