# 003. Use Transactional Outbox Pattern

Date: 2026-07-12

## Status
Accepted

## Context
When a microservice mutates state (e.g., creates a Venue) and needs to publish an event to Kafka, doing both operations synchronously creates a dual-write problem.
*   If DB commits but Kafka crashes -> Silent data loss. The event is never sent.
*   If Kafka acknowledges but DB fails -> Phantom event. Other services think a venue exists when it doesn't.

## Decision
We will implement the **Transactional Outbox Pattern**.

Instead of calling `producer.publish()` directly in the business logic, the service writes an `OutboxEvent` record to its local database *in the exact same transaction* as the business entity.

A background process (Celery Beat) then polls the `OutboxEvent` table and reliably forwards pending events to Kafka, marking them as `PUBLISHED` upon successful ACK.

## Alternatives Considered
*   **Direct Publish with Retries:** Brittle. If the pod dies before the retry succeeds, the event is lost.
*   **Change Data Capture (CDC / Debezium):** Extremely robust, but introduces heavy infrastructural complexity (requires Kafka Connect, specialized Postgres logical replication slots). Overkill for our current scale.
*   **Two-Phase Commit (2PC):** Too slow and not supported by Kafka in a way that pairs easily with Postgres.

## Consequences
*   **Positive:** Guarantees *at-least-once* delivery. Zero data loss. Tolerates Kafka downtime gracefully (events queue up in Postgres).
*   **Negative:** Adds slight latency to event publishing (due to the polling interval). Requires consumers to be idempotent since events may be delivered more than once during retry scenarios.
*   **Implementation:** We created `AbstractOutboxModel` in the shared `bmv_libraries` package, which provides state tracking (`PENDING`, `PUBLISHED`, `FAILED`) and retry fields, ensuring all services implement the outbox identically.
