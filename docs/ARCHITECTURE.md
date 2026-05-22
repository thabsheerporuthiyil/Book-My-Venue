# ARCHITECTURE.md

# Book My Venue — System Architecture

## 1. Architecture Goal

Book My Venue is designed as a scalable microservices-based SaaS platform.

The architecture should support:

- Independent service boundaries
- Independent data ownership
- API Gateway routing
- Secure authentication
- Async communication for side effects
- AI service separation
- Future payment and subscription services
- Production-ready deployment

## 2. High-Level Architecture

```text
React Frontend
      |
      v
API Gateway / Nginx
      |
      |---------------- Auth Service
      |---------------- Venue Service
      |---------------- Booking Service
      |---------------- Notification Service
      |---------------- AI Service
      |
PostgreSQL / Redis / Vector DB / Object Storage
```

## 3. Services

## 3.1 Auth Service

### Responsibility

Auth Service manages identity and access.

It owns:

- Users
- Roles
- Authentication
- JWT generation
- Refresh tokens
- Basic user profiles

### Main Features

- Register customer
- Register vendor
- Login
- Refresh token
- Get current user
- Role management

### Owned Data

- User
- Role
- RefreshToken
- VendorProfile basic status
- CustomerProfile basic data

### Technology

- Django REST Framework
- PostgreSQL

## 3.2 Venue Service

### Responsibility

Venue Service manages all venue-related data.

It owns:

- Venues
- Venue images
- Amenities
- Categories
- Venue policies
- Venue approval status

### Main Features

- Create venue
- Update venue
- Upload images
- Add amenities
- Add policies
- Admin approval
- Public venue listing
- Venue detail

### Owned Data

- Venue
- VenueImage
- VenueCategory
- Amenity
- VenueAmenity
- VenuePolicy

### Technology

- Django REST Framework
- PostgreSQL
- Cloudinary/S3 for images

## 3.3 Booking Service

### Responsibility

Booking Service manages bookings and availability.

It owns:

- Booking requests
- Booking status
- Availability rules
- Blocked slots
- Conflict prevention
- Booking status history

### Main Features

- Check availability
- Create booking request
- Prevent double booking
- Vendor accept/reject booking
- Customer cancel booking
- Booking history

### Owned Data

- Booking
- AvailabilityRule
- BlockedSlot
- BookingStatusHistory

### Technology

- Django REST Framework
- PostgreSQL

### Important Rule

Booking Service is the final source of truth for availability.

## 3.4 Notification Service

### Responsibility

Notification Service handles asynchronous communication.

It owns:

- Notifications
- Email logs
- Notification templates
- Delivery status

### Main Features

- Booking request notification
- Booking accepted/rejected notification
- Venue approval notification
- Reminder notification later

### Owned Data

- Notification
- NotificationTemplate
- EmailLog

### Technology

- Django or FastAPI
- Celery
- Redis
- PostgreSQL

## 3.5 AI Service

### Responsibility

AI Service manages RAG and agentic AI features.

It owns:

- AI conversations
- Messages
- Embeddings
- Document chunks
- AI tool calls
- RAG pipeline

### Main Features

- AI venue recommendation
- Venue policy Q&A
- Venue description generator
- AI booking assistant
- Vendor insights later
- Admin summary assistant later

### Owned Data

- KnowledgeDocument
- DocumentChunk
- EmbeddingRecord
- AIConversation
- AIMessage
- AIToolCall

### Technology

- FastAPI
- LangChain or LlamaIndex
- pgvector/Qdrant/Chroma
- PostgreSQL
- LLM provider

## 4. API Gateway

Use Nginx as the first API Gateway.

Example routes:

```text
/api/auth/*        -> auth-service
/api/venues/*      -> venue-service
/api/bookings/*    -> booking-service
/api/notifications/* -> notification-service
/api/ai/*          -> ai-service
```

Benefits:

- One base API URL for frontend
- Central routing
- Easier local development
- Easier production deployment

## 5. Communication Patterns

## 5.1 Synchronous Communication

Used when immediate result is required.

Examples:

```text
Booking Service -> Venue Service
Check if venue exists and is approved.

AI Service -> Venue Service
Search venues for recommendation.

AI Service -> Booking Service
Check availability before suggesting booking.
```

Recommended protocol:

```text
HTTP REST APIs
```

## 5.2 Asynchronous Communication

Used for side effects and background jobs.

Examples:

```text
BookingCreated -> Notification Service
BookingAccepted -> Notification Service
VenueApproved -> Notification Service
```

Initial tool:

```text
Redis + Celery
```

Future options:

```text
RabbitMQ
Kafka
NATS
```

## 6. Authentication Flow

```text
1. User logs in through Auth Service.
2. Auth Service returns JWT.
3. Frontend stores token.
4. Frontend sends token in Authorization header.
5. API Gateway forwards request.
6. Each service validates JWT.
7. Service checks role/permission before action.
```

Header:

```http
Authorization: Bearer <access_token>
```

## 7. Service-to-Service Security

Services should not blindly trust each other.

Use:

- Internal API key
- Service token
- JWT validation
- Network-level restrictions later
- Separate internal routes where needed

## 8. Data Ownership Rule

Each service owns its own database tables.

Other services should not directly write another service's database.

Example:

```text
Venue Service owns venue data.
Booking Service stores venue_id but does not edit venue table.
AI Service can retrieve allowed data through APIs or controlled sync jobs.
```

## 9. Database Strategy

Recommended for learning and production-style design:

```text
auth_db
venue_db
booking_db
notification_db
ai_db
```

Each service connects only to its own database.

## 10. AI Architecture

```text
Frontend
   |
Django/Core API or API Gateway
   |
FastAPI AI Service
   |
Retriever / Tools / LLM
   |
Vector DB + Service APIs
```

AI can call tools such as:

- Search venues
- Get venue details
- Check availability
- Retrieve policy chunks
- Generate description

Important:

```text
AI should not confirm bookings directly.
Booking Service must verify all real booking actions.
```

## 11. Booking Reliability

Booking creation must be protected against race conditions.

Rules:

- Check conflict inside database transaction.
- Lock relevant records or use database constraints where possible.
- Never trust frontend availability result.
- Recheck availability before accepting booking.
- Store status history.

Conflict condition:

```text
existing_start < new_end
AND
existing_end > new_start
```

## 12. Deployment Architecture for Development

Use Docker Compose:

```text
frontend
gateway
auth-service
venue-service
booking-service
notification-service
ai-service
auth-db
venue-db
booking-db
notification-db
ai-db
redis
vector-db
```

## 13. Production Considerations

Later production setup:

- Docker images for each service
- Nginx reverse proxy
- Managed PostgreSQL
- Managed Redis
- S3/Cloudinary
- CI/CD using GitHub Actions
- Centralized logging
- Error monitoring
- HTTPS
- Environment-based settings
- Health check endpoints

## 14. Health Check Endpoints

Each service should expose:

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "venue-service"
}
```

## 15. Failure Handling

### AI Service Down

Core booking should continue working.

### Notification Service Down

Booking should succeed; notification should retry.

### Venue Service Down

Booking creation may fail because venue validation is required.

### Booking Service Down

Booking-related actions should be unavailable, but venue browsing can still work.

## 16. Senior-Level Architecture Rule

Start with the minimum useful services:

```text
Auth Service
Venue Service
Booking Service
Notification Service
AI Service
```

Do not create Payment, Analytics, Review, and Subscription services until the core system is stable.
