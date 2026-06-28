# Book My Venue — System Architecture

# 1. Architecture Goal

Book My Venue is designed as a **multi-tenant SaaS platform** for venue businesses.

The system follows a **Modular Monolith architecture** in the MVP stage while keeping clear boundaries that allow extraction into microservices in the future.

The architecture goals are:

* Multi tenant SaaS platform
* Strong tenant data isolation
* Domain driven modular structure
* API first development
* Easy future migration to microservices
* Production ready authentication and authorization
* Scalable database architecture
* Clear separation of business domains
* Async processing support
* AI integration support

---

# 2. High Level Architecture

```text
                    React Frontend
                           |
                           |
                    Nginx / API Gateway
                           |
                           |
                 Django Modular Monolith
                           |
        ------------------------------------------------
        |              |              |               |
     Accounts        Tenants        Venues         Bookings
        |              |              |               |
        ------------------------------------------------
                           |
                     Notification Module
                           |
                         AI Module
                           |
                    PostgreSQL + Redis
```

---

# 3. Architecture Style

Current implementation:

```text
Modular Monolith
```

Future target:

```text
Microservices Architecture
```

Reason:

A modular monolith is easier to:

* develop
* deploy
* maintain
* debug
* test

during the early stages of a SaaS product.

When traffic and team size increase, modules can be extracted into independent services.

---

# 4. Application Structure

```text
apps/
├── accounts/
├── tenants/
├── venues/
├── bookings/
├── notifications/
├── ai/
├── common/
└── core/
```

Each module contains:

```text
models.py
serializers.py
views.py
services.py
selectors.py
permissions.py
urls.py
```

---

# 5. Module Responsibilities

# 5.1 Accounts Module

Responsible for:

* Authentication
* User management
* JWT tokens
* Customer registration
* Vendor registration
* Current user information
* Context validation

### Owns

```text
User
CustomerProfile
RefreshToken
```

### APIs

```text
POST /api/auth/register/customer/
POST /api/auth/register/vendor/
POST /api/auth/login/
POST /api/auth/refresh/
GET  /api/auth/me/
POST /api/auth/context/
```

---

# 5.2 Tenants Module

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
GET /api/tenants/my-tenants/
POST /api/tenants/switch/
```

---

# 5.3 Venues Module

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

# 5.4 Bookings Module

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

# 5.5 Notifications Module

Responsible for:

* Email notifications
* In app notifications
* Templates
* Delivery tracking

### Owns

```text
Notification
NotificationTemplate
EmailLog
```

---

# 5.6 AI Module

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

# 6. Multi Tenant Architecture

Book My Venue uses:

```text
django-tenants
```

with:

```text
Schema Per Tenant
```

architecture.

---

# 7. PostgreSQL Schema Layout

```text
public
│
├── users
├── customer_profiles
├── tenants
├── tenant_domains
├── tenant_memberships
├── service_registry
├── tenant_service_provisions
└── shared_reference_tables
```

Tenant schemas:

```text
tenant_abc_hall
tenant_green_palace
tenant_city_auditorium
tenant_star_convention
```

Each tenant schema contains:

```text
venues
bookings
notifications
analytics
```

---

# 8. Why Schema Based Multi Tenancy?

Advantages:

### Strong Isolation

Each tenant has its own schema.

### Security

One tenant cannot accidentally read another tenant's data.

### Easier Backup

Individual tenant backup and restore.

### Easier Migration

Tenant specific migrations.

### Enterprise Ready

Supports:

* white labeling
* custom domains
* custom features
* subscription plans

---

# 9. Tenant Resolution Flow

```text
Incoming Request
        |
        |
Tenant Middleware
        |
        |
Resolve Domain
        |
        |
Load Tenant Schema
        |
        |
Set search_path
        |
        |
Execute Request
```

Example:

```text
abc.bookmyvenue.com
```

loads:

```text
tenant_abc
```

schema.

---

# 10. Shared Data vs Tenant Data

## Shared (Public Schema)

```text
Users
Authentication
Tenants
Memberships
Subscriptions
Service Registry
Domains
```

## Tenant Schema

```text
Venues
Bookings
Notifications
Analytics
Reviews
Reports
```

---

# 11. Service Registry Architecture

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

* feature flags
* subscription plans
* tenant specific enablement
* future SaaS monetization

---

# 12. Tenant Provisioning Flow

```text
Vendor Registration
        |
Create User
        |
Create Tenant
        |
Create Membership
        |
Create Domain
        |
Provision Services
        |
Create Tenant Schema
        |
Run Tenant Migrations
```

---

# 13. Authentication Architecture

Authentication is centralized.

```text
JWT Authentication
```

Tokens:

```text
Access Token
Refresh Token
```

Header:

```http
Authorization: Bearer <token>
```

---

# 14. Authorization Layers

## Layer 1

Authentication

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
ADMIN
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

# 15. API Design Principles

All APIs use:

```text
APIView
```

No GenericAPIView.

No ViewSets.

Reason:

* explicit logic
* better control
* easier scaling
* easier permission handling

---

# 16. API Documentation

API documentation uses:

```text
drf-spectacular
Swagger UI
OpenAPI 3
```

Every API has:

* request schema
* response schema
* status codes

using:

```python
@extend_schema
```

---

# 17. Business Logic Pattern

Business logic should not be placed directly inside views.

Architecture:

```text
APIView
     ↓
Serializer
     ↓
Service Layer
     ↓
Selector Layer
     ↓
Models
```

---

# 18. Services Layer

Responsible for:

* business rules
* transactions
* orchestration
* side effects

Example:

```text
create_tenant()
create_booking()
accept_booking()
```

---

# 19. Selectors Layer

Responsible for:

* complex queries
* optimized fetching
* reusable read operations

Example:

```text
get_user_tenants()
get_tenant_membership()
get_available_venues()
```

---

# 20. Database Architecture

Current database:

```text
PostgreSQL
```

Provider:

```text
Neon
```

Environment:

```text
DATABASE_URL
```

Connection pooling:

```text
PgBouncer
```

---

# 21. Caching Layer

Future:

```text
Redis
```

Usage:

* rate limiting
* cache
* background jobs
* sessions
* OTP
* notifications

---

# 22. Background Processing

Future:

```text
Celery
Redis
```

Tasks:

* emails
* notifications
* reports
* AI indexing
* analytics

---

# 23. File Storage

Future:

```text
AWS S3
```

Used for:

* venue images
* documents
* invoices

---

# 24. Logging

Future:

```text
Structured Logging
```

Stack:

```text
Django Logging
Sentry
ELK
```

---

# 25. Deployment Architecture

```text
Frontend
     |
Nginx
     |
Django App
     |
PostgreSQL (Neon)
     |
Redis
```

Containerized using:

```text
Docker
Docker Compose
```

---

# 26. Health Endpoints

```http
GET /health/
```

Response:

```json
{
  "status": "ok"
}
```

---

# 27. Future Extraction to Microservices

Possible extraction order:

```text
1. Notifications
2. AI
3. Bookings
4. Venues
5. Accounts
```

The current modular architecture is intentionally designed so each module can become an independent service with minimal refactoring.

---

# 28. Senior Level Architecture Principles

* Domain driven modules
* Service layer pattern
* Selector pattern
* Multi tenant architecture
* API first design
* Schema based isolation
* Explicit APIViews
* OpenAPI documentation
* Transactional business logic
* Future microservice readiness
* Production ready PostgreSQL architecture
* Clear ownership boundaries
* SaaS friendly design
