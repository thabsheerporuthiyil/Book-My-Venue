import uuid
from typing import Literal

from pydantic import BaseModel

from .base import EventEnvelope


class VenueCreatedPayload(BaseModel):
    venue_id: uuid.UUID
    tenant_id: uuid.UUID
    vendor_id: uuid.UUID
    name: str
    city: str


class VenueCreatedEvent(EventEnvelope):
    event_type: Literal["venue.created"] = "venue.created"
    payload: VenueCreatedPayload


class VenueApprovedPayload(BaseModel):
    venue_id: uuid.UUID
    tenant_id: uuid.UUID
    vendor_id: uuid.UUID
    approved_by: uuid.UUID
    name: str
    city: str


class VenueApprovedEvent(EventEnvelope):
    event_type: Literal["venue.approved"] = "venue.approved"
    payload: VenueApprovedPayload
