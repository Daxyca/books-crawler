import uvicorn
from src.app.utils.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    print("\n" + "-" * 70)
    print("STARTING BOOKS CRAWLER API")
    print("-" * 70)
    base_url = f"http://{settings.api_host}:{settings.api_port}"
    print(f"\nServer: {base_url}")
    print(f"Swagger UI: {base_url}/docs")
    print(f"ReDoc: {base_url}/redoc")
    print(f"API Key: {settings.api_key}")
    print(f"Rate Limit: {settings.rate_limit_requests} requests per hour")
    print("\n" + "-" * 70 + "\n")

    uvicorn.run(
        "src.app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
