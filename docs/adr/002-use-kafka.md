# 002. Use Kafka for Event-Driven Architecture

Date: 2026-07-12

## Status
Accepted

## Context
As the platform grows, synchronous REST calls between microservices create tight coupling, cascading failures, and high latency. For example, when a venue is approved, we need to notify the vendor, update the AI embeddings for search, and update analytics. Blocking the approval HTTP request to do all this is unacceptable.

## Decision
We will use **Apache Kafka** as the central event bus for asynchronous, inter-service communication (Event Choreography).

## Alternatives Considered
*   **RabbitMQ:** Excellent for task queues, but lacks long-term event retention and replayability, which is critical for rebuilding read models (e.g., AI Search Indexing).
*   **Redis Pub/Sub:** Extremely fast but transient. If a consumer is down during publish, the event is lost forever.
*   **AWS SQS/SNS:** Good managed alternative, but locks us into AWS. Kafka gives us cloud portability and higher throughput for event streaming.

## Consequences
*   **Positive:** True decoupling. Services can consume events at their own pace. Event replay allows bringing up new services (e.g., a new Recommendation Engine) and feeding it historical data.
*   **Negative:** High operational complexity. Requires managing topics, partitions, and consumer offsets. Minimum memory footprint is high.
*   **Implementation Strategy:** We will adopt a YAGNI (You Aren't Gonna Need It) approach. We define the event schemas and contracts in Phase 1, but we do not spin up the Kafka cluster until Phase 2 (when the Booking Service is built and there are multiple real consumers).
