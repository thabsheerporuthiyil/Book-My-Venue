"""
Unit tests for apps.accounts.core.services.otp

Tests the OTP generation, Redis storage, Celery dispatch,
and verification logic in complete isolation.
"""

import pytest
from apps.accounts.core.services.otp import (
    OTP_LENGTH,
    OTP_TTL_SECONDS,
    _get_otp_cache_key,
    generate_and_send_otp,
    verify_otp,
)
from django.core.cache import cache

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# generate_and_send_otp
# ---------------------------------------------------------------------------


class TestGenerateAndSendOTP:
    def test_returns_numeric_string_of_correct_length(self, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        otp = generate_and_send_otp(verified_user)

        assert otp.isdigit()
        assert len(otp) == OTP_LENGTH

    def test_stores_otp_in_redis(self, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        otp = generate_and_send_otp(verified_user)

        cache_key = _get_otp_cache_key(verified_user.email)
        stored = cache.get(cache_key)
        assert stored == otp

    def test_dispatches_celery_task(self, verified_user, mocker):
        mock_delay = mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        otp = generate_and_send_otp(verified_user)

        mock_delay.assert_called_once_with(
            user_email=verified_user.email,
            otp_code=otp,
            user_full_name=verified_user.full_name,
            otp_ttl_seconds=OTP_TTL_SECONDS,
        )

    def test_each_call_generates_unique_otp(self, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")

        otps = {generate_and_send_otp(verified_user) for _ in range(20)}
        # With 6-digit codes, 20 calls should produce multiple distinct values
        assert len(otps) > 1


# ---------------------------------------------------------------------------
# verify_otp
# ---------------------------------------------------------------------------


class TestVerifyOTP:
    def test_valid_otp_returns_true(self, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        otp = generate_and_send_otp(verified_user)

        # The user fixture is already verified, but let's test the flow:
        # Reset is_verified to False to simulate real registration
        verified_user.is_verified = False
        verified_user.save(update_fields=["is_verified"])

        result = verify_otp(verified_user.email, otp)
        assert result is True

    def test_marks_user_as_verified(self, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        otp = generate_and_send_otp(verified_user)

        verified_user.is_verified = False
        verified_user.save(update_fields=["is_verified"])

        verify_otp(verified_user.email, otp)

        verified_user.refresh_from_db()
        assert verified_user.is_verified is True

    def test_deletes_otp_from_redis_after_verification(self, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        otp = generate_and_send_otp(verified_user)

        verified_user.is_verified = False
        verified_user.save(update_fields=["is_verified"])

        verify_otp(verified_user.email, otp)

        cache_key = _get_otp_cache_key(verified_user.email)
        assert cache.get(cache_key) is None

    def test_wrong_otp_returns_false(self, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        generate_and_send_otp(verified_user)

        result = verify_otp(verified_user.email, "000000")
        assert result is False

    def test_expired_otp_returns_false(self, verified_user):
        # Don't generate an OTP — simulate expired (nothing in cache)
        result = verify_otp(verified_user.email, "123456")
        assert result is False

    def test_nonexistent_user_returns_false(self, db):
        cache_key = _get_otp_cache_key("ghost@test.com")
        cache.set(cache_key, "123456", timeout=300)

        result = verify_otp("ghost@test.com", "123456")
        assert result is False

    def test_email_is_case_insensitive(self, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        otp = generate_and_send_otp(verified_user)

        verified_user.is_verified = False
        verified_user.save(update_fields=["is_verified"])

        result = verify_otp(verified_user.email.upper(), otp)
        assert result is True

    def test_otp_cannot_be_reused(self, verified_user, mocker):
        mocker.patch("apps.accounts.core.services.otp.send_otp_email_task.delay")
        otp = generate_and_send_otp(verified_user)

        verified_user.is_verified = False
        verified_user.save(update_fields=["is_verified"])

        # First use should succeed
        assert verify_otp(verified_user.email, otp) is True
        # Second use should fail (OTP was deleted from Redis)
        assert verify_otp(verified_user.email, otp) is False
