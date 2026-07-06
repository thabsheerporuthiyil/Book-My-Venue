# Service Provisioning Runbook

When a new vendor registers an organization (Tenant), they need access to various microservices (Venues, Bookings, Notifications, AI). 

We manage this using a **Service Registry** pattern.

## The Models
1. **`ServiceRegistry`**: A master list of all available services on the platform (e.g. `VENUES`, `BOOKINGS`, `AI`).
2. **`TenantServiceProvision`**: A mapping table indicating which services a specific tenant is allowed to use.

## How to add a new Microservice to the Platform
If you build a new microservice (e.g. `analytics-service`), you must register it so tenants can use it.

1. Open the Django Admin panel for `auth-service`.
2. Go to **Tenants** -> **Service Registries**.
3. Create a new record:
   - **Name**: `ANALYTICS`
   - **Display name**: `Analytics Service`
   - **Requires tenant provisioning**: Checked
   - **Is active**: Checked

Now, when a new vendor registers, the Orchestrator (`register_vendor_orchestrator`) will automatically read this active service and create a `TenantServiceProvision` record for the new tenant.

## Feature Toggles (Monetization)
This pattern allows for future SaaS monetization. 
If the `AI` service is only available on the "Pro" plan, you can simply write logic to *not* provision the `AI` service for tenants on the free plan. 

To manually revoke access to a service for a specific tenant:
1. Open the Django Admin panel.
2. Go to **Tenants** -> **Tenant Service Provisions**.
3. Find the record for the specific Tenant and Service.
4. Delete the record or change its status to `FAILED`.
