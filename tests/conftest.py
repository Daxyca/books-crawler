import pytest
from src.app.utils.config import get_settings


@pytest.fixture
def settings():
    return get_settings()
