# Book My Venue — Database Design

# 1. Database Strategy

Book My Venue uses a **microservices** database architecture.

Every service has its own isolated PostgreSQL database hosted on **Neon** (serverless Postgres).

The auth-service uses **Row-Level Tenancy** (Shared Database, Shared Schema):

```text
All tenants share the same tables in a single public schema.
Tenant isolation is enforced at the application level via
foreign keys (tenant_id) and membership checks in the service layer.
```

This gives:

* Uber/Airbnb-level scalability (supports 10,000+ tenants)
* Standard Django ORM with no special database engine overrides
* Independent scaling of each service's database
* No cross-service database joins (services communicate via HTTP APIs)
* Easier future migrations per service

---

# 2. Database Per Service

| Service | Database | Hosting |
|---------|----------|---------|
| auth-service | `auth_db` | Neon PostgreSQL |
| venue-service | `venue_db` | Neon PostgreSQL |
| booking-service | `booking_db` | Neon PostgreSQL |
| notification-service | `notification_db` | Neon PostgreSQL |
| ai-service | `ai_db` | Neon PostgreSQL |

---

# 3. Auth Service — Database Layout

All tables live in the `public` schema. There are no per-tenant schemas.

```text
public
│
├── accounts_user
├── accounts_customerprofile
├── tenants_tenant
├── tenants_tenantdomain
├── tenants_tenantmembership
├── tenants_serviceregistry
├── tenants_tenantserviceprovision
├── token_blacklist_outstandingtoken
├── token_blacklist_blacklistedtoken
├── django_migrations
├── django_content_type
├── django_admin_log
├── django_session
└── silk_* (dev profiling tables)
```

---

# 4. Tables (Public Schema — auth-service)

## 4.1 User (`accounts_user`)

Stores all platform users. Inherits from Django's `AbstractUser`.

```text
id              UUID PK         auto-generated
email           VARCHAR UNIQUE  login identifier (no username)
password        VARCHAR
full_name       VARCHAR(255)
phone           VARCHAR(20)     optional
global_role     VARCHAR(20)     USER | ADMIN
is_active       BOOLEAN         default True
is_verified     BOOLEAN         default False
is_staff        BOOLEAN         default False (Django admin access)
is_superuser    BOOLEAN         default False
last_login      DATETIME        nullable
date_joined     DATETIME        auto
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
email (unique)
global_role
is_active
```

---

## 4.2 CustomerProfile (`accounts_customerprofile`)

```text
id              UUID PK
user_id         UUID FK → accounts_user (OneToOne, CASCADE)
profile_image   URLField        optional (Cloudinary URL)
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
user_id (unique — from OneToOneField)
```

---

## 4.3 Tenant (`tenants_tenant`)

Represents a vendor organization.

```text
id              UUID PK
name            VARCHAR(255)
slug            SlugField UNIQUE
status          VARCHAR(20)         PENDING | ACTIVE | SUSPENDED | REJECTED
contact_email   EmailField
contact_phone   VARCHAR(20)         optional
created_by      UUID FK → accounts_user (PROTECT)
created_at      DATETIME            auto_now_add
updated_at      DATETIME            auto_now
```

Indexes:

```text
slug (unique)
status
created_by
```

---

## 4.4 TenantDomain (`tenants_tenantdomain`)

Stores tenant domains.

```text
id              UUID PK
tenant_id       UUID FK → tenants_tenant (CASCADE)
domain          VARCHAR(255) UNIQUE     db_index=True
is_primary      BOOLEAN                 default True
created_at      DATETIME                auto_now_add
```

> Note: `updated_at` is intentionally absent — domains are not updated, only replaced.

Indexes:

```text
domain (unique, db_index)
tenant_id
```

Examples:

```text
grandhall.bookmyvenue.local
citypalace.bookmyvenue.local
```

---

## 4.5 TenantMembership (`tenants_tenantmembership`)

Stores users belonging to tenants.

```text
id              UUID PK
tenant_id       UUID FK → tenants_tenant (CASCADE)
user_id         UUID FK → accounts_user (CASCADE)
role            VARCHAR(20)     OWNER | MANAGER | STAFF
is_active       BOOLEAN         default True
created_at      DATETIME        auto_now_add
```

> Note: `updated_at` is intentionally absent in current model. Memberships are created and toggled via `is_active`.

Roles:

```text
OWNER     — full tenant control
MANAGER   — venue and booking management
STAFF     — limited operational access
```

Unique constraint:

```text
(tenant_id, user_id)
```

Indexes:

```text
tenant_id
user_id
role
is_active
```

---

## 4.6 ServiceRegistry (`tenants_serviceregistry`)

Defines platform services available for provisioning.

```text
id                          UUID PK
name                        VARCHAR(100) UNIQUE     service identifier (e.g. VENUES)
display_name                VARCHAR(150)            human-readable name
base_url                    URLField                optional service base URL
requires_tenant_provisioning BOOLEAN                default True
is_active                   BOOLEAN                 default True
provision_endpoint          VARCHAR(255)            default /internal/tenants/provision/
created_at                  DATETIME                auto_now_add
updated_at                  DATETIME                auto_now
```

Default ordering: `name` (alphabetical)

Examples:

```text
VENUES
BOOKINGS
NOTIFICATIONS
AI
ANALYTICS
REVIEWS
```

Indexes:

```text
name (unique)
is_active
```

---

## 4.7 TenantServiceProvision (`tenants_tenantserviceprovision`)

Stores services provisioned for each tenant.

```text
id              UUID PK
tenant_id       UUID FK → tenants_tenant (CASCADE)
service_id      UUID FK → tenants_serviceregistry (PROTECT)
status          VARCHAR(20)     PENDING | CREATED | FAILED
error_message   TextField       optional, populated on failure
provisioned_at  DATETIME        nullable, set when status → CREATED
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Unique constraint:

```text
(tenant_id, service_id)
```

Indexes:

```text
tenant_id
service_id
status
```

---

# 5. Venue Service Tables (`venue_db`)

---

## 5.1 VenueCategory

```text
id              UUID PK
name            VARCHAR
slug            SlugField UNIQUE
description     TextField       optional
is_active       BOOLEAN         default True
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
slug (unique)
is_active
```

---

## 5.2 Amenity

```text
id              UUID PK
name            VARCHAR
slug            SlugField UNIQUE
icon            VARCHAR         optional (icon class or URL)
is_active       BOOLEAN         default True
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
slug (unique)
is_active
```

---

## 5.3 Venue

```text
id              UUID PK
vendor_id       UUID            references auth-service user (cross-service)
tenant_id       UUID            references auth-service tenant (cross-service)
category_id     UUID FK → VenueCategory
name            VARCHAR
slug            SlugField
description     TextField
address         VARCHAR
city            VARCHAR
state           VARCHAR
country         VARCHAR
postal_code     VARCHAR
latitude        DECIMAL         nullable
longitude       DECIMAL         nullable
capacity        INTEGER
base_price      DECIMAL(10,2)
price_type      VARCHAR(20)     FULL_DAY | HALF_DAY | HOURLY
approval_status VARCHAR(20)     PENDING_APPROVAL | APPROVED | REJECTED | SUSPENDED
is_active       BOOLEAN         default True
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
vendor_id
tenant_id
category_id
city
capacity
base_price
approval_status
is_active
```

Composite indexes:

```text
(city, approval_status)
(category_id, approval_status)
(city, category_id)
```

---

## 5.4 VenueImage

```text
id              UUID PK
venue_id        UUID FK → Venue (CASCADE)
image_url       URLField
public_id       VARCHAR         optional (Cloudinary public_id)
caption         VARCHAR         optional
is_primary      BOOLEAN         default False
sort_order      INTEGER         default 0
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
venue_id
is_primary
sort_order
```

---

## 5.5 VenueAmenity (join table)

```text
id              UUID PK
venue_id        UUID FK → Venue (CASCADE)
amenity_id      UUID FK → Amenity (CASCADE)
created_at      DATETIME        auto_now_add
```

Unique constraint:

```text
(venue_id, amenity_id)
```

---

## 5.6 VenuePolicy

```text
id              UUID PK
venue_id        UUID FK → Venue (CASCADE)
title           VARCHAR
content         TextField
policy_type     VARCHAR(20)     CANCELLATION | FOOD | DECORATION | GENERAL
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
venue_id
policy_type
```

---

# 6. Booking Service Tables (`booking_db`)

---

## 6.1 AvailabilityRule

```text
id              UUID PK
venue_id        UUID            cross-service reference
day_of_week     INTEGER         0=Monday ... 6=Sunday
start_time      TIME
end_time        TIME
is_available    BOOLEAN         default True
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
venue_id
day_of_week
```

---

## 6.2 BlockedSlot

```text
id              UUID PK
venue_id        UUID            cross-service reference
start_datetime  DATETIME
end_datetime    DATETIME
reason          VARCHAR         optional
created_by      UUID            cross-service user reference
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
venue_id
start_datetime
end_datetime
```

---

## 6.3 Booking

```text
id                  UUID PK
booking_reference   VARCHAR UNIQUE      e.g. BMV-20260610-0001
venue_id            UUID                cross-service reference
customer_id         UUID                cross-service user reference
vendor_id           UUID                cross-service user reference
tenant_id           UUID                cross-service tenant reference
start_datetime      DATETIME
end_datetime        DATETIME
guest_count         INTEGER
status              VARCHAR(20)         PENDING | ACCEPTED | REJECTED | CANCELLED | COMPLETED | EXPIRED
total_amount        DECIMAL(12,2)
special_requests    TextField           optional
rejection_reason    TextField           optional
cancellation_reason TextField           optional
created_at          DATETIME            auto_now_add
updated_at          DATETIME            auto_now
```

Indexes:

```text
venue_id
customer_id
vendor_id
tenant_id
status
start_datetime
end_datetime
```

Composite indexes:

```text
(venue_id, start_datetime)
(venue_id, end_datetime)
(venue_id, status)
```

---

## 6.4 BookingStatusHistory

Audit trail for every booking status transition.

```text
id              UUID PK
booking_id      UUID FK → Booking (CASCADE)
old_status      VARCHAR(20)     nullable (null on creation)
new_status      VARCHAR(20)
changed_by      UUID            cross-service user reference
reason          TextField       optional
created_at      DATETIME        auto_now_add
```

Indexes:

```text
booking_id
new_status
```

---

# 7. Notification Service Tables (`notification_db`)

---

## 7.1 Notification

```text
id                  UUID PK
recipient_user_id   UUID            cross-service user reference
notification_type   VARCHAR(50)
title               VARCHAR
message             TextField
is_read             BOOLEAN         default False
metadata            JSONB           optional
created_at          DATETIME        auto_now_add
read_at             DATETIME        nullable
```

Indexes:

```text
recipient_user_id
is_read
notification_type
```

---

## 7.2 NotificationTemplate

```text
id              UUID PK
template_key    VARCHAR UNIQUE
subject         VARCHAR
body            TextField
channel         VARCHAR(20)     EMAIL | IN_APP | PUSH
is_active       BOOLEAN         default True
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

Indexes:

```text
template_key (unique)
channel
is_active
```

---

## 7.3 EmailLog

```text
id              UUID PK
recipient_email VARCHAR
subject         VARCHAR
body            TextField
status          VARCHAR(20)     PENDING | SENT | FAILED
error_message   TextField       optional
sent_at         DATETIME        nullable
created_at      DATETIME        auto_now_add
```

Indexes:

```text
recipient_email
status
```

---

# 8. AI Service Tables (`ai_db`)

---

## 8.1 KnowledgeDocument

```text
id              UUID PK
source_type     VARCHAR(50)     VENUE_POLICY | FAQ | HELP | VENDOR_DOC
source_id       UUID
title           VARCHAR
content         TextField
metadata        JSONB           optional
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

---

## 8.2 DocumentChunk

```text
id              UUID PK
document_id     UUID FK → KnowledgeDocument (CASCADE)
chunk_text      TextField
chunk_index     INTEGER
metadata        JSONB           optional
created_at      DATETIME        auto_now_add
```

---

## 8.3 EmbeddingRecord

```text
id              UUID PK
chunk_id        UUID FK → DocumentChunk (CASCADE)
embedding       VECTOR          pgvector column
embedding_model VARCHAR(100)
created_at      DATETIME        auto_now_add
```

---

## 8.4 AIConversation

```text
id              UUID PK
user_id         UUID            cross-service user reference
session_title   VARCHAR         optional
created_at      DATETIME        auto_now_add
updated_at      DATETIME        auto_now
```

---

## 8.5 AIMessage

```text
id                  UUID PK
conversation_id     UUID FK → AIConversation (CASCADE)
role                VARCHAR(20)     USER | ASSISTANT | SYSTEM
content             TextField
metadata            JSONB           optional
created_at          DATETIME        auto_now_add
```

---

## 8.6 AIToolCall

```text
id                  UUID PK
conversation_id     UUID FK → AIConversation (CASCADE)
tool_name           VARCHAR(100)
input_payload       JSONB
output_payload      JSONB
status              VARCHAR(20)     PENDING | SUCCESS | FAILED
error_message       TextField       optional
created_at          DATETIME        auto_now_add
```

---

# 9. Cross-Service Data References

Services do NOT share databases. Cross-service references store only UUIDs:

```text
booking.venue_id     → calls venue-service internal API to validate
booking.customer_id  → calls auth-service internal API to validate
booking.tenant_id    → calls auth-service internal API to validate
```

Internal API calls are protected with:

```http
X-Internal-API-Key: <shared-secret>
```

---

# 10. Booking Conflict Rule

A booking conflicts when:

```text
existing_start < new_end
AND
existing_end > new_start
```

Blocking statuses:

```text
ACCEPTED
```

Future (with PENDING expiration support):

```text
PENDING
ACCEPTED
```

---

# 11. Transaction Rules

The following operations must always be atomic:

```text
Vendor Registration      → @transaction.atomic
Tenant Provisioning      → @transaction.atomic
Booking Creation         → @transaction.atomic + conflict recheck
Booking Acceptance       → @transaction.atomic + availability recheck
Booking Cancellation     → @transaction.atomic
Payment Processing       → @transaction.atomic (future)
```

Always use:

```python
@transaction.atomic
def service_function():
    ...
```

---

# 12. Soft Delete Strategy

Do not hard delete:

```text
Users        → is_active = False
Venues       → is_active = False, approval_status = SUSPENDED
Bookings     → status = CANCELLED
Tenants      → status = SUSPENDED
```

Never expose deleted records in public APIs.

---

# 13. Audit Fields

All important tables contain:

```text
created_at    DATETIME    auto_now_add
updated_at    DATETIME    auto_now (where applicable)
```

Future:

```text
created_by    UUID        FK to user
updated_by    UUID        FK to user
```

---

# 14. Senior-Level Database Principles

* UUID primary keys on every model
* Schema-based tenant isolation (auth-service)
* Database-per-service (microservices pattern)
* Proper indexing on all query fields
* Composite indexes for multi-column search queries
* Unique constraints at the database level
* Transactional writes for all multi-step operations
* Soft deletion with `is_active` / `status` fields
* JSONB for flexible metadata storage
* pgvector for AI embedding storage (ai-service)
* Cross-service references via UUID only (no foreign keys across services)
* Internal HTTP APIs for cross-service data validation
