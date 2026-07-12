import logging

from django.core.cache import cache
from django.utils.crypto import get_random_string

from apps.accounts.core.exceptions import InvalidOTPError
from apps.accounts.core.services.auth import logout_all_user_sessions
from apps.accounts.models import User
from apps.accounts.tasks import send_password_reset_email_task

logger = logging.getLogger(__name__)

# Config
RESET_OTP_TTL_SECONDS = 900  # 15 minutes


def _get_password_reset_cache_key(email: str) -> str:
    return f"password_reset_otp:{email.lower().strip()}"


def initiate_forgot_password(email: str):
    """
    Initiates the forgot password flow by generating an OTP and sending an email.
    Fails silently if the user doesn't exist (to prevent email enumeration).
    """
    email_clean = email.lower().strip()
    user = User.objects.filter(email=email_clean).first()

    if not user:
        logger.warning("Password reset requested for non-existent email: %s", email_clean)
        return

    # Generate a secure 6-digit numeric OTP
    otp_code = get_random_string(length=6, allowed_chars="0123456789")
    cache_key = _get_password_reset_cache_key(email_clean)

    # Store OTP in Redis
    cache.set(cache_key, otp_code, timeout=RESET_OTP_TTL_SECONDS)

    # Dispatch Celery task
    send_password_reset_email_task.delay(
        user_email=email_clean,
        otp_code=otp_code,
        user_full_name=user.full_name,
        otp_ttl_seconds=RESET_OTP_TTL_SECONDS,
    )
    logger.info("Initiated password reset for user: %s", email_clean)


def complete_password_reset(email: str, otp: str, new_password: str):
    """
    Verifies the OTP and resets the user's password.
    Instantly terminates all active sessions across all devices.
    """
    email_clean = email.lower().strip()
    cache_key = _get_password_reset_cache_key(email_clean)

    stored_otp = cache.get(cache_key)

    if not stored_otp:
        raise InvalidOTPError("OTP has expired or does not exist.")

    if stored_otp != otp:
        raise InvalidOTPError("Invalid OTP code.")

    user = User.objects.filter(email=email_clean).first()
    if not user:
        # Should realistically never happen unless user was deleted during the 15min window
        raise InvalidOTPError("Invalid OTP code.")

    # Apply new password
    user.set_password(new_password)
    user.save(update_fields=["password"])

    # OTP is single-use
    cache.delete(cache_key)

    # Invalidate all existing sessions
    logout_all_user_sessions(user)

    logger.info("Password successfully reset for user %s via OTP", email_clean)
    return user
