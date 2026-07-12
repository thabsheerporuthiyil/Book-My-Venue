# Book My Venue

Book My Venue is a **multi-tenant SaaS venue booking platform** built with a **microservices architecture**.

The platform allows customers to search and book venues, while venue owners can manage venues, availability, booking requests, pricing, and business operations.

---

## Services

```text
auth-service          Authentication, users, roles, tenants, multi-tenancy (Port 8001)
venue-service         Venues, images, amenities, policies, categories (Port 8002)
booking-service       Availability, bookings, conflict prevention (Port 8003)
notification-service  Emails and in-app notifications via Celery (Port 8004)
ai-service            RAG, embeddings, agentic AI features (Port 8005)
```

---

## Tech Stack

### Frontend
- React + JavaScript
- Tailwind CSS

### Backend
- Django REST Framework (auth, venue, booking, notification services)
- FastAPI (ai-service)
- djangorestframework-simplejwt — JWT authentication with HttpOnly cookies
- Row-Level Multi-Tenancy — isolated data per tenant
- drf-spectacular — OpenAPI / Swagger documentation
- dj-database-url — DATABASE_URL parsing
- python-decouple — environment variable management

### Infrastructure
- PostgreSQL (one database per service)
- Redis (caching, Celery broker)
- Celery (background task processing)
- Docker + Docker Compose
- Nginx API Gateway

### Dev Tooling
- Ruff — linting + formatting (replaces flake8, isort, black)
- pre-commit — enforces Ruff on every git commit
- django-silk — SQL query profiler (dev only)
- uv — fast Python package manager

### Cloud / Storage
- Cloudinary — venue image storage
- Neon — managed PostgreSQL (development)
- OpenAI / Google Gemini — AI/LLM integration

---

## Project Structure

```text
Book My Venue/
├── docs/               Architecture, PRD, API contracts, DB design, user flows
├── frontend/web/       React frontend application
├── gateway/nginx/      Nginx reverse proxy + API gateway config
├── infrastructure/     Scripts, deployment configs
├── shared/
│   ├── python/         Shared Python utilities (base models, exceptions, response builders)
│   └── javascript/     Shared JS utilities and API clients
└── services/
    ├── auth-service/
    ├── venue-service/
    ├── booking-service/
    ├── notification-service/
    └── ai-service/
```

---

## Documentation

| Doc | Description |
|-----|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, service boundaries, patterns |
| [PRODUCT_REQUIREMENTS.md](docs/PRODUCT_REQUIREMENTS.md) | PRD, user types, features, business rules |
| [DATABASE_DESIGN.md](docs/DATABASE_DESIGN.md) | All database tables, fields, indexes, constraints |
| [API_CONTRACTS.md](docs/API_CONTRACTS.md) | Full API reference for all services |
| [USER_FLOWS.md](docs/USER_FLOWS.md) | End-to-end user and system flows |
