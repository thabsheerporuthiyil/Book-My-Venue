import logging
import random
import string

from django.core.cache import cache

from apps.accounts.models import User
from apps.accounts.tasks import send_otp_email_task

logger = logging.getLogger(__name__)

# Constants
OTP_LENGTH = 6
OTP_TTL_SECONDS = 300  # 5 minutes


def _get_otp_cache_key(email: str) -> str:
    """Generates the Redis cache key for a given email's OTP."""
    safe_email = email.strip().lower()
    return f"otp:verify:{safe_email}"


def generate_and_send_otp(user: User) -> str:
    """
    Generates a secure 6-digit OTP, stores it in Redis with a 5-minute TTL,
    and dispatches a Celery task to asynchronously send the email to the user.
    """
    secure_random = random.SystemRandom()
    otp_code = "".join(secure_random.choice(string.digits) for _ in range(OTP_LENGTH))

    # Save to Redis
    cache_key = _get_otp_cache_key(user.email)
    cache.set(cache_key, otp_code, timeout=OTP_TTL_SECONDS)

    # Log it for development convenience
    logger.info("=" * 50)
    logger.info(f"📧 EMAIL OTP TRIGGERED FOR: {user.email}")
    logger.info(f"🔑 YOUR VERIFICATION OTP IS: {otp_code}")
    logger.info(f"⏰ This code expires in {OTP_TTL_SECONDS // 60} minutes.")
    logger.info("=" * 50)

    # Push email sending to background worker
    send_otp_email_task.delay(
        user_email=user.email,
        otp_code=otp_code,
        user_full_name=user.full_name,
        otp_ttl_seconds=OTP_TTL_SECONDS,
    )

    return otp_code


def verify_otp(email: str, code: str) -> bool:
    """
    Validates the provided OTP against the one stored in Redis.
    If valid, marks the user as verified and destroys the OTP.
    """
    safe_email = email.strip().lower()
    cache_key = _get_otp_cache_key(safe_email)

    stored_code = cache.get(cache_key)

    if not stored_code:
        return False  # Expired or never existed

    if stored_code == code.strip():
        # Valid code! Mark user as verified.
        try:
            user = User.objects.get(email=safe_email)
            user.is_verified = True
            user.save(update_fields=["is_verified"])

            # Destroy the code in Redis so it cannot be reused
            cache.delete(cache_key)
            return True
        except User.DoesNotExist:
            return False

    return False
