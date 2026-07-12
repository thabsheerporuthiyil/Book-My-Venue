"""
Approval Service — Admin-only business logic for venue approval workflow.
"""

import logging

from apps.venues.core.constants import ApprovalStatus
from apps.venues.core.exceptions import VenueNotFoundError
from apps.venues.core.models import Venue

logger = logging.getLogger(__name__)


def approve_venue(*, venue_id):
    """Approve a pending venue for public listing."""
    try:
        venue = Venue.objects.get(id=venue_id)
    except Venue.DoesNotExist as e:
        raise VenueNotFoundError() from e

    venue.approval_status = ApprovalStatus.APPROVED
    venue.save(update_fields=["approval_status", "updated_at"])

    logger.info("Venue APPROVED: %s", venue_id)
    return venue


def reject_venue(*, venue_id, reason=None):
    """Reject a pending venue."""
    try:
        venue = Venue.objects.get(id=venue_id)
    except Venue.DoesNotExist as e:
        raise VenueNotFoundError() from e

    venue.approval_status = ApprovalStatus.REJECTED
    venue.save(update_fields=["approval_status", "updated_at"])

    logger.info("Venue REJECTED: %s | Reason: %s", venue_id, reason)
    return venue


def suspend_venue(*, venue_id, reason=None):
    """Suspend an active venue (e.g., policy violation)."""
    try:
        venue = Venue.objects.get(id=venue_id)
    except Venue.DoesNotExist as e:
        raise VenueNotFoundError() from e

    venue.approval_status = ApprovalStatus.SUSPENDED
    venue.save(update_fields=["approval_status", "updated_at"])

    logger.info("Venue SUSPENDED: %s | Reason: %s", venue_id, reason)
    return venue
