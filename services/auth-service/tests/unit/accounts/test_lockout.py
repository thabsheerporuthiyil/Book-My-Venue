"""
Unit tests for apps.accounts.core.lockout.AccountLockoutTracker

Tests the Redis-backed brute force protection system.
"""

import pytest
from apps.accounts.core.lockout import AccountLockoutTracker

pytestmark = pytest.mark.unit


class TestAccountLockoutTracker:
    EMAIL = "lockout@test.com"

    def test_not_locked_initially(self):
        assert AccountLockoutTracker.is_locked_out(self.EMAIL) is False

    def test_not_locked_below_threshold(self):
        for _ in range(AccountLockoutTracker.MAX_ATTEMPTS - 1):
            AccountLockoutTracker.record_failed_attempt(self.EMAIL)

        assert AccountLockoutTracker.is_locked_out(self.EMAIL) is False

    def test_locked_at_threshold(self):
        for _ in range(AccountLockoutTracker.MAX_ATTEMPTS):
            AccountLockoutTracker.record_failed_attempt(self.EMAIL)

        assert AccountLockoutTracker.is_locked_out(self.EMAIL) is True

    def test_locked_above_threshold(self):
        for _ in range(AccountLockoutTracker.MAX_ATTEMPTS + 3):
            AccountLockoutTracker.record_failed_attempt(self.EMAIL)

        assert AccountLockoutTracker.is_locked_out(self.EMAIL) is True

    def test_clear_attempts_unlocks_account(self):
        for _ in range(AccountLockoutTracker.MAX_ATTEMPTS):
            AccountLockoutTracker.record_failed_attempt(self.EMAIL)

        assert AccountLockoutTracker.is_locked_out(self.EMAIL) is True

        AccountLockoutTracker.clear_attempts(self.EMAIL)
        assert AccountLockoutTracker.is_locked_out(self.EMAIL) is False

    def test_record_returns_attempt_count(self):
        for i in range(1, 4):
            count = AccountLockoutTracker.record_failed_attempt(self.EMAIL)
            assert count == i

    def test_email_is_case_insensitive(self):
        for _ in range(AccountLockoutTracker.MAX_ATTEMPTS):
            AccountLockoutTracker.record_failed_attempt("LOCKOUT@TEST.COM")

        assert AccountLockoutTracker.is_locked_out("lockout@test.com") is True
