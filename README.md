# Book My Venue

Book My Venue is a SaaS-enabled venue booking platform built with a microservices architecture.

The platform allows customers to search and book venues, while venue owners can manage venues, availability, booking requests, pricing, and business operations.

## Tech Stack

### Frontend
- React
- JavaScript
- Tailwind CSS

### Backend
- Django REST Framework
- FastAPI for AI service

### Infrastructure
- PostgreSQL
- Redis
- Celery
- Docker
- Nginx API Gateway

## Services

```text
auth-service          Authentication, users, roles
venue-service         Venues, images, amenities, policies
booking-service       Availability, bookings, conflict prevention
notification-service  Emails and notifications
ai-service            RAG and Agentic AI features