# Book My Venue Documentation

Welcome to the documentation for Book My Venue. This folder contains all the technical details, architecture decisions, and operational guides required to understand, maintain, and scale the platform.

If you are returning to this project after a long time, start here.

## 📁 Structure

This documentation is organized into an industry-standard format:

- **Root Files**: High-level overviews of the system.
- **`decisions/`**: Architecture Decision Records (ADRs). These explain *why* we built things a certain way (e.g., why we use HttpOnly cookies instead of localStorage).
- **`guides/`**: Deep dives into complex systems and features (e.g., how our row-level multi-tenancy works).
- **`runbooks/`**: Step-by-step instructions for operational tasks (e.g., how to provision a new service for a tenant).

---

## 📚 Core Documents

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)**: The big picture. Explains the microservices, bounded contexts, tech stack, and senior-level design principles. Read this to understand how all the pieces fit together.
2. **[DATABASE_DESIGN.md](./DATABASE_DESIGN.md)**: Defines the table schemas, indexes, and constraints for the entire platform.
3. **[API_CONTRACTS.md](./API_CONTRACTS.md)**: Complete request/response payload examples for every endpoint.
4. **[USER_FLOWS.md](./USER_FLOWS.md)**: Visualizes the step-by-step logic for complex operations (e.g., Registration, Login, Token Refresh).
5. **[PRODUCT_REQUIREMENTS.md](./PRODUCT_REQUIREMENTS.md)**: The PRD. Defines the user types, tenant models, and business requirements.

---

## 🏗️ Decisions (ADRs)

Read these to understand the reasoning behind major architectural shifts.

- **[001: HttpOnly Cookies for JWTs](./decisions/001-httponly-cookies.md)** - Why we migrated away from `Authorization: Bearer` headers.
- **[002: Row-Level Tenancy](./decisions/002-row-level-tenancy.md)** - Why we migrated away from `django-tenants` (schema-per-tenant) to a shared schema architecture.

---

## 📖 Feature Guides

Deep dives into how specific parts of the system are implemented.

- **[Authentication System](./guides/authentication.md)** - Covers OTP verification, account lockout, and token rotation.
- **[Multi-Tenancy](./guides/multi_tenancy.md)** - How tenant isolation is achieved using Row-Level Tenancy.

---

### [Operational Guides](./guides/)
Operational procedures for managing the platform.
1. **[local_development.md](./guides/local_development.md)**: Strategies for running the microservices locally with low RAM using Docker Compose Profiles.
2. **[multi_tenancy.md](./guides/multi_tenancy.md)**: How vendor environments are provisioned.
3. **[authentication.md](./guides/authentication.md)**: How the Nginx Gateway verifies JWTs.
4. **[testing.md](./guides/testing.md)**: Overview of integration testing.
5. **[version_control.md](./guides/version_control.md)**: Details our Trunk-Based Development and CI/CD workflow.

---

## 🛠️ Runbooks

Operational procedures for managing the platform.

- **[Service Provisioning](./runbooks/provisioning.md)** - How the ServiceRegistry and TenantServiceProvision models work to enable features for vendors.
