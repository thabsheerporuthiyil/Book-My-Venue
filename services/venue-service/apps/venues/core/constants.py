"""
Domain constants for the Venue Service.

Using Django's TextChoices ensures these values are enforced at both
the database level (via CharField choices) and the API level (via serializers).
"""

from django.db import models


class PriceType(models.TextChoices):
    FULL_DAY = "FULL_DAY", "Full Day"
    HALF_DAY = "HALF_DAY", "Half Day"
    HOURLY = "HOURLY", "Hourly"


class ApprovalStatus(models.TextChoices):
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    SUSPENDED = "SUSPENDED", "Suspended"


class PolicyType(models.TextChoices):
    CANCELLATION = "CANCELLATION", "Cancellation"
    FOOD = "FOOD", "Food"
    DECORATION = "DECORATION", "Decoration"
    ALCOHOL = "ALCOHOL", "Alcohol"
    SMOKING = "SMOKING", "Smoking"
    MUSIC_NOISE = "MUSIC_NOISE", "Music / Noise"
    PARKING = "PARKING", "Parking"
    OUTSIDE_VENDOR = "OUTSIDE_VENDOR", "Outside Vendors"
    GENERAL = "GENERAL", "General"


class PolicyValue(models.TextChoices):
    ALLOWED = "ALLOWED", "Allowed"
    NOT_ALLOWED = "NOT_ALLOWED", "Not Allowed"
    WITH_RESTRICTIONS = "WITH_RESTRICTIONS", "With Restrictions"
    CUSTOM = "CUSTOM", "Custom"


class VenueStaffRole(models.TextChoices):
    VENUE_OWNER = "VENUE_OWNER", "Venue Owner"
    VENUE_MANAGER = "VENUE_MANAGER", "Venue Manager"
    VENUE_STAFF = "VENUE_STAFF", "Venue Staff"
