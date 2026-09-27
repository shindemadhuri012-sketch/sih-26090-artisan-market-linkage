"""
SIH 26090: Configuration Unit Tests
Tests environment settings loading, default fallbacks, and validator behavior.
"""

from backend.app.core.config import Settings


def test_default_settings_instantiation():
    """Verify that Settings can be instantiated with default safe values."""
    settings = Settings()
    assert settings.APP_NAME == "SIH 26090 Artisan Market Linkage"
    assert settings.APP_ENV in ["development", "staging", "production"]
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.DATABASE_POOL_SIZE > 0
    assert settings.EMBEDDING_DIMENSION == 768


def test_cors_origins_parsing():
    """Verify that CORS origins handle both string and list inputs."""
    # List input
    settings_list = Settings(CORS_ORIGINS=["http://localhost:3000", "https://artisan.in"])
    assert "http://localhost:3000" in settings_list.CORS_ORIGINS
    assert "https://artisan.in" in settings_list.CORS_ORIGINS

    # Comma-separated string input
    settings_str = Settings(CORS_ORIGINS="http://localhost:3000, https://artisan.in")
    assert "http://localhost:3000" in settings_str.CORS_ORIGINS
    assert "https://artisan.in" in settings_str.CORS_ORIGINS
