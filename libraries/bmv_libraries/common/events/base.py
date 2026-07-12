import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventEnvelope(BaseModel):
    """
    Standardized Event Envelope for all microservices in Book My Venue.

    Attributes:
        event_id: Unique identifier for idempotency (UUID4).
        event_version: Schema version for backward compatibility.
        event_type: The domain event name (e.g. 'venue.created').
        producer: Service that emitted the event (e.g. 'venue-service').
        tenant_id: Tenant context for multi-tenancy.
        correlation_id: Ties user request across microservices.
        causation_id: The ID of the event that caused this event (if any).
        trace_id: OpenTelemetry trace identifier.
        source: System identifier of the producer.
        occurred_at: UTC timestamp when the event happened.
        payload: The strictly typed domain payload.
    """

    model_config = ConfigDict(extra="allow", frozen=True)  # Forward compatibility

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_version: int = Field(default=1)
    event_type: str
    producer: str
    tenant_id: str
    correlation_id: str
    causation_id: str | None = None
    trace_id: str | None = None
    source: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    payload: BaseModel
