# Book My Venue — API Contracts

## 1. API Style

All APIs use JSON request and response bodies.

Base route through API Gateway:

```text
/api/auth/         → auth-service
/api/venues/       → venue-service
/api/bookings/     → booking-service
/api/notifications/ → notification-service
/api/ai/           → ai-service
```

Authentication:

```text
Tokens are delivered as HttpOnly cookies (access_token, refresh_token).
The browser sends them automatically on every request.
```

Fallback for mobile/internal:

```http
Authorization: Bearer <access_token>
```

Vendor/staff requests additionally require:

```http
X-Tenant-Id: <tenant_uuid>
```

---

## 2. Common Response Format

Success:

```json
{
  "success": true,
  "message": "Request successful.",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid input.",
  "errors": {}
}
```
```

Paginated response:

```json
{
  "success": true,
  "message": "Data fetched successfully.",
  "data": {
    "count": 100,
    "next": "http://localhost/api/venues/?page=2",
    "previous": null,
    "results": []
  }
}
```

---

## 3. Auth Service APIs

### 3.1 Register Customer

```http
POST /api/auth/register/customer/
```

Auth: None required

Request:

```json
{
  "full_name": "Customer One",
  "email": "customer@example.com",
  "phone": "9876543210",
  "password": "StrongPassword123"
}
```

Response `201`:

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

Error `409` — Email already taken:

```json
{
  "success": false,
  "error_code": "USER_ALREADY_EXISTS",
  "message": "A user with this email already exists."
}
```
```

---

### 3.2 Register Vendor

```http
POST /api/auth/register/vendor/
```

Auth: None required

Request:

```json
{
  "full_name": "Vendor One",
  "email": "vendor@example.com",
  "phone": "9876543210",
  "password": "StrongPassword123",
  "business_name": "Green Palace Events",
  "business_email": "business@greenpalace.com",
  "business_phone": "9876543211",
  "preferred_domain": "green-palace"
}
```

> `preferred_domain` is optional. If omitted, the slug of `business_name` is used.

Response `201`:

```json
{
  "success": true,
  "message": "Vendor registered successfully. Tenant is waiting for approval.",
  "data": {
    "user_id": "uuid",
    "email": "vendor@example.com",
    "tenant_id": "uuid",
    "domain": "green-palace.bookmyvenue.local",
    "status": "PENDING"
  }
}
```

Error `409` — Domain taken:

```json
{
  "success": false,
  "error_code": "DOMAIN_ALREADY_TAKEN",
  "message": "This domain is already taken."
}
```
```

---

### 3.3 Login

```http
POST /api/auth/login/
```

Auth: None required

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123"
}
```

Response `200`:

Tokens are set as `HttpOnly` cookies (`access_token`, `refresh_token`) on the response.

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

Error `401`:

```json
{
  "success": false,
  "error_code": "INVALID_CREDENTIALS",
  "message": "Invalid email or password."
}
```

Error `429` — Account locked:

```json
{
  "success": false,
  "error_code": "ACCOUNT_LOCKED",
  "message": "Account is temporarily locked due to too many failed attempts. Please try again in 15 minutes."
}
```
```

---

### 3.4 Token Refresh

```http
POST /api/auth/refresh/
```

Auth: Refresh token is read from the `refresh_token` HttpOnly cookie.

Request: No body needed. The refresh token is extracted from cookies.

Response `200`:

New `access_token` and `refresh_token` cookies are set on the response. The old refresh token is blacklisted (token rotation).

```json
{
  "success": true,
  "message": "Token refreshed."
}
```

Error `401`:

```json
{
  "success": false,
  "error_code": "INVALID_TOKEN",
  "message": "Invalid or expired refresh token."
}
```

---

### 3.5 Verify OTP

```http
POST /api/auth/verify-otp/
```

Auth: None required

Request:

```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Email verified successfully."
}
```

---

### 3.6 Resend OTP

```http
POST /api/auth/resend-otp/
```

Auth: None required

Request:

```json
{
  "email": "user@example.com"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "OTP sent successfully."
}
```

---

### 3.7 Logout

```http
POST /api/auth/logout/
```

Auth: `access_token` HttpOnly cookie (authenticated)

Request:

```json
{
  "all_devices": false
}
```

> Set `all_devices` to `true` to terminate all active sessions across all devices.

Response `200`:

```json
{
  "success": true,
  "message": "Logout successful."
}
```

Both `access_token` and `refresh_token` cookies are deleted from the response.

---

### 3.8 Change Password

```http
POST /api/auth/change-password/
```

Auth: `access_token` HttpOnly cookie (authenticated)

Request:

```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword456"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Password changed successfully. Please log in again."
}
```

> All active sessions are terminated and cookies are cleared. The user must log in again.

---

### 3.9 Get Current User

```http
GET /api/auth/me/
```

Auth: `access_token` HttpOnly cookie (authenticated)

Response `200`:

```json
{
  "success": true,
  "message": "User fetched successfully.",
  "data": {
    "id": "uuid",
    "full_name": "User Name",
    "email": "user@example.com",
    "phone": "9876543210",
    "global_role": "USER",
    "is_verified": false
  }
}
```

---

### 3.6 Get My Tenants

```http
GET /api/auth/tenants/my-tenants/
```

Auth: `access_token` HttpOnly cookie (authenticated)

Response `200`:

```json
{
  "success": true,
  "message": "Tenants fetched.",
  "data": [
    {
      "tenant_id": "uuid",
      "tenant_name": "Green Palace Events",
      "domain": "green-palace.bookmyvenue.local",
      "role": "OWNER",
      "status": "ACTIVE"
    }
  ]
}
```

---

## 4. Internal Auth Service APIs

> These routes are **not publicly exposed**. They are called by other services only.
> All requests must include `X-Internal-API-Key` header.

### 4.1 Validate Context

```http
POST /internal/auth/validate-context/
X-Internal-API-Key: <shared-secret>
```

Request:

```json
{
  "access_token": "<jwt_access_token>",
  "tenant_id": "uuid"
}
```

> `tenant_id` is optional. If omitted, only user-level validation is performed.

Response `200` — Valid:

```json
{
  "valid": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "global_role": "USER"
  },
  "tenant": {
    "id": "uuid",
    "role": "OWNER"
  }
}
```

Response `401` — Invalid token:

```json
{
  "valid": false,
  "message": "Invalid token."
}
```

Response `403` — No tenant access:

```json
{
  "valid": false,
  "message": "User lacks tenant access."
}
```

---

## 5. Venue Service APIs

### 5.1 Create Venue

```http
POST /api/venues/
```

Auth: `Authorization: Bearer <token>` + `X-Tenant-Id: <tenant_uuid>`

Role required: `OWNER` or `MANAGER`

Request:

```json
{
  "name": "Green Palace Auditorium",
  "category_id": "uuid",
  "description": "A premium auditorium for weddings and events.",
  "address": "Main Road",
  "city": "Calicut",
  "state": "Kerala",
  "country": "India",
  "postal_code": "673001",
  "capacity": 500,
  "base_price": "75000.00",
  "price_type": "FULL_DAY",
  "amenity_ids": ["uuid1", "uuid2"],
  "policies": [
    {
      "title": "Cancellation Policy",
      "content": "Cancellation allowed before 7 days.",
      "policy_type": "CANCELLATION"
    }
  ]
}
```

`price_type` values:

```text
FULL_DAY
HALF_DAY
HOURLY
```

Response `201`:

```json
{
  "success": true,
  "message": "Venue created and submitted for approval.",
  "data": {
    "id": "uuid",
    "name": "Green Palace Auditorium",
    "approval_status": "PENDING_APPROVAL"
  }
}
```

---

### 5.2 List Approved Venues (Public)

```http
GET /api/venues/?city=Calicut&capacity_min=300&price_max=80000&category=auditorium
```

Auth: None required

Query params:

```text
city             string
category         string (slug)
capacity_min     integer
capacity_max     integer
price_min        decimal
price_max        decimal
amenities        comma-separated UUIDs
page             integer (default 1)
page_size        integer (default 20, max 100)
```

Response `200`:

```json
{
  "success": true,
  "message": "Venues fetched successfully.",
  "data": {
    "count": 12,
    "next": "/api/venues/?page=2",
    "previous": null,
    "results": [
      {
        "id": "uuid",
        "name": "Green Palace Auditorium",
        "city": "Calicut",
        "capacity": 500,
        "base_price": "75000.00",
        "price_type": "FULL_DAY",
        "primary_image": "https://res.cloudinary.com/example/image.jpg",
        "approval_status": "APPROVED"
      }
    ]
  }
}
```

---

### 5.3 Get Venue Detail (Public)

```http
GET /api/venues/{venue_id}/
```

Auth: None required

Response `200`:

```json
{
  "success": true,
  "message": "Venue fetched successfully.",
  "data": {
    "id": "uuid",
    "name": "Green Palace Auditorium",
    "description": "A premium auditorium for weddings and events.",
    "address": "Main Road",
    "city": "Calicut",
    "state": "Kerala",
    "country": "India",
    "capacity": 500,
    "base_price": "75000.00",
    "price_type": "FULL_DAY",
    "amenities": ["Parking", "AC", "Stage"],
    "policies": [
      {
        "title": "Cancellation Policy",
        "content": "Cancellation allowed before 7 days.",
        "policy_type": "CANCELLATION"
      }
    ],
    "images": [
      {
        "image_url": "https://res.cloudinary.com/example/image.jpg",
        "is_primary": true
      }
    ]
  }
}
```

---

### 5.4 Approve / Reject Venue

```http
PATCH /api/venues/{venue_id}/approval/
```

Auth: `Authorization: Bearer <token>` (global_role=ADMIN)

Request:

```json
{
  "approval_status": "APPROVED",
  "reason": null
}
```

`approval_status` values:

```text
APPROVED
REJECTED
SUSPENDED
```

Response `200`:

```json
{
  "success": true,
  "message": "Venue approval status updated.",
  "data": {
    "id": "uuid",
    "approval_status": "APPROVED"
  }
}
```

---

### 5.5 Internal — Venue Booking Validation

```http
GET /internal/venues/{venue_id}/booking-validation/
X-Internal-API-Key: <shared-secret>
```

Called by booking-service before creating a booking.

Response `200`:

```json
{
  "id": "uuid",
  "vendor_id": "uuid",
  "tenant_id": "uuid",
  "approval_status": "APPROVED",
  "is_active": true,
  "base_price": "75000.00",
  "price_type": "FULL_DAY",
  "capacity": 500
}
```

---

## 6. Booking Service APIs

### 6.1 Check Availability

```http
POST /api/bookings/check-availability/
```

Auth: None required

Request:

```json
{
  "venue_id": "uuid",
  "start_datetime": "2026-06-10T18:00:00+05:30",
  "end_datetime": "2026-06-10T22:00:00+05:30"
}
```

Available response `200`:

```json
{
  "success": true,
  "message": "Venue is available.",
  "data": {
    "available": true,
    "conflicts": []
  }
}
```

Unavailable response `200`:

```json
{
  "success": true,
  "message": "Venue is not available.",
  "data": {
    "available": false,
    "conflicts": [
      {
        "booking_id": "uuid",
        "start_datetime": "2026-06-10T17:00:00+05:30",
        "end_datetime": "2026-06-10T20:00:00+05:30"
      }
    ]
  }
}
```

---

### 6.2 Create Booking Request

```http
POST /api/bookings/
```

Auth: `Authorization: Bearer <token>`

Role: Customer (global_role=USER)

Request:

```json
{
  "venue_id": "uuid",
  "start_datetime": "2026-06-10T18:00:00+05:30",
  "end_datetime": "2026-06-10T22:00:00+05:30",
  "guest_count": 400,
  "special_requests": "Need decoration support."
}
```

Response `201`:

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

Conflict response `409`:

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

### 6.3 Vendor Booking Requests

```http
GET /api/bookings/vendor/
```

Auth: `Authorization: Bearer <token>` + `X-Tenant-Id: <tenant_uuid>`

Role: `OWNER` or `MANAGER`

Response `200`:

```json
{
  "success": true,
  "message": "Vendor bookings fetched successfully.",
  "data": {
    "count": 5,
    "results": [
      {
        "id": "uuid",
        "booking_reference": "BMV-20260610-0001",
        "venue_id": "uuid",
        "customer_id": "uuid",
        "start_datetime": "2026-06-10T18:00:00+05:30",
        "end_datetime": "2026-06-10T22:00:00+05:30",
        "guest_count": 400,
        "status": "PENDING"
      }
    ]
  }
}
```

---

### 6.4 Accept Booking

```http
PATCH /api/bookings/{booking_id}/accept/
```

Auth: `Authorization: Bearer <token>` + `X-Tenant-Id: <tenant_uuid>`

Role: `OWNER` or `MANAGER`

Response `200`:

```json
{
  "success": true,
  "message": "Booking accepted successfully.",
  "data": {
    "id": "uuid",
    "status": "ACCEPTED"
  }
}
```

---

### 6.5 Reject Booking

```http
PATCH /api/bookings/{booking_id}/reject/
```

Auth: `Authorization: Bearer <token>` + `X-Tenant-Id: <tenant_uuid>`

Role: `OWNER` or `MANAGER`

Request:

```json
{
  "reason": "Venue is not available due to maintenance."
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Booking rejected successfully.",
  "data": {
    "id": "uuid",
    "status": "REJECTED"
  }
}
```

---

### 6.6 Cancel Booking (Customer)

```http
PATCH /api/bookings/{booking_id}/cancel/
```

Auth: `Authorization: Bearer <token>`

Response `200`:

```json
{
  "success": true,
  "message": "Booking cancelled successfully.",
  "data": {
    "id": "uuid",
    "status": "CANCELLED"
  }
}
```

---

### 6.7 Customer Booking History

```http
GET /api/bookings/my-bookings/
```

Auth: `Authorization: Bearer <token>`

Response `200`:

```json
{
  "success": true,
  "message": "Bookings fetched successfully.",
  "data": {
    "count": 3,
    "results": [
      {
        "id": "uuid",
        "booking_reference": "BMV-20260610-0001",
        "venue_id": "uuid",
        "start_datetime": "2026-06-10T18:00:00+05:30",
        "end_datetime": "2026-06-10T22:00:00+05:30",
        "status": "ACCEPTED"
      }
    ]
  }
}
```

---

## 7. Notification Service APIs

### 7.1 List My Notifications

```http
GET /api/notifications/
```

Auth: `Authorization: Bearer <token>`

Response `200`:

```json
{
  "success": true,
  "message": "Notifications fetched successfully.",
  "data": {
    "count": 3,
    "results": [
      {
        "id": "uuid",
        "title": "Booking Accepted",
        "message": "Your booking for Grand Hall has been accepted.",
        "notification_type": "BOOKING_ACCEPTED",
        "is_read": false,
        "created_at": "2026-06-10T10:00:00+05:30"
      }
    ]
  }
}
```

---

### 7.2 Mark Notification as Read

```http
PATCH /api/notifications/{notification_id}/read/
```

Auth: `Authorization: Bearer <token>`

Response `200`:

```json
{
  "success": true,
  "message": "Notification marked as read.",
  "data": {}
}
```

---

## 8. AI Service APIs

### 8.1 AI Venue Recommendation

```http
POST /api/ai/recommend-venues/
```

Auth: `Authorization: Bearer <token>`

Request:

```json
{
  "query": "I need a wedding hall in Calicut for 500 people under ₹80,000 with parking.",
  "date": "2026-06-10",
  "start_time": "18:00",
  "end_time": "22:00"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Recommended venues generated.",
  "data": {
    "extracted_filters": {
      "city": "Calicut",
      "capacity_min": 500,
      "price_max": 80000,
      "amenities": ["Parking"]
    },
    "recommendations": [
      {
        "venue_id": "uuid",
        "name": "Green Palace Auditorium",
        "reason": "Matches your capacity, budget, and parking requirement."
      }
    ]
  }
}
```

---

### 8.2 Venue Policy Question

```http
POST /api/ai/venue-policy-question/
```

Auth: `Authorization: Bearer <token>`

Request:

```json
{
  "venue_id": "uuid",
  "question": "Is outside catering allowed?"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Answer generated.",
  "data": {
    "answer": "Outside catering is allowed, but an additional cleaning fee may apply.",
    "sources": [
      {
        "document_id": "uuid",
        "policy_title": "Food Policy"
      }
    ]
  }
}
```

---

### 8.3 Generate Venue Description

```http
POST /api/ai/generate-venue-description/
```

Auth: `Authorization: Bearer <token>` + `X-Tenant-Id: <tenant_uuid>`

Role: `OWNER` or `MANAGER`

Request:

```json
{
  "venue_name": "Green Palace Auditorium",
  "city": "Calicut",
  "capacity": 500,
  "amenities": ["Parking", "AC", "Stage", "Dining Hall"],
  "venue_type": "Wedding Hall"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Description generated successfully.",
  "data": {
    "description": "Green Palace Auditorium is a spacious, elegantly appointed wedding hall in the heart of Calicut..."
  }
}
```

---

## 9. Error Status Codes

| Code | Meaning |
|------|---------|
| `200` | OK |
| `201` | Created |
| `400` | Bad Request (validation error, business rule violation) |
| `401` | Unauthorized (missing/invalid/expired JWT) |
| `403` | Forbidden (insufficient role or tenant access) |
| `404` | Not Found |
| `409` | Conflict (booking slot conflict, duplicate resource) |
| `422` | Unprocessable Entity (invalid datetime format, etc.) |
| `500` | Internal Server Error |

Examples:

```text
401 → Missing or expired JWT token
403 → User does not have OWNER or MANAGER role
404 → Venue not found
409 → Booking slot conflict
422 → Invalid datetime format in booking request
```

---

## 10. Senior-Level API Rules

1. Every protected endpoint must validate JWT via auth-service.
2. Every vendor/staff endpoint must validate tenant membership and role.
3. Every vendor action must verify object ownership (vendor can only manage their own venues/bookings).
4. Booking creation must recheck availability atomically.
5. AI responses must never bypass Booking Service validation.
6. All list APIs must be paginated (no unbounded queries).
7. All APIs must return a consistent `{success, message, data}` response format.
8. Internal APIs must be protected with `X-Internal-API-Key` header.
9. All datetime values must be timezone-aware (ISO 8601 with offset).
10. Conflict response for booking must use HTTP `409` not `400`.
