# Authentication System Guide

This guide explains how authentication and session management work in Book My Venue.

## 1. Token Delivery
We use JWTs (JSON Web Tokens) via `djangorestframework-simplejwt`.
For security, tokens are delivered as **HttpOnly cookies**, preventing XSS theft.

- `access_token`: Lives for 15 minutes.
- `refresh_token`: Lives for 7 days.

Tokens are automatically injected into `request.COOKIES` and read by our `CustomJWTCookieAuthentication` class.

## 2. Token Rotation
To prevent replay attacks if a refresh token is compromised, we implement **Token Rotation**:
- Every time the `/api/auth/refresh/` endpoint is called, a brand new `access_token` and `refresh_token` pair is generated.
- The **old refresh token is immediately blacklisted**.
- If someone tries to use a blacklisted refresh token, the request is rejected.
- **Race Condition Prevention:** To prevent simultaneous concurrent refresh requests from failing (which happens frequently in React apps), we securely cache the newly generated token pair in Redis for **5 seconds**, keyed by a hash of the old refresh token. If a concurrent request arrives with the same old refresh token within that 5-second window, it seamlessly receives the exact same cached tokens.

## 3. Account Lockout (Brute-Force Protection)
To protect against brute-force password guessing, we track failed login attempts in **Redis**:
- If a user fails to log in 5 times consecutively, their account is locked.
- The lockout duration is 15 minutes.
- Successful logins clear the failed attempt counter.
- *Implementation detail:* `apps.accounts.core.lockout.LockoutManager`

## 4. Session Termination (Logout)
Because JWTs are stateless, we use the `token_blacklist` app to invalidate them.

- **Standard Logout**: The specific refresh token used in the session is added to the blacklist. The cookies are deleted from the client browser.
- **Logout All Devices**: We perform two critical actions:
  1. We bulk-insert all of the user's `OutstandingToken` records into the `BlacklistedToken` table.
  2. **Global Revocation Timestamp**: We write the current Unix timestamp to Redis (`jwt:revoke:<user_id>`). Our `CustomJWTCookieAuthentication` class intercepts all Access Tokens and rejects them if their issued-at (`iat`) claim is older than this timestamp. This provides **instant Access Token revocation**.

## 5. Password Management
When a user changes their password (via `/api/auth/change-password/`) or completes a password reset (via `/api/auth/reset-password/`), we enforce security by **instantly terminating all of their active sessions**. We perform the "Logout All Devices" operation (including setting the Redis Epoch) as part of the transaction.

### Forgot Password Flow
- Initiated via `/api/auth/forgot-password/`. Fails silently for non-existent emails to prevent **Email Enumeration**.
- Generates a 6-digit OTP stored in Redis (15-minute TTL).
- Sent asynchronously via Celery (`accounts.send_password_reset_email`).

## 6. OTP Verification
Newly registered users cannot log in immediately. They must verify their email.
- A 6-digit OTP is generated and stored in Redis with a 5-minute TTL.
- **Asynchronous Delivery**: The email is pushed to a background queue (Celery) to prevent blocking the API request. The `send_otp_email_task` handles SMTP delivery and includes automatic retries (up to 3 times) if the SMTP server flakes out.
- The user submits the OTP to `/api/auth/verify-otp/`.
- Once verified, `user.is_verified` is set to `True`, allowing them to log in.

## 7. Additional Security Mitigations
- **Email Enumeration Prevention**: The `/api/auth/resend-otp/` and `/api/auth/forgot-password/` endpoints strictly return a generic `200 OK` regardless of whether the email exists. This prevents attackers from guessing registered users.
- **OTP Pumping Prevention**: OTP endpoints use dedicated DRF throttle scopes (`resend_otp`: 3/minute) to prevent attackers from rapidly requesting OTPs and draining company AWS SES / Twilio credits.
- **Ghost User Garbage Collection**: A Celery beat task (`delete_unverified_ghost_users`) runs daily at Midnight UTC to permanently delete any user accounts that are `is_verified=False` and older than **24 hours**. This prevents the database from bloating with unusable, unverified email addresses.
- **Fast Test Execution**: For testing, we completely swap Redis for Django's `LocMemCache` and disable the `django-silk` profiler in `tests/conftest.py` to prevent database deadlocks and network timeouts, keeping test execution under 3 seconds.
