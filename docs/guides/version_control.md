# Version Control & CI/CD Pipeline

Book My Venue follows **Trunk-Based Development** rather than the traditional GitFlow. This ensures rapid integration, minimizes merge conflicts, and maintains a deployment-ready main branch at all times.

## Trunk-Based Development

In this repository, `main` is the only long-lived branch. It is heavily protected and represents the "source of truth."

### The Workflow

1. **Create a Feature Branch:** Always branch off `main` for your work.
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```
2. **Commit Often:** Commit small, logical chunks of work. Our `pre-commit` hooks will run automatically to enforce code quality before the commit is created.
3. **Open a Pull Request:** Push your feature branch and open a PR against `main`.
4. **CI Pipeline Validation:** GitHub Actions will automatically trigger. It runs our Ruff linters and all Pytest suites (for both Venue and Auth services) against your PR.
5. **Merge:** Once CI is green and your PR is approved, it is merged into `main`.

> **Note:** Never commit directly to `main`. Branch protection rules require all code to pass CI via a Pull Request.

## Continuous Integration (GitHub Actions)

Our CI pipeline is defined in `.github/workflows/ci.yml`. It ensures that broken code never reaches production.

### Pipeline Stages
1. **Code Quality (Ruff):** Validates that all Python files adhere to our strict formatting and linting rules.
2. **Venue Service Tests:** Spins up an in-memory SQLite database and local Redis instance to run the entire Venue Service test suite (`pytest`).
3. **Auth Service Tests:** Spins up the Auth Service environment and runs its `pytest` suite.

Because we use `uv` and fast dependencies, the entire CI pipeline typically completes in under 60 seconds.
