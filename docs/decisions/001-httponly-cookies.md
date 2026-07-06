# ADR 001: HttpOnly Cookies for JWT Authentication

**Date:** July 2026
**Status:** Accepted

## Context
Originally, the platform used standard JWT authentication where the client (frontend) was responsible for storing the `access_token` and `refresh_token` (typically in `localStorage`) and attaching the `Authorization: Bearer <token>` header to every API request.

Storing JWTs in `localStorage` exposes them to **Cross-Site Scripting (XSS)** attacks. If a malicious script runs on the page, it can read `localStorage` and exfiltrate the tokens, granting the attacker full access to the user's account.

## Decision
We migrated the authentication system to use **HttpOnly Cookies**.

1. When a user logs in, the `access_token` and `refresh_token` are set as `HttpOnly`, `Secure`, and `SameSite=Lax` cookies on the HTTP response.
2. The browser automatically attaches these cookies to every subsequent request to the API domain.
3. JavaScript running in the browser cannot read `HttpOnly` cookies, completely neutralizing XSS token theft.

## Consequences
### Positive
- Tokens are immune to XSS attacks.
- Frontend code is simplified (no need to manually manage or attach tokens).
- Stronger alignment with enterprise security standards.

### Negative
- We must handle CSRF (Cross-Site Request Forgery) protection carefully, as browsers send cookies automatically. We mitigate this using `SameSite=Lax` on the cookies.
- Mobile apps (iOS/Android) and internal service-to-service calls that do not have a cookie jar must fall back to the `Authorization: Bearer` header. Our `CustomJWTCookieAuthentication` class explicitly supports this fallback.
