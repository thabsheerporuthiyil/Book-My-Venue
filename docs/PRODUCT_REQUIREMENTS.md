# PRODUCT_REQUIREMENTS.md

# Book My Venue — Product Requirements Document

## 1. Product Overview

**Book My Venue** is a SaaS-enabled venue booking platform where customers can search, compare, and book venues such as auditoriums, wedding halls, conference halls, event spaces, party halls, and turfs.

Venue owners can register as vendors, list their venues, manage availability, handle booking requests, update pricing, upload images, define policies, and view business insights from a vendor dashboard.

The platform is designed using a microservices architecture with a separate AI service for RAG-based assistance and agentic AI workflows.

## 2. Product Vision

To build a scalable, production-ready venue booking marketplace that helps:

- Customers find and book suitable venues easily.
- Venue owners manage bookings and availability digitally.
- Admins control platform quality, approvals, and operations.
- AI assist users, vendors, and admins with search, recommendations, policy Q&A, and insights.

## 3. Target Users

### 3.1 Customer

A customer is a person who wants to book a venue for an event.

Customer can:

- Register and login
- Search venues
- Filter by location, category, price, capacity, amenities, and availability
- View venue details
- Ask AI questions about venue policies
- Request a booking
- Track booking status
- Cancel booking based on rules
- Add reviews after completed bookings

### 3.2 Vendor / Venue Owner

A vendor owns or manages one or more venues.

Vendor can:

- Register and login
- Create venue listings
- Upload venue images
- Add venue description, capacity, price, amenities, and policies
- Manage availability
- View booking requests
- Accept or reject bookings
- View booking history
- View business insights
- Use AI to generate descriptions or understand performance

### 3.3 Admin

Admin manages platform operations.

Admin can:

- Approve or reject vendors
- Approve or reject venues
- Suspend users or venues
- Manage categories and amenities
- View bookings
- Handle complaints
- Monitor platform activity
- Use AI to summarize reports and detect unusual activity

## 4. MVP Scope

The first version should focus only on the core booking marketplace.

### MVP Features

#### Authentication

- Customer registration
- Vendor registration
- Login
- JWT authentication
- Refresh token
- Role-based access control

#### Venue Management

- Vendor can create venue
- Vendor can update own venue
- Vendor can upload venue images
- Vendor can add amenities
- Vendor can add policies
- Admin can approve/reject venue
- Customer can see only approved venues

#### Search and Discovery

- List approved venues
- Search by keyword
- Filter by city/location
- Filter by venue category
- Filter by capacity
- Filter by price range
- Filter by amenities

#### Booking

- Customer can check availability
- Customer can create booking request
- System must prevent double booking
- Vendor can accept or reject booking
- Customer can view booking status
- Vendor can view booking requests

#### Notifications

- Booking request notification to vendor
- Booking accepted/rejected notification to customer
- Venue approval notification to vendor

#### Admin

- Admin can view users
- Admin can approve vendors
- Admin can approve venues
- Admin can suspend venue

## 5. Future Scope

After the MVP is stable, add:

- Payment gateway
- Refund management
- Vendor subscription plans
- SaaS billing
- Reviews and ratings
- Advanced analytics
- Calendar view
- AI venue recommendation
- RAG-based venue policy Q&A
- Agentic AI booking assistant
- WhatsApp/SMS notifications
- Multi-location support
- Team members for vendor accounts

## 6. Core Business Rules

1. Only approved venues should be visible to customers.
2. A vendor can manage only their own venues.
3. A customer cannot create/update venues.
4. A vendor cannot access another vendor’s booking data.
5. Admin can approve, reject, suspend, or restore venues.
6. A booking cannot overlap with an existing confirmed/accepted booking.
7. Availability must be checked in the backend before booking creation.
8. AI can recommend venues, but cannot confirm bookings directly.
9. Booking Service is the final source of truth for availability.
10. Notifications should not block booking creation.
11. Venue deletion should not be allowed if future accepted bookings exist.
12. A booking status should follow a valid state transition.

## 7. Booking Statuses

Initial statuses:

- `PENDING`
- `ACCEPTED`
- `REJECTED`
- `CANCELLED`
- `EXPIRED`
- `COMPLETED`

Future payment-related statuses:

- `PAYMENT_PENDING`
- `PAID`
- `PAYMENT_FAILED`
- `REFUNDED`

## 8. Booking State Transitions

Allowed transitions:

```text
PENDING -> ACCEPTED
PENDING -> REJECTED
PENDING -> CANCELLED
PENDING -> EXPIRED

ACCEPTED -> COMPLETED
ACCEPTED -> CANCELLED

REJECTED -> final
CANCELLED -> final
EXPIRED -> final
COMPLETED -> final
```

## 9. Non-Functional Requirements

### Security

- JWT-based authentication
- Role-based authorization
- Service-to-service authentication
- Input validation
- Secure file upload
- Environment variables for secrets
- No hardcoded credentials

### Scalability

- Microservice boundaries
- Separate database ownership per service
- API Gateway
- Async notifications
- Caching for read-heavy APIs
- Pagination for list APIs
- Database indexes on frequently queried fields

### Reliability

- Booking conflict prevention
- Database transactions for booking creation
- Idempotent event handling
- Retry support for background jobs
- Structured logging
- Error tracking later

### Performance

- Paginated venue listing
- Indexed search fields
- Optimized queries
- Cached venue details later
- Async image upload processing later

### Maintainability

- Clear service boundaries
- API contracts
- Separate settings for dev/staging/prod
- Dockerized services
- Clean documentation
- Tests for critical business logic

## 10. Success Criteria for MVP

The MVP is successful when:

- Customer can register/login.
- Vendor can register/login.
- Vendor can create venue.
- Admin can approve venue.
- Customer can search approved venues.
- Customer can request booking.
- System prevents overlapping bookings.
- Vendor can accept/reject booking.
- Notifications are triggered asynchronously.
