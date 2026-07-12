# Event Versioning Policy

Treat events like public APIs. Once an event is published and consumed by other services, its schema is a binding contract.

Breaking this contract will cause production incidents across the platform.

## Rule 1: Backward Compatibility is Mandatory
Producers **must** ensure that schema changes do not break existing consumers.

### Allowed Changes (Minor - Safe)
You may modify the payload without incrementing `event_version`:
*   ✅ **Adding a new optional field:** `new_field: str | None = None`
*   ✅ **Adding a new field with a default value:** `is_featured: bool = False`

*Consumers (using Pydantic with `extra="allow"`) will safely ignore fields they don't recognize.*

### Forbidden Changes (Breaking - Unsafe)
You **must not** make these changes to an existing version:
*   ❌ **Renaming a field:** (e.g., `venue_id` to `id`)
*   ❌ **Removing a field**
*   ❌ **Changing a field's data type:** (e.g., string to int)
*   ❌ **Adding a new required field without a default**

## Rule 2: Handling Breaking Changes (Version Bumps)
If a breaking change is unavoidable, you must create a new version of the event.

1.  Create a new Payload class (e.g., `VenueCreatedPayloadV2`).
2.  Create a new Event class with `event_version = 2`.
3.  **The Producer must publish BOTH versions temporarily.**
    *   `producer.publish(EventV1)`
    *   `producer.publish(EventV2)`
4.  Wait for all downstream consumers to upgrade to read `V2`.
5.  Once confirmed, remove the `V1` publishing code from the producer.

## Rule 3: Idempotency is Mandatory
Consumers **must** be designed to process the exact same event multiple times safely.
*   Always check the `event_id` (Idempotency Key) or use `INSERT ... ON CONFLICT DO NOTHING`.
*   The Outbox pattern guarantees *at-least-once* delivery, meaning duplicates **will** happen in production.
