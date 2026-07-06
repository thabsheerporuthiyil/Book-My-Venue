import logging

from django.contrib.auth import authenticate
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.core.exceptions import (
    AccountLockedError,
    InactiveUserError,
    InvalidCredentialsError,
    SamePasswordError,
    UnverifiedAccountError,
)
from apps.accounts.core.lockout import AccountLockoutTracker

logger = logging.getLogger(__name__)


def authenticate_user(email: str, password: str):
    """
    Validates email + password credentials and returns the active user.

    Raises:
        AccountLockedError: If the account is temporarily locked.
        InvalidCredentialsError: If credentials are wrong or user doesn't exist.
        InactiveUserError: If the user account is deactivated.
        UnverifiedAccountError: If the user has not verified their OTP.
    """
    email_clean = email.lower().strip()

    if AccountLockoutTracker.is_locked_out(email_clean):
        logger.warning("Blocked login attempt for locked account: %s", email_clean)
        raise AccountLockedError(
            f"Account is temporarily locked due to too many failed attempts. "
            f"Please try again in {AccountLockoutTracker.LOCKOUT_TIME_SECONDS // 60} minutes."
        )

    user = authenticate(username=email_clean, password=password)

    if not user:
        AccountLockoutTracker.record_failed_attempt(email_clean)
        logger.warning("Failed login attempt for: %s", email_clean)
        raise InvalidCredentialsError("Invalid email or password.")

    if not user.is_active:
        raise InactiveUserError("User account is inactive.")

    if not user.is_verified:
        logger.warning("Blocked login attempt for unverified account: %s", email_clean)
        raise UnverifiedAccountError("Please verify your email address to log in.")

    # Successful login, clear any tracked failures
    AccountLockoutTracker.clear_attempts(email_clean)

    return user


def get_tokens_for_user(user) -> dict:
    """
    Generates a JWT access + refresh token pair for the given user.

    Returns:
        {"access": "<token>", "refresh": "<token>"}
    """
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def logout_all_user_sessions(user):
    """
    Terminates all active sessions for the user by adding all their
    outstanding refresh tokens to the blacklist.
    """
    tokens = OutstandingToken.objects.filter(user=user)
    # Bulk create blacklisted tokens ignoring duplicates
    blacklisted = []
    for token in tokens:
        if not hasattr(token, "blacklistedtoken"):
            blacklisted.append(BlacklistedToken(token=token))

    if blacklisted:
        BlacklistedToken.objects.bulk_create(blacklisted, ignore_conflicts=True)

    logger.info("Terminated all active sessions for user %s", user.email)


def change_user_password(user, current_password: str, new_password: str):
    """
    Changes the user's password after validating the current one.

    Rules:
        - current_password must match the stored hash.
        - new_password must differ from current_password.
        - Django's AUTH_PASSWORD_VALIDATORS are applied via set_password.

    Raises:
        InvalidCredentialsError: If current_password is wrong.
        SamePasswordError: If new_password == current_password.
    """
    if not user.check_password(current_password):
        raise InvalidCredentialsError("Current password is incorrect.")

    if current_password == new_password:
        raise SamePasswordError("New password must be different from the current password.")

    user.set_password(new_password)
    # Use update_fields to avoid touching other columns unnecessarily
    user.save(update_fields=["password"])

    # CRITICAL: Invalidate all existing sessions
    logout_all_user_sessions(user)

    logger.info("Password changed for user %s", user.email)
    return user
