# Book My Venue — User Flows

# 1. Customer Registration Flow

```text
Customer
    |
    v
Register Page
    |
    v
POST /api/v1/auth/register/customer/
    |
    v
Auth Service
    |
    ├── Create User
    ├── Create Customer Profile
    └── Return Success
```

Response:

```json
{
  "message": "Registration successful."
}
```

---

# 2. Vendor Registration Flow

```text
Vendor
    |
    v
Register Page
    |
    v
POST /api/v1/auth/register/vendor/
```

Auth Service performs:

```text
Create User
Create Tenant
Create Domain
Create Tenant Membership
Provision Services
```

Flow:

```text
Vendor
    |
    v
Auth Service
    |
    ├── User
    ├── Tenant
    ├── Domain
    ├── Membership
    └── Service Provisioning
```

Response:

```json
{
  "message": "Vendor registration successful."
}
```

---

# 3. Login Flow

```text
User
    |
    v
Login Page
    |
    v
POST /api/v1/auth/login/
```

Auth Service:

```text
Validate credentials
Generate JWT tokens
Return user information
```

Response:

```json
{
  "access": "...",
  "refresh": "...",
  "user": {}
}
```

---

# 4. My Profile Flow

```text
Frontend
    |
Authorization: Bearer JWT
    |
    v
GET /api/v1/auth/me/
```

Backend:

```text
Validate JWT
Load User
Return User Profile
```

---

# 5. Tenant Selection Flow

A user may belong to multiple organizations.

```text
User
    |
    v
GET /api/v1/tenants/my-tenants/
```

Response:

```json
[
  {
    "tenant_id": "",
    "name": "",
    "role": "OWNER"
  }
]
```

User selects a tenant.

Frontend stores:

```text
selectedTenantId
```

---

# 6. Authenticated Request Flow

```text
Frontend
    |
Authorization: Bearer JWT
X-Tenant-Id: tenant_uuid
    |
    v
API
```

Every protected request contains:

```http
Authorization: Bearer <token>
X-Tenant-Id: <tenant_uuid>
```

---

# 7. Request Validation Flow

```text
Frontend
      |
      | Authorization: Bearer JWT
      | X-Tenant-Id
      |
      v
API Gateway
      |
      ├── Validate JWT
      ├── Verify Membership
      ├── Add Internal Headers
      |
      v
Application Service
```

Internal headers:

```text
X-User-Id
X-Tenant-Id
X-Role
```

---

# 8. Tenant Resolution Flow

Request:

```http
Authorization: Bearer xxx
X-Tenant-Id: tenant_uuid
```

Backend:

```text
JWT Authentication
        |
        v
Tenant Middleware
        |
        v
Find Membership
        |
        v
Set Current Tenant
```

Then:

```python
request.tenant
request.tenant_membership
request.role
```

become available.

---

# 9. Venue Creation Flow

```text
Tenant Owner
      |
      v
Create Venue
      |
      v
POST /api/v1/venues/
```

Backend:

```text
Validate JWT
Validate Tenant
Validate Role
Create Venue
```

Database:

```text
tenant_schema.venues
```

Response:

```json
{
  "id": "",
  "name": "",
  "status": "DRAFT"
}
```

---

# 10. Venue Update Flow

```text
Tenant Owner
      |
      v
PATCH /api/v1/venues/{id}/
```

Backend:

```text
Check Ownership
Check Role
Update Venue
```

---

# 11. Venue Listing Flow

```text
Customer
      |
      v
GET /api/v1/public/venues/
```

Filters:

* city
* category
* capacity
* price
* amenities

Response:

```json
{
  "count": 100,
  "results": []
}
```

---

# 12. Venue Detail Flow

```text
Customer
      |
      v
GET /api/v1/public/venues/{id}/
```

Returns:

* venue details
* images
* amenities
* policies
* pricing

---

# 13. Booking Creation Flow

```text
Customer
      |
      v
POST /api/v1/bookings/
```

Backend:

```text
Validate JWT
Validate Tenant
Validate Venue
Check Availability
Create Booking
```

Response:

```json
{
  "booking_reference": "BMV123456",
  "status": "PENDING"
}
```

---

# 14. Booking Conflict Flow

```text
Customer A
Customer B
      |
      v
Book Same Slot
```

System checks:

```text
existing_start < new_end
AND
existing_end > new_start
```

If conflict:

```json
{
  "message": "Selected slot is unavailable."
}
```

---

# 15. Vendor Accept Booking Flow

```text
Vendor
      |
      v
PATCH /api/v1/bookings/{id}/accept/
```

Backend:

```text
Validate Role
Verify Ownership
Recheck Availability
Update Status
```

Status:

```text
PENDING -> ACCEPTED
```

---

# 16. Vendor Reject Booking Flow

```text
PATCH /api/v1/bookings/{id}/reject/
```

Status:

```text
PENDING -> REJECTED
```

---

# 17. Customer Cancel Booking Flow

```text
PATCH /api/v1/bookings/{id}/cancel/
```

Status:

```text
PENDING -> CANCELLED
ACCEPTED -> CANCELLED
```

---

# 18. Notification Flow

```text
Booking Created
       |
       v
Event
       |
       v
Notification Service
       |
       ├── Email
       ├── In App Notification
       └── Push Notification
```

Notification failure should not affect booking creation.

---

# 19. Tenant Invitation Flow (Future)

```text
Owner
     |
     v
Invite Member
     |
     v
Email Invitation
     |
     v
Accept Invitation
     |
     v
Membership Created
```

---

# 20. AI Recommendation Flow (Future)

```text
User:
"I need an auditorium in Kochi for 500 people."
```

Flow:

```text
User
   |
   v
AI Service
   |
   ├── Extract Requirements
   ├── Search Venues
   ├── Rank Results
   └── Return Recommendations
```

---

# 21. RAG Policy Q&A Flow (Future)

```text
User:
"Can I bring outside food?"
```

Flow:

```text
User
   |
   v
AI Service
   |
   ├── Retrieve Policy Chunks
   ├── Generate Answer
   └── Return Response
```

---

# 22. AI Booking Assistant Flow (Future)

```text
User
   |
   v
AI Assistant
   |
   ├── Search Venues
   ├── Check Availability
   ├── Suggest Options
   └── Create Booking Draft
```

Important:

```text
AI never confirms bookings directly.
Booking Service remains the source of truth.
```

---

# 23. Failure Flow: AI Service Down

```text
AI Service Unavailable
        |
        v
Normal Booking Flow Continues
```

---

# 24. Failure Flow: Notification Service Down

```text
Booking Created
      |
Notification Failed
      |
Retry Later
```

Booking should never be rolled back.

---

# 25. Future Microservice Extraction Flow

Current:

```text
Django Modular Monolith
```

Future:

```text
Auth Service
Venue Service
Booking Service
Notification Service
AI Service
```

Communication:

```text
REST
Events
Queues
```

The current architecture is designed so that each module can be extracted into independent services with minimal refactoring.
