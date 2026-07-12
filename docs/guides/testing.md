# Testing Strategy & Guidelines

This guide covers how testing is structured and executed across all microservices in Book My Venue. We follow a strict Testing Pyramid combined with a dedicated Security testing layer.

## 1. Test Suite Organization

Tests in Book My Venue are split into two distinct categories: **Microservice Tests** (Unit/Integration) and **Global Infrastructure Tests** (Load/E2E).

### 1.1 Microservice Tests (Isolated)
Located in the `tests/` directory of *each individual service* (e.g., `services/auth-service/tests/`). These test the backend logic using `pytest`:

```text
tests/
├── conftest.py             # Global test fixtures (cache clearing, silk disabling, etc.)
├── unit/                   # Unit Tests (Fast, Isolated)
├── integration/            # Integration Tests (API + DB + Serializers)
└── security/               # Security Tests (OWASP, Lockouts, Cookie Flags)
```

### 1.2 Global Infrastructure Tests (End-to-End & Load)
Located in the **root** `tests/` directory of the entire repository. These test the platform as a whole (Nginx Gateway, Docker network, databases, caching, and cross-service communication):

```text
Book My Venue/
└── tests/
    ├── load/               # Locust load testing scripts (e.g., locustfile.py)
    └── e2e/                # Playwright / Cypress UI tests (Phase 2+)
```

## 2. Running Tests

We use `uv` for fast package management and environment isolation. By default, `pytest-django` automatically provisions a dedicated test database (e.g., `test_auth_db`).

To avoid rebuilding the test database from scratch every time (which runs all migrations), always use the `--reuse-db` flag locally.

### Run All Tests
```bash
uv run pytest --reuse-db
```

### Run by Layer
```bash
# Fastest — Tests core domain logic in isolation
uv run pytest -m unit --reuse-db

# Tests full HTTP request/response pipeline and DB writes
uv run pytest -m integration --reuse-db

# Tests brute-force, token blacklists, and enumeration defenses
uv run pytest -m security --reuse-db
```

### Run Specific Tests
```bash
# Run a specific file
uv run pytest tests/security/test_auth_security.py --reuse-db

# Run a specific test class
uv run pytest tests/unit/accounts/test_otp_service.py::TestVerifyOTP --reuse-db

# Run a specific test method with verbose output and short tracebacks
uv run pytest tests/unit/accounts/test_lockout.py::TestAccountLockoutTracker::test_locked_at_threshold -v --tb=short
```

## 3. Testing Optimizations

Our test environment is heavily optimized to run in **under 3 seconds** despite having nearly 100 tests.

1. **Local Memory Cache**: We completely bypass the Redis dependency during testing. In `tests/conftest.py`, the `CACHES` setting is overridden to use Django's `LocMemCache`. This prevents massive 5-second socket timeouts on every test if a local Redis Docker container is not running.
2. **Disabling Profilers**: Tools like `django-silk` log every SQL query and HTTP request. If enabled during tests, they cause severe database deadlocks and slow down execution by 1000%. We dynamically strip `silk` from `MIDDLEWARE` and `INSTALLED_APPS` in `tests/conftest.py`.
3. **Database Transactions**: `pytest-django` wraps every individual test in an atomic database transaction that is rolled back immediately after the test completes. This guarantees perfectly clean state between tests without needing to run `TRUNCATE` or `DELETE` statements.

## 4. Writing Tests

### Fixtures
Always define test data in `conftest.py` using fixtures. Avoid global variables.
Example: `verified_user`, `api_client`.

### Assertions
Keep assertions clean. Test the happy path, the failure path (e.g., `pytest.raises`), and edge cases (e.g., case-insensitive emails).

### Isolation
Never mock the database in integration tests. Let it hit the actual test PostgreSQL database. Only mock external dependencies like:
- AWS SES / Twilio (Celery tasks like `send_otp_email_task.delay`)
- External microservice HTTP calls (using `responses` or `unittest.mock`)

### Testing Celery Tasks & `transaction.on_commit`
Because we heavily use `transaction.on_commit` to delay Celery task execution (e.g., `dispatch_tenant_provisioning`) until the database transaction is fully committed, standard mock assertions (`mock_task.delay.assert_called_once()`) will fail during tests. This happens because `pytest-django` wraps tests in a transaction that is never actually committed.

To properly test these tasks, you must mock `transaction.on_commit` to execute instantly:
```python
@patch('django.db.transaction.on_commit')
def test_vendor_registration_triggers_provisioning(mock_on_commit, api_client):
    # Make on_commit execute the lambda immediately during the test
    mock_on_commit.side_effect = lambda f: f()
    # ... fire request ...
    mock_provisioning_task.delay.assert_called_once()
```
