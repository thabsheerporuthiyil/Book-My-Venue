from unittest.mock import patch

import pytest
from apps.accounts.core.exceptions import InvalidOTPError
from apps.accounts.core.services.password import complete_password_reset, initiate_forgot_password
from django.core.cache import cache

pytestmark = pytest.mark.django_db


@pytest.fixture
def clean_cache():
    cache.clear()
    yield
    cache.clear()


class TestPasswordService:
    @patch("apps.accounts.core.services.password.send_password_reset_email_task.delay")
    def test_initiate_forgot_password_generates_otp_and_calls_task(self, mock_delay, verified_user, clean_cache):
        initiate_forgot_password(verified_user.email)

        cache_key = f"password_reset_otp:{verified_user.email}"
        stored_otp = cache.get(cache_key)

        assert stored_otp is not None
        assert len(stored_otp) == 6
        assert stored_otp.isdigit()

        mock_delay.assert_called_once_with(
            user_email=verified_user.email,
            otp_code=stored_otp,
            user_full_name=verified_user.full_name,
            otp_ttl_seconds=900,
        )

    @patch("apps.accounts.core.services.password.send_password_reset_email_task.delay")
    def test_initiate_forgot_password_fails_silently_for_invalid_email(self, mock_delay, clean_cache):
        initiate_forgot_password("unknown@example.com")

        cache_key = "password_reset_otp:unknown@example.com"
        assert cache.get(cache_key) is None
        mock_delay.assert_not_called()

    @patch("apps.accounts.core.services.password.logout_all_user_sessions")
    def test_complete_password_reset_success(self, mock_logout, verified_user, clean_cache):
        otp_code = "123456"
        cache_key = f"password_reset_otp:{verified_user.email}"
        cache.set(cache_key, otp_code, timeout=900)

        complete_password_reset(verified_user.email, otp_code, "NewStrongPassword123!")

        # Verify password changed
        verified_user.refresh_from_db()
        assert verified_user.check_password("NewStrongPassword123!")

        # Verify cache cleared
        assert cache.get(cache_key) is None

        # Verify sessions terminated
        mock_logout.assert_called_once_with(verified_user)

    def test_complete_password_reset_invalid_otp(self, verified_user, clean_cache):
        with pytest.raises(InvalidOTPError):
            complete_password_reset(verified_user.email, "000000", "NewStrongPassword123!")
