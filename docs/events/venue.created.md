# Event: venue.created

Emitted when a vendor successfully registers a new venue. At this stage, the venue is in `PENDING_APPROVAL` status and is not yet visible to customers.

*   **Version:** 1
*   **Producer:** `venue-service`
*   **Topic:** `venue.lifecycle`
*   **Partition Key:** `venue_id`

## Consumers
*   **Notification Service:** Sends a welcome/confirmation email to the vendor.
*   *(Future) Analytics Service:* Records venue acquisition metrics.

## Payload Schema (v1)

```json
{
  "event_id": "uuid",
  "event_version": 1,
  "event_type": "venue.created",
  "producer": "venue-service",
  "tenant_id": "uuid",
  "correlation_id": "uuid",
  "causation_id": null,
  "trace_id": null,
  "source": "bookmyvenue.venue-service",
  "occurred_at": "2026-07-12T10:00:00Z",
  "payload": {
    "venue_id": "uuid",
    "tenant_id": "uuid",
    "vendor_id": "uuid",
    "name": "Grand Palace Hall",
    "city": "Mumbai"
  }
}
```
