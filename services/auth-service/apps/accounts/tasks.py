import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(
    name="accounts.send_otp_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,  # retry after 30 seconds if SMTP server fails
)
def send_otp_email_task(self, user_email: str, otp_code: str, user_full_name: str, otp_ttl_seconds: int):
    """
    Sends the OTP verification email asynchronously.
    We accept primitive types (str, int) instead of Django model instances
    to prevent serialization issues and race conditions.
    """
    subject = "Verify your Book My Venue account"
    message = (
        f"Hello {user_full_name},\n\n"
        f"Your verification code is: {otp_code}\n\n"
        f"This code will expire in {otp_ttl_seconds // 60} minutes."
    )

    try:
        logger.info(f"Sending OTP email to {user_email} via Celery...")
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,  # We want exceptions to bubble up to trigger retries
        )
        logger.info(f"Successfully sent OTP to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send OTP to {user_email}: {e}. Retrying...")
        # Automatically retry the task if there's a temporary SMTP network failure
        raise self.retry(exc=e)
