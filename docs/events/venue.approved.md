# Event: venue.approved

Emitted when a platform admin manually approves a venue. The venue is now visible to customers and can receive bookings.

*   **Version:** 1
*   **Producer:** `venue-service`
*   **Topic:** `venue.lifecycle`
*   **Partition Key:** `venue_id`

## Consumers
*   **Notification Service:** Emails the vendor that their venue is now live.
*   **AI Service:** Triggers a job to fetch venue details and generate vector embeddings for semantic search.
*   *(Future) Search Service:* Indexes the venue for standard full-text search.

## Payload Schema (v1)

```json
{
  "event_id": "uuid",
  "event_version": 1,
  "event_type": "venue.approved",
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
    "approved_by": "uuid",
    "name": "Grand Palace Hall",
    "city": "Mumbai"
  }
}
```
