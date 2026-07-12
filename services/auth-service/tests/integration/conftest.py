"""
Shared fixtures for integration tests.

Sets DRF throttle rates extremely high so API tests can focus
on business logic without being rate-limited.
"""

import pytest


@pytest.fixture(autouse=True)
def _disable_throttling(settings):
    """Set throttle rates very high so they never trigger during tests."""
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {
            "anon": "10000/minute",
            "user": "10000/minute",
            "login": "10000/minute",
            "resend_otp": "10000/minute",
        },
    }
