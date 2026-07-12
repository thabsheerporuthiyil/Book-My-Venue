class AccountBaseException(Exception):
    """
    Base exception for all account-related business logic errors.

    Subclasses define:
        error_code  — A stable, machine-readable identifier for frontend/mobile clients.
        status_code — The HTTP status code the global exception handler should return.
    """

    error_code = "ACCOUNT_ERROR"
    status_code = 400

    def __init__(self, message=None):
        self.message = message or self.__class__.__doc__ or "An account error occurred."
        super().__init__(self.message)


class UserAlreadyExistsError(AccountBaseException):
    """A user with this email already exists."""

    error_code = "USER_ALREADY_EXISTS"
    status_code = 409


class InvalidCredentialsError(AccountBaseException):
    """Invalid email or password."""

    error_code = "INVALID_CREDENTIALS"
    status_code = 401


class InactiveUserError(AccountBaseException):
    """User account is inactive."""

    error_code = "INACTIVE_USER"
    status_code = 403


class DomainAlreadyTakenError(AccountBaseException):
    """This domain is already taken."""

    error_code = "DOMAIN_ALREADY_TAKEN"
    status_code = 409


class SamePasswordError(AccountBaseException):
    """New password must be different from the current password."""

    error_code = "SAME_PASSWORD"
    status_code = 400


class PasswordChangeError(AccountBaseException):
    """Generic error during a password change operation."""

    error_code = "PASSWORD_CHANGE_FAILED"
    status_code = 400


class AccountLockedError(AccountBaseException):
    """Account is temporarily locked due to too many failed login attempts."""

    error_code = "ACCOUNT_LOCKED"
    status_code = 429


class UnverifiedAccountError(AccountBaseException):
    """Please verify your email address to log in."""

    error_code = "UNVERIFIED_ACCOUNT"
    status_code = 403


class InvalidOTPError(AccountBaseException):
    """OTP has expired or does not exist."""

    error_code = "INVALID_OTP"
    status_code = 400
