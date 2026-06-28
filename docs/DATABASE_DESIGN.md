# Book My Venue — Database Design

# 1. Database Strategy

Book My Venue uses:

```text
PostgreSQL
django-tenants
Schema Per Tenant Architecture
```

Current provider:

```text
Neon PostgreSQL
```

The system follows:

```text
Shared Database
+
Separate Schema Per Tenant
```

This gives:

* Strong tenant isolation
* Easier backups
* Better security
* Enterprise SaaS capabilities
* Easier future microservice extraction

---

# 2. PostgreSQL Schema Layout

## Public Schema

The `public` schema stores shared data used across all tenants.

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
├── django_migrations
├── django_content_type
├── django_admin_log
├── django_session
└── shared reference tables
```

---

## Tenant Schemas

Each tenant gets its own PostgreSQL schema.

Example:

```text
tenant_abc_hall
tenant_city_palace
tenant_grand_convention
tenant_green_auditorium
```

Each schema contains:

```text
venues
venue_images
amenities
venue_policies
bookings
availability_rules
blocked_slots
notifications
analytics
```

---

# 3. Shared Schema Tables (Public)

# 3.1 User

Stores all platform users.

```text
id UUID PK
email VARCHAR UNIQUE
password
full_name
phone
global_role
is_active
is_verified
last_login
created_at
updated_at
```

Indexes:

```text
email
global_role
is_active
```

---

# 3.2 CustomerProfile

```text
id UUID PK
user_id UUID FK
profile_image nullable
date_of_birth nullable
created_at
updated_at
```

Indexes:

```text
user_id
```

---

# 3.3 Tenant

Represents a vendor organization.

```text
id UUID PK
name
slug UNIQUE
schema_name UNIQUE
status
contact_email
contact_phone
created_by UUID FK
created_at
updated_at
```

Indexes:

```text
slug
schema_name
status
created_by
```

---

# 3.4 TenantDomain

Stores tenant domains.

```text
id UUID PK
tenant_id UUID FK
domain UNIQUE
is_primary
created_at
updated_at
```

Indexes:

```text
domain
tenant_id
```

Examples:

```text
grandhall.bookmyvenue.com
citypalace.bookmyvenue.com
```

---

# 3.5 TenantMembership

Stores users belonging to tenants.

```text
id UUID PK
tenant_id UUID FK
user_id UUID FK
role
is_active
created_at
updated_at
```

Roles:

```text
OWNER
ADMIN
MANAGER
STAFF
```

Indexes:

```text
tenant_id
user_id
role
is_active
```

Unique constraint:

```text
tenant_id + user_id
```

---

# 3.6 ServiceRegistry

Defines platform services.

```text
id UUID PK
code UNIQUE
name
description
is_active
requires_tenant_provisioning
created_at
updated_at
```

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
code
is_active
```

---

# 3.7 TenantServiceProvision

Stores services enabled for a tenant.

```text
id UUID PK
tenant_id UUID FK
service_id UUID FK
schema_name
is_enabled
provisioned_at
created_at
updated_at
```

Indexes:

```text
tenant_id
service_id
is_enabled
```

Unique constraint:

```text
tenant_id + service_id
```

---

# 4. Tenant Schema Tables

The following tables exist inside every tenant schema.

---

# 4.1 VenueCategory

```text
id UUID PK
name
slug UNIQUE
description
is_active
created_at
updated_at
```

Indexes:

```text
slug
is_active
```

---

# 4.2 Amenity

```text
id UUID PK
name
slug UNIQUE
icon nullable
is_active
created_at
updated_at
```

Indexes:

```text
slug
is_active
```

---

# 4.3 Venue

```text
id UUID PK
vendor_id UUID
category_id UUID
name
slug
description
address
city
state
country
postal_code
latitude nullable
longitude nullable
capacity
base_price
price_type
approval_status
is_active
created_at
updated_at
```

Indexes:

```text
vendor_id
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

# 4.4 VenueImage

```text
id UUID PK
venue_id UUID FK
image_url
public_id nullable
caption nullable
is_primary
sort_order
created_at
updated_at
```

Indexes:

```text
venue_id
is_primary
sort_order
```

---

# 4.5 VenueAmenity

```text
id UUID PK
venue_id UUID FK
amenity_id UUID FK
created_at
```

Unique constraint:

```text
venue_id + amenity_id
```

Indexes:

```text
venue_id
amenity_id
```

---

# 4.6 VenuePolicy

```text
id UUID PK
venue_id UUID FK
title
content
policy_type
created_at
updated_at
```

Indexes:

```text
venue_id
policy_type
```

---

# 5. Booking Tables

---

# 5.1 AvailabilityRule

```text
id UUID PK
venue_id UUID
day_of_week
start_time
end_time
is_available
created_at
updated_at
```

Indexes:

```text
venue_id
day_of_week
```

---

# 5.2 BlockedSlot

```text
id UUID PK
venue_id UUID
start_datetime
end_datetime
reason nullable
created_by UUID
created_at
updated_at
```

Indexes:

```text
venue_id
start_datetime
end_datetime
```

---

# 5.3 Booking

```text
id UUID PK
booking_reference UNIQUE
venue_id UUID
customer_id UUID
vendor_id UUID
start_datetime
end_datetime
guest_count
status
total_amount
special_requests nullable
rejection_reason nullable
cancelled_reason nullable
created_at
updated_at
```

Indexes:

```text
venue_id
customer_id
vendor_id
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

# 5.4 BookingStatusHistory

```text
id UUID PK
booking_id UUID
old_status nullable
new_status
changed_by UUID
reason nullable
created_at
```

Indexes:

```text
booking_id
new_status
```

---

# 6. Notification Tables

---

# 6.1 Notification

```text
id UUID PK
recipient_user_id UUID
notification_type
title
message
is_read
metadata JSONB
created_at
read_at nullable
```

Indexes:

```text
recipient_user_id
is_read
notification_type
```

---

# 6.2 NotificationTemplate

```text
id UUID PK
template_key UNIQUE
subject
body
channel
is_active
created_at
updated_at
```

Indexes:

```text
template_key
channel
is_active
```

---

# 6.3 EmailLog

```text
id UUID PK
recipient_email
subject
body
status
error_message nullable
sent_at nullable
created_at
```

Indexes:

```text
recipient_email
status
```

---

# 7. Future AI Tables

---

# 7.1 KnowledgeDocument

```text
id UUID PK
source_type
source_id
title
content
metadata JSONB
created_at
updated_at
```

---

# 7.2 DocumentChunk

```text
id UUID PK
document_id UUID
chunk_text
chunk_index
metadata JSONB
created_at
```

---

# 7.3 EmbeddingRecord

```text
id UUID PK
chunk_id UUID
embedding VECTOR
embedding_model
created_at
```

---

# 7.4 AIConversation

```text
id UUID PK
user_id UUID
session_title
created_at
updated_at
```

---

# 7.5 AIMessage

```text
id UUID PK
conversation_id UUID
role
content
metadata JSONB
created_at
```

---

# 7.6 AIToolCall

```text
id UUID PK
conversation_id UUID
tool_name
input_payload JSONB
output_payload JSONB
status
error_message
created_at
```

---

# 8. Booking Conflict Rule

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

Future:

```text
PENDING
ACCEPTED
```

with expiration support.

---

# 9. Transaction Rules

The following operations must always be atomic:

```text
Vendor Registration
Tenant Provisioning
Booking Creation
Booking Acceptance
Booking Cancellation
Payment Processing
```

Always use:

```python
transaction.atomic()
```

---

# 10. Soft Delete Strategy

Do not hard delete:

```text
Users
Venues
Bookings
Tenants
```

Use:

```text
is_active
status
```

instead.

---

# 11. Audit Fields

All important tables should contain:

```text
created_at
updated_at
created_by nullable
updated_by nullable
```

Current MVP:

```text
created_at
updated_at
```

---

# 12. Senior Level Database Principles

* UUID primary keys
* Schema based tenant isolation
* Proper indexing
* Unique constraints
* Composite indexes
* Transactional writes
* Soft deletion
* JSONB for flexible metadata
* Database level integrity
* Future pgvector support
* Production ready PostgreSQL design
* Easy migration to microservices
