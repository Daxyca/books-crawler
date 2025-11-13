"""
FastAPI main application.

This is the entry point for the Books Crawler API.
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from src.app.utils.db import Database
from src.app.utils.config import get_settings
from src.app.api.rate_limiter import limiter
from src.app.api.routes import books, changes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting API server...")
    await Database.connect()
    yield
    # Shutdown
    print("Shutting down API server...")
    await Database.close()


# Create FastAPI app
app = FastAPI(
    title="Books Crawler API",
    description="""
    RESTful API for the Books Crawler project.
    
    This API provides access to:
    - Books: Query, filter, and retrieve book data from books.toscrape.com
    - Changes: Track and monitor changes in book data over time
    
    Authentication:
    - All endpoints require an API key. Include it in the `X-API-Key` header.
    
    Rate Limiting:
    - Limit: 100 requests per hour per IP address
    - Headers: Check `X-RateLimit-Limit` and `X-RateLimit-Remaining`
    
    Pagination:
    - Most endpoints support pagination with `page` and `page_size` parameters.
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# CORS middleware
# In production, restrict to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(books.router)
app.include_router(changes.router)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.

    Returns basic API information and links to documentation.
    """
    settings = get_settings()
    return {
        "message": "Books Crawler API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "books": "/books",
            "book_by_id": "/books/{book_id}",
            "changes": "/changes",
        },
        "authentication": "Include X-API-Key header",
        "rate_limit": f"{settings.rate_limit_requests} requests per hour",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the health status of the API and database connection.
    """
    try:
        # Check database connection
        db = Database.get_db()
        await db.command("ping")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "api": "healthy",
        "database": db_status,
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource was not found: {request.url.path}",
            "docs": "/docs",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
