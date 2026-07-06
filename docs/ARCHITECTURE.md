# Book My Venue — System Architecture

# 1. Architecture Goal

Book My Venue is designed as a **multi-tenant SaaS platform** for venue businesses.

The system follows a **Microservices Architecture** where each bounded domain is an independent service with its own database, deployment, and lifecycle.

The architecture goals are:

* Multi-tenant SaaS platform
* Strong tenant data isolation
* Domain-driven modular structure
* API-first development
* Independent service deployment
* Production-ready authentication and authorization
* Scalable database architecture
* Clear separation of business domains
* Async processing support
* AI integration support

---

# 2. High-Level Architecture

```text
                    React Frontend
                           |
                           |
                    Nginx API Gateway (Port 8080)
                           |
          -------------------------------------------------
          |          |          |            |            |
    Auth Service  Venue     Booking    Notification   AI Service
    (Port 8001)  Service   Service      Service      (FastAPI)
                (Port 8002)(Port 8003)  (Port 8004)  (Port 8005)
          |          |          |            |            |
    auth_db      venue_db  booking_db  notification_db  ai_db
          |
    Redis (Shared)
    Celery Workers
```

---

# 3. Architecture Style

Current implementation:

```text
Microservices Architecture
```

Each service is:

* An independent Django REST Framework application
* Has its own PostgreSQL database
* Has its own Docker container
* Deployed independently
* Communicates over HTTP with internal API keys

---

# 4. Services Overview

```text
services/
├── auth-service/         Django + DRF + Celery — Authentication, users, tenants, emails
├── venue-service/        Django + DRF — Venues, images, amenities, policies
├── booking-service/      Django + DRF — Availability, bookings, conflict prevention
├── notification-service/ Django + DRF + Celery — Notifications
└── ai-service/           FastAPI — RAG and agentic AI features
```

---

# 5. Auth Service Structure

```text
auth-service/
├── apps/
│   ├── accounts/         Custom User model, JWT auth, customer profiles
│   ├── tenants/          Tenant, TenantDomain, TenantMembership, ServiceRegistry
│   └── common/           Shared utilities
├── config/
│   └── settings/
│       ├── base.py       Shared settings (installed apps, DRF, JWT, middleware)
│       ├── dev.py        DEBUG=True, Silk profiler, CORS open
│       └── prod.py       DEBUG=False, HTTPS, HSTS, strict CORS
├── manage.py
├── pyproject.toml        Ruff linter + formatter config
├── .pre-commit-config.yaml  Ruff hooks on every commit
└── requirements/
    ├── base.txt          Core dependencies
    ├── dev.txt           Dev-only dependencies (Silk, pre-commit, etc.)
    └── prod.txt          Production-only dependencies
```

Each app contains:

```text
core/
├── models.py       Domain models
├── services/       Business logic layer
├── selectors/      Read-only query layer
├── exceptions.py   Domain-specific exceptions
└── constants.py    Domain constants

api/
├── views/          Explicit APIViews only — no GenericAPIView or ViewSets
├── serializers/    Input/output serializers
└── urls/
    ├── public.py   Public-facing routes
    └── internal.py Internal service-to-service routes
```

---

# 6. Module Responsibilities

## 6.1 Accounts Module (auth-service)

Responsible for:

* Authentication
* User management
* JWT tokens
* Customer registration
* Vendor registration
* Current user information
* Internal context validation

### Owns

```text
User
CustomerProfile
```

### APIs

```text
POST /api/auth/register/customer/
POST /api/auth/register/vendor/
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
POST /api/auth/change-password/
POST /api/auth/verify-otp/
POST /api/auth/resend-otp/
GET  /api/auth/me/
POST /internal/auth/validate-context/
```

---

## 6.2 Tenants Module (auth-service)

Responsible for:

* Tenant creation
* Tenant memberships
* Tenant domains
* Service provisioning
* Tenant context

### Owns

```text
Tenant
TenantDomain
TenantMembership
ServiceRegistry
TenantServiceProvision
```

### APIs

```text
GET  /api/auth/tenants/my-tenants/
POST /api/auth/tenants/switch/
```

---

## 6.3 Venues Module (venue-service)

Responsible for:

* Venue management
* Venue images
* Amenities
* Categories
* Venue policies

### Owns

```text
Venue
VenueImage
Amenity
VenuePolicy
VenueCategory
```

---

## 6.4 Bookings Module (booking-service)

Responsible for:

* Availability
* Bookings
* Booking history
* Conflict prevention

### Owns

```text
Booking
AvailabilityRule
BlockedSlot
BookingStatusHistory
```

---

## 6.5 Notifications Module (notification-service)

Responsible for:

* Email notifications
* In-app notifications
* Templates
* Delivery tracking
* Celery task processing

### Owns

```text
Notification
NotificationTemplate
EmailLog
```

---

## 6.6 AI Module (ai-service)

Responsible for:

* RAG
* Embeddings
* AI assistant
* Venue recommendation
* Vendor insights

### Owns

```text
KnowledgeDocument
DocumentChunk
EmbeddingRecord
AIConversation
AIMessage
AIToolCall
```

---

# 7. Multi-Tenant Architecture

Book My Venue uses **Row-Level Tenancy** (also known as Shared Database, Shared Schema).

All tenant data lives in a single `public` schema. Tenant isolation is enforced at the application level through `tenant_id` foreign keys on relevant models and membership checks in the service layer.

This is the same approach used by Uber, Airbnb, and Shopify at scale. It avoids the operational overhead of schema-per-tenant while maintaining strong isolation through application-level access controls.

---

# 8. Database Layout

All tables in the auth-service live in a single `public` schema:

```text
public schema (auth_db)
│
├── accounts_user
├── accounts_customerprofile
├── tenants_tenant
├── tenants_tenantdomain
├── tenants_tenantmembership
├── tenants_serviceregistry
├── tenants_tenantserviceprovision
├── token_blacklist_outstandingtoken    (JWT token tracking)
├── token_blacklist_blacklistedtoken    (JWT blacklisting)
└── django_* (admin, sessions, migrations, content types)
```

Each downstream service uses its own isolated Neon PostgreSQL database:

```text
venue_db       → venue-service
booking_db     → booking-service
notification_db → notification-service
ai_db          → ai-service
```

---

# 9. Why Row-Level Tenancy?

Advantages:

### Scalability

No per-tenant schema overhead. Supports 10,000+ tenants without operational complexity.

### Simplicity

Standard Django ORM. No special middleware or database engine overrides.

### Industry Standard

Used by Uber, Airbnb, Shopify, and Stripe at massive scale.

### Enterprise Ready

Supports:

* Custom domains
* Feature flags per tenant (via ServiceRegistry)
* Subscription plan control
* Future SaaS monetization

---

# 10. Tenant Resolution Flow

```text
Incoming Request
        |
JWT Cookie Authentication (CustomJWTCookieAuthentication)
        |
Extract user_id from access token
        |
Read X-Tenant-Id header (for vendor/staff requests)
        |
Query TenantMembership to verify access
        |
Execute Request with tenant context
```

---

# 11. Data Ownership

## Auth Service (auth_db)

```text
Users, CustomerProfiles
Tenants, TenantDomains, TenantMemberships
ServiceRegistry, TenantServiceProvision
JWT Outstanding & Blacklisted Tokens
```

## Service-Specific Databases

```text
venue-service     → Venues, Images, Amenities, Policies
booking-service   → Bookings, Availability, Conflicts
notification-service → Notifications, Email Logs, Templates
ai-service        → Embeddings, Conversations, Tool Calls
```

---

# 12. Service Registry Architecture

Services are dynamically configurable.

```text
ServiceRegistry
```

stores:

```text
VENUES
BOOKINGS
NOTIFICATIONS
AI
REVIEWS
ANALYTICS
```

Each tenant gets provisioned services through:

```text
TenantServiceProvision
```

Benefits:

* Feature flags per tenant
* Subscription plan control
* Tenant-specific enablement
* Future SaaS monetization

---

# 13. Tenant Provisioning Flow

```text
Vendor Registration
        |
Create User
        |
Create Tenant
        |
Create Membership (OWNER role)
        |
Create Primary Domain
        |
Provision Active Services (bulk create TenantServiceProvision records)
        |
Tenant Status: PENDING (requires admin approval to become ACTIVE)
```

---

# 14. Authentication Architecture

Authentication is centralized in auth-service.

```text
JWT Authentication (djangorestframework-simplejwt)
Custom Cookie Authentication (CustomJWTCookieAuthentication)
```

Tokens:

```text
Access Token   — 15 minutes, HttpOnly cookie
Refresh Token  — 7 days, HttpOnly cookie, rotated on every use
```

Token Delivery:

```text
Tokens are set as HttpOnly cookies on login/refresh responses.
JavaScript cannot read them (XSS protection).
Browser sends them automatically on every request.
```

Fallback (mobile/internal):

```http
Authorization: Bearer <access_token>
```

Security Features:

```text
- Token rotation: old refresh token is blacklisted on every refresh
- Password change: all sessions terminated via bulk blacklisting
- Logout all devices: blacklists all outstanding tokens for the user
- Account lockout: 5 failed attempts → 15-minute lockout (Redis-backed)
- Rate limiting: 5 login attempts per minute (DRF throttle)
- Cookie flags: HttpOnly, Secure (prod), SameSite=Lax
```

---

# 15. Authorization Layers

## Layer 1

Authentication (JWT validation)

## Layer 2

Global Role

```text
ADMIN
USER
```

## Layer 3

Tenant Membership Role

```text
OWNER
MANAGER
STAFF
```

## Layer 4

Object Permissions

Example:

```text
Vendor can update only own venues.
```

---

# 16. Inter-Service Communication

Services communicate with each other via HTTP using internal APIs.

Protection:

```http
X-Internal-API-Key: <shared-secret>
```

Example: booking-service validates a user's context by calling:

```http
POST /internal/auth/validate-context/
X-Internal-API-Key: <key>

{
  "access_token": "...",
  "tenant_id": "..."
}
```

Auth service responds with:

```json
{
  "valid": true,
  "user": { "id": "...", "email": "...", "global_role": "USER" },
  "tenant": { "id": "...", "role": "OWNER" }
}
```

---

# 17. API Design Principles

All APIs use:

```text
APIView
```

No GenericAPIView. No ViewSets.

Reason:

* Explicit logic
* Better control
* Easier permission handling
* Easier scaling

---

# 18. API Documentation

API documentation uses:

```text
drf-spectacular
Swagger UI
OpenAPI 3
```

Every API has:

* Request schema
* Response schema
* Status codes

using:

```python
@extend_schema
```

Swagger UI available at:

```text
GET /api/docs/
```

ReDoc available at:

```text
GET /api/redoc/
```

---

# 19. Business Logic Pattern

Business logic should not be placed directly inside views.

Architecture:

```text
APIView
     ↓
Serializer (input validation only)
     ↓
Service Layer (business rules, transactions, side effects)
     ↓
Selector Layer (complex queries, reusable reads)
     ↓
Models
```

---

# 20. Services Layer

Responsible for:

* Business rules
* Atomic transactions (`@transaction.atomic`)
* Orchestration
* Side effects

Examples:

```text
register_customer()
register_vendor_orchestrator()
create_vendor_with_tenant()
```

---

# 21. Selectors Layer

Responsible for:

* Complex queries
* Optimized fetching (`select_related`, `prefetch_related`)
* Reusable read operations

Examples:

```text
get_active_user_by_id()
get_user_membership()
get_active_provision_services()
```

---

# 22. Database Architecture

Each service has its own isolated PostgreSQL database hosted on **Neon** (serverless Postgres).

Connection via `DATABASE_URL` environment variable, parsed by `dj-database-url`.

```python
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

No custom database engine overrides — standard PostgreSQL backend is used for all services.

---

# 23. Caching Layer

```text
Redis
```

Usage:

* Rate limiting
* Account lockout tracking (failed login attempts)
* OTP storage and verification
* Background task queue (Celery broker)
* Response cache
* Notification queuing

---

# 24. Background Processing

```text
Celery + Redis
```

Tasks:

* Emails
* Notifications
* Reports
* AI indexing
* Analytics

---

# 25. File Storage

```text
Cloudinary
```

Future:

```text
AWS S3
```

Used for:

* Venue images
* Documents
* Invoices

---

# 26. Dev Tooling

| Tool | Purpose |
|------|---------|
| `ruff` | Linting + formatting (replaces flake8, isort, black) |
| `pre-commit` | Enforces ruff on every git commit |
| `django-silk` | SQL query profiler (dev only) |
| `uv` | Fast Python package manager |
| `dj-database-url` | Parses `DATABASE_URL` into Django `DATABASES` config |
| `python-decouple` | Environment variable management |
| `drf-spectacular` | OpenAPI schema generation |

---

# 27. Deployment Architecture

```text
React Frontend (Static)
      |
Nginx API Gateway
      |
      ├── /api/auth/*       → auth-service (Django)
      ├── /api/venues/*     → venue-service (Django)
      ├── /api/bookings/*   → booking-service (Django)
      ├── /api/notifications/* → notification-service (Django)
      └── /api/ai/*         → ai-service (FastAPI)
```

Containerized using:

```text
Docker + Docker Compose
```

Each service:

```text
Dockerfile (multi-stage for production)
```

---

# 28. Health Endpoints

Every service exposes:

```http
GET /health/
```

Response:

```json
{
  "status": "ok",
  "service": "auth-service"
}
```

---

# 29. Settings Split Pattern

Every Django service follows:

```text
config/settings/
├── base.py    — All shared settings (apps, middleware, DRF, JWT, Spectacular)
├── dev.py     — DEBUG=True, CORS open, Silk profiler enabled
└── prod.py    — DEBUG=False, HTTPS enforced, HSTS, strict CORS, env-driven DB
```

Active settings controlled by:

```bash
DJANGO_SETTINGS_MODULE=config.settings.dev   # development
DJANGO_SETTINGS_MODULE=config.settings.prod  # production
```

---

# 30. Senior-Level Architecture Principles

* Domain-driven bounded services
* Service + Selector layer pattern
* Row-level multi-tenancy (Uber/Airbnb pattern)
* API-first design
* Explicit APIViews only
* OpenAPI documentation on every endpoint
* Transactional business logic (`@transaction.atomic`)
* Internal API key protection for inter-service calls
* JWT authentication with HttpOnly cookies and token rotation
* Global exception handler with consistent JSON error envelope
* Account lockout and brute-force protection
* OTP email verification
* Split settings (base/dev/prod) with production hardening
* UUID primary keys on all models
* Environment-driven configuration (no hardcoded secrets)
* Ruff + pre-commit for code quality enforcement
* Docker-first deployment strategy
* Neon (serverless Postgres) for database hosting
