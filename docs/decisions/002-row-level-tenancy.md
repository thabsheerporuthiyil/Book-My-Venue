# ADR 002: Row-Level Tenancy over Schema-Per-Tenant

**Date:** July 2026
**Status:** Accepted

## Context
Initially, the `auth-service` used `django-tenants` to implement a **Schema-Per-Tenant** architecture. Under this model, every time a new vendor registered, a dedicated PostgreSQL schema (e.g., `tenant_grand_hall`) was created. 

While this provided strong data isolation, it presented severe scalability and operational challenges:
1. **Migration Overhead**: Running `manage.py migrate_schemas` across thousands of tenants becomes prohibitively slow.
2. **Connection Pooling**: ORMs struggle with connection pooling when constantly switching schemas via `SET search_path`.
3. **Database Limitations**: PostgreSQL has limits on the optimal number of schemas before metadata lookups degrade performance.

## Decision
We removed `django-tenants` and migrated to a **Row-Level Tenancy** model (also known as Shared Database, Shared Schema).

1. All tenant data lives in the `public` schema.
2. Isolation is enforced at the application level by adding a `tenant_id` Foreign Key to relevant models.
3. Access control is enforced via the `TenantMembership` model and business logic in the Service Layer.

## Consequences
### Positive
- **Massive Scalability**: This is the model used by Uber, Airbnb, and Shopify. The system can easily scale to 10,000+ tenants without operational complexity.
- **Simplicity**: We use standard Django ORM features without needing custom database engine overrides.
- **Faster Migrations**: Migrations apply instantly to the single public schema.

### Negative
- **Risk of Data Bleed**: If a developer writes a query without filtering by `tenant_id` (or verifying user membership), cross-tenant data leakage can occur. 
- **Mitigation**: We mitigate this by strictly routing all business logic through the Service/Selector layers, where context validation is enforced, and never putting raw queries in API views.
