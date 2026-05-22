# API_CONTRACTS.md

# Book My Venue — API Contracts

## 1. API Style

All APIs should use JSON request and response bodies.

Base route through API Gateway:

```text
/api/auth
/api/venues
/api/bookings
/api/notifications
/api/ai
```

Authentication header:

```http
Authorization: Bearer <access_token>
```

## 2. Common Response Format

Success:

```json
{
  "success": true,
  "message": "Request successful",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {}
}
```

Paginated response:

```json
{
  "success": true,
  "message": "Data fetched successfully",
  "data": {
    "count": 100,
    "next": "http://localhost/api/venues?page=2",
    "previous": null,
    "results": []
  }
}
```

## 3. Auth Service APIs

## 3.1 Register Customer

```http
POST /api/auth/register/customer
```

Request:

```json
{
  "full_name": "Customer One",
  "email": "customer@example.com",
  "phone": "9876543210",
  "password": "StrongPassword123"
}
```

Response:

```json
{
  "success": true,
  "message": "Customer registered successfully",
  "data": {
    "user_id": "uuid",
    "email": "customer@example.com",
    "role": "CUSTOMER"
  }
}
```

## 3.2 Register Vendor

```http
POST /api/auth/register/vendor
```

Request:

```json
{
  "full_name": "Vendor One",
  "email": "vendor@example.com",
  "phone": "9876543210",
  "password": "StrongPassword123",
  "business_name": "Green Palace Events",
  "business_email": "business@example.com",
  "business_phone": "9876543211"
}
```

Response:

```json
{
  "success": true,
  "message": "Vendor registered successfully. Waiting for admin approval.",
  "data": {
    "user_id": "uuid",
    "vendor_id": "uuid",
    "approval_status": "PENDING"
  }
}
```

## 3.3 Login

```http
POST /api/auth/login
```

Request:

```json
{
  "email": "customer@example.com",
  "password": "StrongPassword123"
}
```

Response:

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token",
    "user": {
      "id": "uuid",
      "email": "customer@example.com",
      "role": "CUSTOMER"
    }
  }
}
```

## 3.4 Get Current User

```http
GET /api/auth/me
```

Response:

```json
{
  "success": true,
  "message": "User fetched successfully",
  "data": {
    "id": "uuid",
    "full_name": "Customer One",
    "email": "customer@example.com",
    "role": "CUSTOMER"
  }
}
```

## 4. Venue Service APIs

## 4.1 Create Venue

```http
POST /api/venues
```

Role:

```text
VENDOR
```

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

Response:

```json
{
  "success": true,
  "message": "Venue created and submitted for approval",
  "data": {
    "id": "uuid",
    "name": "Green Palace Auditorium",
    "approval_status": "PENDING_APPROVAL"
  }
}
```

## 4.2 List Approved Venues

```http
GET /api/venues?city=Calicut&capacity_min=300&price_max=80000&category=auditorium
```

Response:

```json
{
  "success": true,
  "message": "Venues fetched successfully",
  "data": {
    "count": 1,
    "results": [
      {
        "id": "uuid",
        "name": "Green Palace Auditorium",
        "city": "Calicut",
        "capacity": 500,
        "base_price": "75000.00",
        "primary_image": "https://example.com/image.jpg",
        "approval_status": "APPROVED"
      }
    ]
  }
}
```

## 4.3 Get Venue Detail

```http
GET /api/venues/{venue_id}
```

Response:

```json
{
  "success": true,
  "message": "Venue fetched successfully",
  "data": {
    "id": "uuid",
    "name": "Green Palace Auditorium",
    "description": "A premium auditorium for weddings and events.",
    "city": "Calicut",
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
    "images": []
  }
}
```

## 4.4 Approve Venue

```http
PATCH /api/venues/{venue_id}/approval
```

Role:

```text
ADMIN
```

Request:

```json
{
  "approval_status": "APPROVED",
  "reason": null
}
```

Response:

```json
{
  "success": true,
  "message": "Venue approval status updated",
  "data": {
    "id": "uuid",
    "approval_status": "APPROVED"
  }
}
```

## 5. Booking Service APIs

## 5.1 Check Availability

```http
POST /api/bookings/check-availability
```

Request:

```json
{
  "venue_id": "uuid",
  "start_datetime": "2026-06-10T18:00:00+05:30",
  "end_datetime": "2026-06-10T22:00:00+05:30"
}
```

Available response:

```json
{
  "success": true,
  "message": "Venue is available",
  "data": {
    "available": true,
    "conflicts": []
  }
}
```

Unavailable response:

```json
{
  "success": true,
  "message": "Venue is not available",
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

## 5.2 Create Booking Request

```http
POST /api/bookings
```

Role:

```text
CUSTOMER
```

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

Response:

```json
{
  "success": true,
  "message": "Booking request created successfully",
  "data": {
    "id": "uuid",
    "booking_reference": "BMV-20260610-0001",
    "status": "PENDING"
  }
}
```

Conflict response:

```json
{
  "success": false,
  "message": "Selected slot is not available",
  "errors": {
    "time_slot": "This venue already has a booking in the selected time range."
  }
}
```

## 5.3 Vendor Booking Requests

```http
GET /api/bookings/vendor
```

Role:

```text
VENDOR
```

Response:

```json
{
  "success": true,
  "message": "Vendor bookings fetched successfully",
  "data": {
    "results": [
      {
        "id": "uuid",
        "booking_reference": "BMV-20260610-0001",
        "venue_id": "uuid",
        "customer_id": "uuid",
        "start_datetime": "2026-06-10T18:00:00+05:30",
        "end_datetime": "2026-06-10T22:00:00+05:30",
        "status": "PENDING"
      }
    ]
  }
}
```

## 5.4 Accept Booking

```http
PATCH /api/bookings/{booking_id}/accept
```

Role:

```text
VENDOR
```

Response:

```json
{
  "success": true,
  "message": "Booking accepted successfully",
  "data": {
    "id": "uuid",
    "status": "ACCEPTED"
  }
}
```

## 5.5 Reject Booking

```http
PATCH /api/bookings/{booking_id}/reject
```

Role:

```text
VENDOR
```

Request:

```json
{
  "reason": "Venue is not available due to maintenance."
}
```

Response:

```json
{
  "success": true,
  "message": "Booking rejected successfully",
  "data": {
    "id": "uuid",
    "status": "REJECTED"
  }
}
```

## 5.6 Customer Booking History

```http
GET /api/bookings/my-bookings
```

Role:

```text
CUSTOMER
```

## 6. Notification Service APIs

## 6.1 List My Notifications

```http
GET /api/notifications
```

Response:

```json
{
  "success": true,
  "message": "Notifications fetched successfully",
  "data": {
    "results": [
      {
        "id": "uuid",
        "title": "Booking Accepted",
        "message": "Your booking has been accepted.",
        "is_read": false,
        "created_at": "2026-06-10T10:00:00+05:30"
      }
    ]
  }
}
```

## 6.2 Mark Notification as Read

```http
PATCH /api/notifications/{notification_id}/read
```

Response:

```json
{
  "success": true,
  "message": "Notification marked as read",
  "data": {}
}
```

## 7. AI Service APIs

## 7.1 AI Venue Recommendation

```http
POST /api/ai/recommend-venues
```

Request:

```json
{
  "query": "I need a wedding hall in Calicut for 500 people under 80000 with parking.",
  "date": "2026-06-10",
  "start_time": "18:00",
  "end_time": "22:00"
}
```

Response:

```json
{
  "success": true,
  "message": "Recommended venues generated",
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

## 7.2 Venue Policy Question

```http
POST /api/ai/venue-policy-question
```

Request:

```json
{
  "venue_id": "uuid",
  "question": "Is outside catering allowed?"
}
```

Response:

```json
{
  "success": true,
  "message": "Answer generated",
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

## 7.3 Generate Venue Description

```http
POST /api/ai/generate-venue-description
```

Role:

```text
VENDOR
```

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

Response:

```json
{
  "success": true,
  "message": "Description generated successfully",
  "data": {
    "description": "Green Palace Auditorium is a spacious wedding hall in Calicut..."
  }
}
```

## 8. Service Internal APIs

These APIs should not be publicly exposed without protection.

## 8.1 Venue Validation for Booking Service

```http
GET /internal/venues/{venue_id}/booking-validation
```

Response:

```json
{
  "id": "uuid",
  "vendor_id": "uuid",
  "approval_status": "APPROVED",
  "is_active": true,
  "base_price": "75000.00",
  "price_type": "FULL_DAY"
}
```

## 8.2 User Validation

```http
GET /internal/auth/users/{user_id}
```

Response:

```json
{
  "id": "uuid",
  "role": "CUSTOMER",
  "is_active": true
}
```

## 9. Error Status Codes

Use these status codes:

```text
200 OK
201 Created
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
500 Internal Server Error
```

Examples:

```text
401 -> Missing or invalid token
403 -> User role not allowed
404 -> Venue not found
409 -> Booking conflict
422 -> Invalid date/time format
```

## 10. Senior-Level API Rules

1. Every protected endpoint must validate JWT.
2. Every role-specific endpoint must check role.
3. Every vendor action must check ownership.
4. Booking creation must recheck availability.
5. AI responses must not bypass Booking Service validation.
6. List APIs must be paginated.
7. APIs should return consistent response format.
8. Internal APIs should be protected using service token/API key.
