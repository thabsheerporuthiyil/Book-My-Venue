from django.core.cache import cache


class AccountLockoutTracker:
    """
    Tracks failed login attempts by email address using Redis cache.
    Locks the account for a specified duration if the threshold is reached.
    """

    MAX_ATTEMPTS = 5
    LOCKOUT_TIME_SECONDS = 900  # 15 minutes

    @classmethod
    def _get_cache_key(cls, email: str) -> str:
        # Sanitize email to ensure valid cache key
        safe_email = email.strip().lower()
        return f"lockout:failed_attempts:{safe_email}"

    @classmethod
    def is_locked_out(cls, email: str) -> bool:
        """Checks if the given email is currently locked out."""
        attempts = cache.get(cls._get_cache_key(email), 0)
        return attempts >= cls.MAX_ATTEMPTS

    @classmethod
    def record_failed_attempt(cls, email: str) -> int:
        """
        Records a failed attempt.
        Returns the new number of failed attempts.
        """
        key = cls._get_cache_key(email)
        try:
            # Atomic increment
            attempts = cache.incr(key)
        except ValueError:
            # Key doesn't exist, initialize it
            cache.set(key, 1, timeout=cls.LOCKOUT_TIME_SECONDS)
            attempts = 1

        # If we just hit the max attempts, reset the timeout to ensure the full lockout period starts NOW
        if attempts == cls.MAX_ATTEMPTS:
            cache.set(key, attempts, timeout=cls.LOCKOUT_TIME_SECONDS)

        return attempts

    @classmethod
    def clear_attempts(cls, email: str):
        """Clears all failed attempts upon a successful login."""
        cache.delete(cls._get_cache_key(email))
