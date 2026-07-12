# Local Development Guide

Book My Venue relies on a microservices architecture. Running every service inside Docker continuously requires significant RAM (16GB+ recommended).

To ensure the platform can be developed on 8GB RAM machines comfortably, we utilize **Docker Compose Profiles** and **Native Django Execution**.

## Prerequisites
*   Docker Desktop (Windows/Mac) or Docker Engine (Linux).
*   If on Windows, ensure your `.wslconfig` limits Docker memory to 2.5GB to prevent system freezes.
*   Python 3.12+ installed locally.

## Code Quality & Pre-commit
We use `pre-commit` with `ruff` to automatically lint and format code before it is committed.
If you haven't already, install it globally:
```powershell
uv pip install pre-commit ruff --system
pre-commit install
```
Any time you run `git commit`, `ruff` will automatically format your code. If it catches logical errors it cannot auto-fix, the commit will be blocked until you fix them.

## The `dev.ps1` Helper
On Windows, use the `dev.ps1` script located in the project root to control the environment.

### Workflow A: Native Development (Recommended)
This workflow uses ~500MB of RAM. It runs the heavy infrastructure (Redis, Gateway) in Docker, but runs the Django APIs natively on your host machine.

1.  **Start Infrastructure**
    ```powershell
    .\dev.ps1 infra
    ```
    This starts Redis (and the API Gateway).

2.  **Run Django Natively**
    Open a new terminal, activate your virtual environment, and run the service you are working on:
    ```powershell
    cd services\venue-service
    uv run python manage.py runserver 8002
    ```
    You can now hit the API directly at `http://localhost:8002`.

### Workflow B: Full Containerization (Testing & Integration)
This workflow uses ~1.5GB to 2.5GB of RAM. Use this when you need to test the interaction between multiple services (e.g. Auth Service calling Venue Service through the Gateway).

1.  **Start Specific Services**
    ```powershell
    .\dev.ps1 auth    # Starts auth-service
    .\dev.ps1 venue   # Starts venue-service
    .\dev.ps1 booking # Starts booking-service
    ```
    *(Note: You can run these commands consecutively, they will incrementally add containers to the running network)*

2.  **Start Background Workers (Optional)**
    Do not run Celery workers unless you are actively debugging asynchronous tasks (like email sending or Outbox event publishing).
    ```powershell
    .\dev.ps1 workers
    ```

3.  **Stop Everything**
    ```powershell
    .\dev.ps1 down
    ```

## Docker Compose Profiles Explained
Under the hood, `dev.ps1` uses Docker Compose Profiles. If you are on Mac/Linux, you can run the commands directly:

```bash
docker compose --profile auth --profile venue up -d
docker compose --profile workers up -d
docker compose --profile auth --profile venue down
```
Services without a profile (like `redis`) will always start automatically.
