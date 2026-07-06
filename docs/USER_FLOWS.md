# Book My Venue — User Flows

# 1. Customer Registration Flow

```text
Customer
    |
    v
Register Page
    |
    v
POST /api/auth/register/customer/
    |
    v
Auth Service
    |
    ├── Validate input (email unique check)
    ├── Create User (global_role=USER, is_verified=False)
    ├── Create CustomerProfile
    └── Return user_id + email
```

Response:

```json
{
  "success": true,
  "message": "Customer registered successfully.",
  "data": {
    "user_id": "uuid",
    "email": "customer@example.com",
    "global_role": "USER"
  }
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
POST /api/auth/register/vendor/
```

Auth Service performs (all in one `@transaction.atomic` block):

```text
1. Validate email not already taken
2. Validate domain not already taken
3. Create User
4. Create Tenant (status=PENDING)
5. Create TenantMembership (role=OWNER)
6. Create TenantDomain (is_primary=True)
7. Bulk create TenantServiceProvision records for all active services
```

Flow:

```text
Vendor
    |
    v
Auth Service
    |
    ├── User created
    ├── Tenant created (status=PENDING — awaits admin approval)
    ├── Domain assigned (e.g. grand-hall.bookmyvenue.local)
    ├── Membership created (role=OWNER)
    └── Services provisioned (VENUES, BOOKINGS, NOTIFICATIONS, AI)
```

Response:

```json
{
  "success": true,
  "message": "Vendor registered successfully. Tenant is waiting for approval.",
  "data": {
    "user_id": "uuid",
    "email": "vendor@example.com",
    "tenant_id": "uuid",
    "domain": "grand-hall.bookmyvenue.local",
    "status": "PENDING"
  }
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
POST /api/auth/login/
```

Auth Service:

```text
1. Check if account is locked (Redis-backed lockout tracker)
2. Validate email + password credentials
3. Record failed attempt on failure (locks after 5 attempts for 15 min)
4. Check user.is_active
5. Check user.is_verified (OTP must be completed)
6. Clear lockout attempts on success
7. Generate JWT Access Token + Refresh Token
8. Set tokens as HttpOnly cookies on the response
9. Return user info
```

Response:

```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "User Name",
      "global_role": "USER"
    }
  }
}
```

> Tokens (`access_token`, `refresh_token`) are set as HttpOnly cookies.
> They are NOT returned in the JSON body.

---

# 4. Token Refresh Flow

```text
Frontend (access token expired — 401 response)
    |
    v
POST /api/auth/refresh/

Refresh token is automatically sent via HttpOnly cookie.
    |
    v
Auth Service
    |
    ├── Validate refresh token
    ├── Blacklist old refresh token (rotation)
    ├── Issue new access + refresh token pair
    └── Set new tokens as HttpOnly cookies
```

Response:

```json
{
  "success": true,
  "message": "Token refreshed."
}
```

> New cookies are set on the response. Old refresh token is permanently blacklisted.

---

# 5. OTP Verification Flow

```text
User (after registration)
    |
    v
POST /api/auth/verify-otp/
Body: { "email": "...", "otp": "123456" }
    |
    v
Auth Service
    |
    ├── Validate OTP from Redis cache
    ├── Set user.is_verified = True
    └── Delete OTP from Redis
```

If OTP expired or user needs a new one:

```text
POST /api/auth/resend-otp/
Body: { "email": "..." }
    |
    v
Auth Service
    |
    ├── Generate new 6-digit OTP
    ├── Store in Redis with TTL
    └── Send via email (best-effort)
```

---

# 6. My Profile Flow

```text
Frontend
    |
access_token sent via HttpOnly cookie (automatic)
    |
    v
GET /api/auth/me/
    |
    v
Auth Service
    |
    ├── Validate JWT from cookie (or Authorization header)
    ├── Load User from token's user_id
    └── Return user profile
```

---

# 7. Logout Flow

```text
User clicks "Logout"
    |
    v
POST /api/auth/logout/
Body: { "all_devices": false }
    |
    v
Auth Service
    |
    ├── Read refresh token from cookie
    ├── Blacklist the refresh token
    └── Delete access_token and refresh_token cookies
```

For "Logout All Devices":

```text
POST /api/auth/logout/
Body: { "all_devices": true }
    |
    v
Auth Service
    |
    ├── Query all OutstandingTokens for the user
    ├── Bulk blacklist all tokens
    └── Delete cookies
```

---

# 8. Password Change Flow

```text
User
    |
    v
POST /api/auth/change-password/
Body: { "current_password": "...", "new_password": "..." }
    |
    v
Auth Service
    |
    ├── Validate current password
    ├── Validate new password ≠ current password
    ├── Update password hash
    ├── Blacklist ALL outstanding tokens (terminates all sessions)
    └── Delete cookies from response
```

> This ensures that if an account is compromised and the user changes
> their password, the attacker is instantly kicked off all devices.

---

# 9. Tenant Selection Flow

A user (vendor/staff) may belong to multiple organizations.

```text
Frontend (after login)
    |
    v
GET /api/auth/tenants/my-tenants/
access_token sent via HttpOnly cookie (automatic)
    |
    v
Auth Service
    |
    └── Return list of tenant memberships for this user
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "tenant_id": "uuid",
      "tenant_name": "Grand Hall Events",
      "role": "OWNER",
      "status": "ACTIVE"
    }
  ]
}
```

Frontend stores:

```text
selectedTenantId → in localStorage / Zustand / Redux
```

---

# 7. Authenticated Request Flow

Every request to a protected vendor/staff API must include:

```http
Authorization: Bearer <access_token>
X-Tenant-Id: <tenant_uuid>
```

Services call auth-service's internal validate-context endpoint before processing:

```text
POST /internal/auth/validate-context/
X-Internal-API-Key: <shared-secret>

{
  "access_token": "<jwt>",
  "tenant_id": "<tenant_uuid>"
}
```

Auth service returns validated user + tenant context:

```json
{
  "valid": true,
  "user": {
    "id": "uuid",
    "email": "vendor@example.com",
    "global_role": "USER"
  },
  "tenant": {
    "id": "uuid",
    "role": "OWNER"
  }
}
```

---

# 8. Internal Context Validation Flow

```text
Incoming Request to any service
       |
       | Authorization: Bearer JWT
       | X-Tenant-Id: tenant_uuid
       |
       v
Service (venue-service, booking-service, etc.)
       |
       v
Call POST /internal/auth/validate-context/
X-Internal-API-Key: <key>
       |
       v
Auth Service validates:
   ├── JWT is valid
   ├── User exists and is_active=True
   ├── User has active membership in tenant
   └── Tenant status is ACTIVE
       |
       v
Returns: user_id, global_role, tenant_id, role
       |
       v
Service proceeds with request
```

---

# 9. Venue Creation Flow

```text
Tenant Owner
      |
      v
POST /api/venues/
Authorization: Bearer JWT
X-Tenant-Id: <tenant_uuid>
      |
      v
Venue Service
      |
      ├── Validate JWT + Tenant via auth-service
      ├── Check role (OWNER or MANAGER)
      ├── Create Venue (approval_status=PENDING_APPROVAL)
      └── Return venue data
```

Response:

```json
{
  "success": true,
  "message": "Venue created and submitted for approval.",
  "data": {
    "id": "uuid",
    "name": "Grand Hall Auditorium",
    "approval_status": "PENDING_APPROVAL"
  }
}
```

---

# 10. Venue Update Flow

```text
Tenant Owner / Manager
      |
      v
PATCH /api/venues/{venue_id}/
Authorization: Bearer JWT
X-Tenant-Id: <tenant_uuid>
      |
      v
Venue Service
      |
      ├── Validate JWT + Tenant
      ├── Check role (OWNER or MANAGER)
      ├── Check ownership (venue belongs to this tenant)
      └── Update Venue
```

---

# 11. Admin Venue Approval Flow

```text
Platform Admin
      |
      v
PATCH /api/venues/{venue_id}/approval/
Authorization: Bearer JWT (global_role=ADMIN)
      |
      v
Venue Service
      |
      ├── Validate JWT
      ├── Check global_role == ADMIN
      ├── Update approval_status → APPROVED | REJECTED | SUSPENDED
      └── Trigger notification to vendor
```

---

# 12. Venue Listing Flow (Public)

```text
Customer (no auth required)
      |
      v
GET /api/venues/?city=Calicut&category=auditorium&capacity_min=300
      |
      v
Venue Service
      |
      ├── Filter: approval_status=APPROVED, is_active=True
      ├── Apply query filters (city, category, price, capacity, amenities)
      ├── Paginate results
      └── Return list
```

Response:

```json
{
  "success": true,
  "data": {
    "count": 12,
    "next": "/api/venues/?page=2",
    "previous": null,
    "results": []
  }
}
```

---

# 13. Venue Detail Flow

```text
Customer
      |
      v
GET /api/venues/{venue_id}/
      |
      v
Venue Service
      |
      └── Return: details + images + amenities + policies + pricing
```

---

# 14. Booking Creation Flow

```text
Customer
      |
      v
POST /api/bookings/
Authorization: Bearer JWT
      |
      v
Booking Service
      |
      ├── Validate JWT via auth-service
      ├── Validate venue via venue-service internal API
      │     (check approval_status=APPROVED, is_active=True)
      ├── Check availability (conflict detection query)
      ├── Create Booking (status=PENDING)
      ├── Create BookingStatusHistory entry
      └── Trigger notification event (async)
```

Response:

```json
{
  "success": true,
  "message": "Booking request created successfully.",
  "data": {
    "id": "uuid",
    "booking_reference": "BMV-20260610-0001",
    "status": "PENDING"
  }
}
```

---

# 15. Booking Conflict Flow

```text
Customer A and Customer B attempt to book the same slot
      |
      v
Booking Service checks:

  existing_start < new_end
  AND
  existing_end > new_start
  AND
  existing_status IN (ACCEPTED)
```

If conflict:

```json
{
  "success": false,
  "message": "Selected slot is not available.",
  "errors": {
    "time_slot": "This venue already has a booking in the selected time range."
  }
}
```

---

# 16. Vendor Accept Booking Flow

```text
Vendor
      |
      v
PATCH /api/bookings/{booking_id}/accept/
Authorization: Bearer JWT
X-Tenant-Id: <tenant_uuid>
      |
      v
Booking Service
      |
      ├── Validate JWT + Tenant
      ├── Check role (OWNER or MANAGER)
      ├── Verify venue ownership
      ├── Recheck availability (prevents race conditions)
      ├── Update status: PENDING → ACCEPTED
      ├── Create BookingStatusHistory entry
      └── Trigger notification to customer
```

---

# 17. Vendor Reject Booking Flow

```text
PATCH /api/bookings/{booking_id}/reject/
Authorization: Bearer JWT
X-Tenant-Id: <tenant_uuid>

Body: { "reason": "Venue not available due to maintenance." }
      |
      v
Status: PENDING → REJECTED
```

---

# 18. Customer Cancel Booking Flow

```text
PATCH /api/bookings/{booking_id}/cancel/
Authorization: Bearer JWT
      |
      v
Booking Service
      |
      ├── Validate JWT
      ├── Verify customer owns this booking
      ├── Check cancellable statuses (PENDING or ACCEPTED)
      └── Update status → CANCELLED
```

Status transitions:

```text
PENDING  → CANCELLED
ACCEPTED → CANCELLED
```

---

# 19. Notification Flow

```text
Booking Event (created / accepted / rejected / cancelled)
       |
       v
Booking Service emits notification task (Celery)
       |
       v
Notification Service processes:
       ├── Load NotificationTemplate
       ├── Create Notification record (in-app)
       ├── Send Email via email provider
       └── Log to EmailLog
```

> Notification failure **must not** roll back the booking transaction.
> The notification task runs asynchronously via Celery.

---

# 20. Tenant Invitation Flow (Future)

```text
Owner
     |
     v
POST /api/auth/tenants/{tenant_id}/invite/
     |
     v
Auth Service
     |
     ├── Validate owner role
     ├── Create pending invitation record
     ├── Send invitation email
     └── Invitation link: /accept-invite?token=...

Invitee accepts:
     |
     v
POST /api/auth/tenants/accept-invite/
     |
     v
TenantMembership created with specified role
```

---

# 21. AI Recommendation Flow (Future)

```text
User: "I need an auditorium in Kochi for 500 people under ₹80,000."
      |
      v
POST /api/ai/recommend-venues/
Authorization: Bearer JWT
      |
      v
AI Service (FastAPI)
      |
      ├── Parse natural language query (LLM)
      ├── Extract filters: city, capacity_min, price_max, amenities
      ├── Call venue-service internal API with filters
      ├── Rank results with LLM reasoning
      └── Return recommendations with explanation
```

---

# 22. RAG Policy Q&A Flow (Future)

```text
User: "Can I bring outside food?"
      |
      v
POST /api/ai/venue-policy-question/

Body: { "venue_id": "uuid", "question": "Can I bring outside food?" }
      |
      v
AI Service
      |
      ├── Fetch venue policy chunks from vector store
      ├── Retrieve most relevant chunks (semantic search)
      ├── Pass chunks + question to LLM
      └── Return generated answer + source references
```

---

# 23. AI Booking Assistant Flow (Future)

```text
User
   |
   v
AI Assistant chat
   |
   ├── Search Venues (calls venue-service)
   ├── Check Availability (calls booking-service)
   ├── Suggest Options
   └── Create Booking Draft (user confirms)
```

> AI **never** confirms bookings directly.
> The Booking Service remains the single source of truth.

---

# 24. Failure Flow: AI Service Down

```text
AI Service Unavailable
        |
        v
Normal Booking Flow Continues Unaffected
        |
        v
AI features degrade gracefully — no impact on core booking
```

---

# 25. Failure Flow: Notification Service Down

```text
Booking Created Successfully
      |
Celery task queued for notification
      |
Notification Service unavailable
      |
Celery retries with exponential backoff
      |
Booking is NOT rolled back
```

---

# 26. Microservices Communication Flow

All services follow this pattern for inter-service calls:

```text
Service A
    |
    v
HTTP POST to Service B internal endpoint
Headers:
    X-Internal-API-Key: <shared-secret>
    Content-Type: application/json
    |
    v
Service B validates API key
    |
    v
Returns validated data
```

Services:

```text
auth-service        → provides user + tenant validation
venue-service       → provides venue validation for bookings
booking-service     → provides booking data for notifications
notification-service → consumes events from booking/venue services
ai-service          → calls venue-service and booking-service for data
```
