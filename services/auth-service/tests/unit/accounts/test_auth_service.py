"""
Unit tests for apps.accounts.core.services.auth

Tests authentication, token generation, session logout,
and password change business logic in isolation.
"""

import pytest
from apps.accounts.core.exceptions import (
    AccountLockedError,
    InactiveUserError,
    InvalidCredentialsError,
    SamePasswordError,
    UnverifiedAccountError,
)
from apps.accounts.core.services.auth import (
    authenticate_user,
    change_user_password,
    get_tokens_for_user,
    logout_all_user_sessions,
)
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# authenticate_user
# ---------------------------------------------------------------------------


class TestAuthenticateUser:
    def test_valid_credentials_returns_user(self, verified_user, user_password):
        user = authenticate_user(verified_user.email, user_password)
        assert user.id == verified_user.id

    def test_wrong_password_raises_invalid_credentials(self, verified_user):
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(verified_user.email, "WrongPassword123!")

    def test_nonexistent_email_raises_invalid_credentials(self, db):
        with pytest.raises(InvalidCredentialsError):
            authenticate_user("nobody@test.com", "Password123!")

    def test_inactive_user_raises_inactive_error(self, inactive_user, user_password):
        with pytest.raises(InactiveUserError):
            authenticate_user(inactive_user.email, user_password)

    def test_unverified_user_raises_unverified_error(self, db, user_password):
        from apps.accounts.models import User

        user = User.objects.create_user(
            email="unverified@auth.com",
            password=user_password,
            full_name="Unverified",
            is_verified=False,
            is_active=True,
        )
        with pytest.raises(UnverifiedAccountError):
            authenticate_user(user.email, user_password)

    def test_email_is_case_insensitive(self, verified_user, user_password):
        user = authenticate_user(verified_user.email.upper(), user_password)
        assert user.id == verified_user.id

    def test_locked_account_raises_locked_error(self, verified_user, user_password):
        # Simulate 5 failed login attempts to trigger lockout
        for _ in range(5):
            try:
                authenticate_user(verified_user.email, "wrong!")
            except InvalidCredentialsError:
                pass

        with pytest.raises(AccountLockedError):
            authenticate_user(verified_user.email, user_password)

    def test_successful_login_clears_failed_attempts(self, verified_user, user_password):
        # 3 failed attempts (below threshold)
        for _ in range(3):
            try:
                authenticate_user(verified_user.email, "wrong!")
            except InvalidCredentialsError:
                pass

        # Successful login should clear the counter
        authenticate_user(verified_user.email, user_password)

        # 3 more failures should NOT lock (counter was reset)
        for _ in range(3):
            try:
                authenticate_user(verified_user.email, "wrong!")
            except InvalidCredentialsError:
                pass

        # Should still work because counter reset after the successful login
        user = authenticate_user(verified_user.email, user_password)
        assert user.id == verified_user.id


# ---------------------------------------------------------------------------
# get_tokens_for_user
# ---------------------------------------------------------------------------


class TestGetTokensForUser:
    def test_returns_access_and_refresh_tokens(self, verified_user):
        tokens = get_tokens_for_user(verified_user)

        assert "access" in tokens
        assert "refresh" in tokens
        assert isinstance(tokens["access"], str)
        assert isinstance(tokens["refresh"], str)
        assert len(tokens["access"]) > 50
        assert len(tokens["refresh"]) > 50


# ---------------------------------------------------------------------------
# logout_all_user_sessions
# ---------------------------------------------------------------------------


class TestLogoutAllSessions:
    def test_blacklists_all_outstanding_tokens(self, verified_user):
        # Create 3 sessions (3 refresh tokens)
        for _ in range(3):
            RefreshToken.for_user(verified_user)

        outstanding_before = OutstandingToken.objects.filter(user=verified_user).count()
        assert outstanding_before == 3

        logout_all_user_sessions(verified_user)

        blacklisted_count = BlacklistedToken.objects.filter(
            token__user=verified_user,
        ).count()
        assert blacklisted_count == 3

    def test_no_error_when_no_sessions_exist(self, verified_user):
        # Should not raise even if user has no tokens
        logout_all_user_sessions(verified_user)


# ---------------------------------------------------------------------------
# change_user_password
# ---------------------------------------------------------------------------


class TestChangePassword:
    def test_changes_password_successfully(self, verified_user, user_password):
        new_password = "NewSecurePass456!"
        change_user_password(verified_user, user_password, new_password)

        verified_user.refresh_from_db()
        assert verified_user.check_password(new_password)

    def test_wrong_current_password_raises_error(self, verified_user):
        with pytest.raises(InvalidCredentialsError):
            change_user_password(verified_user, "wrong!", "NewPass123!")

    def test_same_password_raises_error(self, verified_user, user_password):
        with pytest.raises(SamePasswordError):
            change_user_password(verified_user, user_password, user_password)

    def test_blacklists_all_sessions_after_change(self, verified_user, user_password):
        # Create sessions
        for _ in range(2):
            RefreshToken.for_user(verified_user)

        change_user_password(verified_user, user_password, "BrandNew789!")

        blacklisted = BlacklistedToken.objects.filter(token__user=verified_user).count()
        assert blacklisted == 2
