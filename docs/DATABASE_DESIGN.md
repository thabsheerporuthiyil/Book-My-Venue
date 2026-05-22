# DATABASE_DESIGN.md

# Book My Venue — Database Design

## 1. Database Ownership Principle

In microservices, each service owns its own database.

Recommended databases:

```text
auth_db
venue_db
booking_db
notification_db
ai_db
```

Services should not directly modify another service's database.

## 2. Auth Service Database

## 2.1 User

Stores platform users.

Fields:

```text
id UUID primary key
email unique
password_hash
full_name
phone
role enum CUSTOMER/VENDOR/ADMIN
is_active boolean
is_verified boolean
created_at
updated_at
```

## 2.2 CustomerProfile

Fields:

```text
id UUID primary key
user_id UUID
date_of_birth nullable
profile_image nullable
created_at
updated_at
```

## 2.3 VendorProfile

Fields:

```text
id UUID primary key
user_id UUID
business_name
business_email
business_phone
approval_status enum PENDING/APPROVED/REJECTED/SUSPENDED
rejection_reason nullable
created_at
updated_at
```

## 2.4 RefreshToken

Fields:

```text
id UUID primary key
user_id UUID
token_hash
expires_at
revoked_at nullable
created_at
```

## 3. Venue Service Database

## 3.1 VenueCategory

Fields:

```text
id UUID primary key
name
slug unique
description nullable
is_active boolean
created_at
updated_at
```

Examples:

```text
Auditorium
Wedding Hall
Conference Hall
Party Hall
Turf
Event Space
```

## 3.2 Venue

Fields:

```text
id UUID primary key
vendor_id UUID
category_id UUID
name
slug unique
description
address
city
state
country
postal_code
latitude nullable
longitude nullable
capacity integer
base_price decimal
price_type enum HOURLY/HALF_DAY/FULL_DAY/CUSTOM
approval_status enum DRAFT/PENDING_APPROVAL/APPROVED/REJECTED/SUSPENDED
rejection_reason nullable
is_active boolean
created_at
updated_at
```

Notes:

- `vendor_id` comes from Auth Service.
- Venue Service stores vendor_id as reference only.
- Venue is visible to customers only when `approval_status = APPROVED`.

## 3.3 VenueImage

Fields:

```text
id UUID primary key
venue_id UUID
image_url
public_id nullable
caption nullable
is_primary boolean
sort_order integer
created_at
updated_at
```

## 3.4 Amenity

Fields:

```text
id UUID primary key
name
slug unique
icon nullable
is_active boolean
created_at
updated_at
```

Examples:

```text
Parking
AC
Stage
Dining Hall
Sound System
Projector
WiFi
Changing Room
```

## 3.5 VenueAmenity

Fields:

```text
id UUID primary key
venue_id UUID
amenity_id UUID
created_at
```

## 3.6 VenuePolicy

Fields:

```text
id UUID primary key
venue_id UUID
title
content
policy_type enum CANCELLATION/FOOD/MUSIC/PAYMENT/GENERAL/OTHER
created_at
updated_at
```

Examples:

```text
Outside catering allowed
Loud music not allowed after 10 PM
Cancellation allowed before 7 days
Advance payment required
```

## 4. Booking Service Database

## 4.1 AvailabilityRule

Defines regular availability of a venue.

Fields:

```text
id UUID primary key
venue_id UUID
day_of_week integer 0-6
start_time time
end_time time
is_available boolean
created_at
updated_at
```

Example:

```text
venue_id: VENUE_123
day_of_week: 6
start_time: 09:00
end_time: 22:00
```

## 4.2 BlockedSlot

Used when vendor blocks a date/time.

Fields:

```text
id UUID primary key
venue_id UUID
start_datetime
end_datetime
reason nullable
created_by UUID
created_at
updated_at
```

## 4.3 Booking

Fields:

```text
id UUID primary key
booking_reference unique
venue_id UUID
customer_id UUID
vendor_id UUID
start_datetime
end_datetime
guest_count integer
status enum PENDING/ACCEPTED/REJECTED/CANCELLED/EXPIRED/COMPLETED
total_amount decimal nullable
special_requests nullable
rejection_reason nullable
cancelled_reason nullable
created_at
updated_at
```

Important:

- `venue_id` references Venue Service data by ID.
- `customer_id` and `vendor_id` reference Auth Service users/profiles by ID.
- Booking Service owns booking status.
- Booking creation must check conflicts.

## 4.4 BookingStatusHistory

Fields:

```text
id UUID primary key
booking_id UUID
old_status nullable
new_status
changed_by UUID
reason nullable
created_at
```

## 5. Notification Service Database

## 5.1 Notification

Fields:

```text
id UUID primary key
recipient_user_id UUID
notification_type enum BOOKING_CREATED/BOOKING_ACCEPTED/BOOKING_REJECTED/VENUE_APPROVED/VENUE_REJECTED
title
message
is_read boolean
metadata jsonb nullable
created_at
read_at nullable
```

## 5.2 NotificationTemplate

Fields:

```text
id UUID primary key
template_key unique
subject
body
channel enum EMAIL/IN_APP/SMS/WHATSAPP
is_active boolean
created_at
updated_at
```

## 5.3 EmailLog

Fields:

```text
id UUID primary key
recipient_email
subject
body
status enum PENDING/SENT/FAILED
error_message nullable
sent_at nullable
created_at
```

## 6. AI Service Database

## 6.1 KnowledgeDocument

Stores documents used for RAG.

Fields:

```text
id UUID primary key
source_type enum VENUE_POLICY/HELP_DOC/FAQ/VENDOR_GUIDE/TERMS
source_id UUID nullable
title
content
metadata jsonb nullable
created_at
updated_at
```

## 6.2 DocumentChunk

Stores chunked text.

Fields:

```text
id UUID primary key
document_id UUID
chunk_text
chunk_index integer
metadata jsonb nullable
created_at
```

## 6.3 EmbeddingRecord

Stores vector embeddings.

Fields:

```text
id UUID primary key
chunk_id UUID
embedding vector
embedding_model
created_at
```

If using pgvector, `embedding` uses vector type.

## 6.4 AIConversation

Fields:

```text
id UUID primary key
user_id UUID
session_title nullable
created_at
updated_at
```

## 6.5 AIMessage

Fields:

```text
id UUID primary key
conversation_id UUID
role enum USER/ASSISTANT/SYSTEM/TOOL
content
metadata jsonb nullable
created_at
```

## 6.6 AIToolCall

Fields:

```text
id UUID primary key
conversation_id UUID
tool_name
input_payload jsonb
output_payload jsonb nullable
status enum SUCCESS/FAILED
error_message nullable
created_at
```

## 7. Important Indexes

## Auth DB

```text
User.email
User.role
VendorProfile.approval_status
```

## Venue DB

```text
Venue.city
Venue.category_id
Venue.capacity
Venue.base_price
Venue.approval_status
Venue.vendor_id
Amenity.slug
VenuePolicy.venue_id
```

## Booking DB

```text
Booking.venue_id
Booking.customer_id
Booking.vendor_id
Booking.status
Booking.start_datetime
Booking.end_datetime
Booking(venue_id, start_datetime, end_datetime)
```

## Notification DB

```text
Notification.recipient_user_id
Notification.is_read
EmailLog.status
```

## AI DB

```text
KnowledgeDocument.source_type
DocumentChunk.document_id
AIConversation.user_id
```

## 8. Booking Conflict Logic

A new booking conflicts if:

```text
existing_start < new_end
AND
existing_end > new_start
```

Only these statuses should block new bookings:

```text
ACCEPTED
```

Depending on business rule, `PENDING` may also temporarily block a slot.

Recommended first version:

```text
ACCEPTED blocks the slot.
PENDING does not block permanently but should be rechecked before accept.
```

For stricter booking:

```text
PENDING and ACCEPTED both block temporarily.
PENDING expires after fixed time.
```

## 9. Race Condition Protection

Danger case:

```text
User A checks availability.
User B checks availability.
Both see available.
Both create booking.
```

Solution:

- Use database transaction.
- Recheck conflict during booking creation.
- Lock relevant rows if needed.
- Keep booking creation atomic.

## 10. Deletion Rules

### Venue

Do not hard delete venue if future bookings exist.

Use:

```text
is_active = false
approval_status = SUSPENDED
```

### User

Do not hard delete user if booking history exists.

Use:

```text
is_active = false
```

### Booking

Do not delete bookings.

Use status changes.

## 11. Audit Fields

Every important table should include:

```text
created_at
updated_at
created_by nullable
updated_by nullable
```

For MVP, at least use:

```text
created_at
updated_at
```
