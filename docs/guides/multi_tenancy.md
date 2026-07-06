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
