def test_settings_load(settings):
    assert settings.mongodb_url.startswith("mongodb://")
    assert settings.base_url == "https://books.toscrape.com"
    assert settings.max_concurrent_requests > 0
