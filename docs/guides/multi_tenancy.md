# Multi-Tenancy Guide

Book My Venue is a SaaS platform serving multiple vendors (tenants) simultaneously. It uses a **Row-Level Tenancy** architecture.

## How it works
In a Row-Level Tenancy setup, all tenants share the exact same database and the exact same tables (`public` schema).

To ensure that Vendor A cannot see Vendor B's venues or bookings, we rely on application-level filtering.

### 1. The Tenant ID
Every resource that belongs to a specific vendor has a `tenant_id` Foreign Key.

```python
class Venue(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
```

### 2. Context Extraction
When a request comes into the API, the system determines the current tenant via the `X-Tenant-Id` header (for internal/vendor APIs).

Because a single user (e.g. an admin staff member) might belong to multiple tenants, they must specify which tenant context they are currently acting under.

### 3. Context Validation (Internal API)
Downstream microservices (like `venue-service` or `booking-service`) do not have access to the `TenantMembership` tables, which live in the `auth-service`.

To securely validate that a user actually has access to a specific `tenant_id`, downstream services make an HTTP call to the auth service:

```http
POST /internal/auth/validate-context/
X-Internal-API-Key: <secret>

{
  "access_token": "<jwt>",
  "tenant_id": "<uuid>"
}
```

The auth service checks the `TenantMembership` table and responds with the user's role (OWNER, MANAGER, STAFF) for that specific tenant.

### 4. Query Filtering
Once the downstream service validates the context, it **must** filter all database queries by that `tenant_id`.

```python
# GOOD: Safe, tenant-isolated query
venues = Venue.objects.filter(tenant_id=current_tenant_id)

# BAD: Data leak! Will return all venues across all tenants
venues = Venue.objects.all()
```

> **Warning:** Row-level tenancy requires strict discipline in the Service and Selector layers to ensure `tenant_id` is always applied to queries.

## 5. Tenant Provisioning
When a new Vendor registers on the platform, we must provision their multi-tenant environment. To ensure the API remains fast, this is handled **asynchronously via Celery**:

1. The Vendor registers via `/api/auth/register/vendor/`.
2. The API creates the `User`, `Tenant`, and `TenantMembership` (Role: OWNER) synchronously.
3. The API fires a Celery task: `dispatch_tenant_provisioning.delay(tenant_id)`.
4. The background worker reaches out to the `ServiceRegistry` and provisions the Tenant across all active downstream microservices (e.g., creating default Venue policies).

## 6. Architectural Decision: Why not `django-tenants`?
A common pattern in monolithic Django apps is "Schema-per-Tenant" using the `django-tenants` package, which creates a separate PostgreSQL schema for every tenant. We explicitly **chose not to use this** for the following reasons:

1. **Microservice Incompatibility:** `django-tenants` relies on routing requests via subdomains in a monolith. In our microservice architecture, replicating complex schema-routing logic across Auth, Venue, and Booking services would be an operational nightmare.
2. **Database Migrations at Scale:** If we have 10,000 tenants, `django-tenants` requires running migrations across 10,000 separate schemas, turning a 2-second deployment into hours of downtime. Row-level migrations run exactly once.
3. **Cross-Tenant Analytics:** Running aggregate queries across the entire platform (e.g., total platform bookings) requires looping through 10,000 schemas in `django-tenants`. In row-level tenancy, it is a single millisecond-fast SQL query.
4. **Serverless DB & Connection Pooling:** We use Neon DB. Heavy schema context-switching (`SET search_path TO tenantX`) degrades the performance of connection poolers (like PgBouncer) and serverless read-replicas. Row-level tenancy requires zero context switching.
