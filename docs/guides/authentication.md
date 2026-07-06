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

## 3. Account Lockout (Brute-Force Protection)
To protect against brute-force password guessing, we track failed login attempts in **Redis**:
- If a user fails to log in 5 times consecutively, their account is locked.
- The lockout duration is 15 minutes.
- Successful logins clear the failed attempt counter.
- *Implementation detail:* `apps.accounts.core.lockout.LockoutManager`

## 4. Session Termination (Logout)
Because JWTs are stateless, we use the `token_blacklist` app to invalidate them.

- **Standard Logout**: The specific refresh token used in the session is added to the blacklist. The cookies are deleted from the client browser.
- **Logout All Devices**: We query the `OutstandingToken` table for *all* tokens associated with the user and bulk-insert them into the `BlacklistedToken` table.

## 5. Password Changes
When a user changes their password, we enforce security by instantly terminating all of their active sessions. We perform a "Logout All Devices" operation as part of the password change transaction.

## 6. OTP Verification
Newly registered users cannot log in immediately. They must verify their email.
- A 6-digit OTP is generated and stored in Redis with a 5-minute TTL.
- **Asynchronous Delivery**: The email is pushed to a background queue (Celery) to prevent blocking the API request. The `send_otp_email_task` handles SMTP delivery and includes automatic retries (up to 3 times) if the SMTP server flakes out.
- The user submits the OTP to `/api/auth/verify-otp/`.
- Once verified, `user.is_verified` is set to `True`, allowing them to log in.
