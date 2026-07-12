import pytest
from django.conf import settings


@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Ensure tests run in a controlled environment.
    - Disable Silk profiler in tests (causes middleware issues)
    - Force LocMemCache for Redis
    """
    if "silk.middleware.SilkyMiddleware" in settings.MIDDLEWARE:
        settings.MIDDLEWARE.remove("silk.middleware.SilkyMiddleware")

    if "silk" in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS.remove("silk")

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }


@pytest.fixture
def mock_auth_service(monkeypatch):
    """
    Mocks the cross-service call to Auth Service during testing.
    Since unit/integration tests shouldn't make real network calls.
    """

    class MockResponse:
        status_code = 200

        def __init__(self, json_data):
            self._json_data = json_data

        def json(self):
            return self._json_data

    def mock_post(url, *args, **kwargs):
        # We simulate a successful response from auth-service
        return MockResponse(
            {
                "valid": True,
                "user": {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "email": "testvendor@example.com",
                    "global_role": "USER",
                },
                "tenant": {"id": "22222222-2222-2222-2222-222222222222", "name": "Test Organization", "role": "OWNER"},
            }
        )

    import requests

    monkeypatch.setattr(requests, "post", mock_post)
