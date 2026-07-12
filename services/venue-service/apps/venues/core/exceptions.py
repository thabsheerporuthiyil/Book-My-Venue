"""
Domain-specific exceptions for the Venue Service.

Each exception defines:
    error_code  — A stable, machine-readable identifier for frontend/mobile clients.
    status_code — The HTTP status code the global exception handler should return.
"""


class VenueBaseException(Exception):
    """Base exception for all venue-related business logic errors."""

    error_code = "VENUE_ERROR"
    status_code = 400

    def __init__(self, message=None):
        self.message = message or self.__class__.__doc__ or "A venue error occurred."
        super().__init__(self.message)


class VenueNotFoundError(VenueBaseException):
    """Venue not found."""

    error_code = "VENUE_NOT_FOUND"
    status_code = 404


class VenueNotApprovedError(VenueBaseException):
    """This venue is not currently approved for bookings."""

    error_code = "VENUE_NOT_APPROVED"
    status_code = 403


class VenueOwnershipError(VenueBaseException):
    """You do not have permission to modify this venue."""

    error_code = "VENUE_OWNERSHIP_ERROR"
    status_code = 403


class CategoryNotFoundError(VenueBaseException):
    """Venue category not found."""

    error_code = "CATEGORY_NOT_FOUND"
    status_code = 404


class DuplicateVenueSlugError(VenueBaseException):
    """A venue with this name already exists in your organization."""

    error_code = "DUPLICATE_VENUE_SLUG"
    status_code = 409


class ImageLimitExceededError(VenueBaseException):
    """Maximum number of images per venue exceeded."""

    error_code = "IMAGE_LIMIT_EXCEEDED"
    status_code = 400


class ImageNotFoundError(VenueBaseException):
    """Image not found."""

    error_code = "IMAGE_NOT_FOUND"
    status_code = 404
