# 001. Use PostgreSQL for Relational Data

Date: 2026-07-12

## Status
Accepted

## Context
Book My Venue is a SaaS platform built using a microservices architecture. We need a primary datastore for the Auth, Venue, and future Booking services. The data model involves relational entities (Tenants, Users, Venues, Bookings) with strong consistency requirements (e.g., overlapping booking prevention, financial transactions).

## Decision
We will use **PostgreSQL** as the primary relational database for all microservices. Each microservice will have its own logical database within the PostgreSQL instance to enforce bounded contexts.

## Alternatives Considered
*   **MySQL:** Perfectly viable, but PostgreSQL's advanced features (native JSONB, better PostGIS integration for future location-based search, advanced indexing) make it a slightly better fit for this domain.
*   **MongoDB:** Rejected because the core domain is highly relational (User -> Tenant -> Venue -> Booking). NoSQL would require complex application-side joins and manual transaction management.

## Consequences
*   **Positive:** ACID compliance guarantees data integrity for bookings and payments. Native JSONB support allows for flexible schema extension (e.g., Venue Metadata, Policies) without sacrificing relational integrity for core fields.
*   **Negative:** Scaling writes is harder than with NoSQL databases, potentially requiring read replicas or sharding at massive scale.
*   **Implementation:** We are using Neon (Serverless Postgres) for cloud-native scaling and branching capabilities. Each service (e.g., `auth_db`, `venue_db`) uses its own separate database url.
