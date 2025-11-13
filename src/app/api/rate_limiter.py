from slowapi import Limiter
from slowapi.util import get_remote_address
from src.app.utils.config import get_settings


# Create limiter instance
# Client's IP address as key for rate limiting
limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_string() -> str:
    settings = get_settings()
    requests = settings.rate_limit_requests
    period = settings.rate_limit_period

    # Convert period to units (second, minute, hour, day)
    if period == 60:
        unit = "minute"
    elif period == 3600:
        unit = "hour"
    elif period == 86400:
        unit = "day"
    else:
        unit = f"{period}seconds"

    return f"{requests}/{unit}"


# Default rate limit for all endpoints
DEFAULT_RATE_LIMIT = get_rate_limit_string()
