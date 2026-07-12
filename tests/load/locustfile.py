from locust import HttpUser, between, task


class BookMyVenueUser(HttpUser):
    # Wait between 1 to 2 seconds between simulated user actions
    wait_time = between(1, 2)

    @task(3)
    def shallow_health_check(self):
        # 1. Tests Nginx -> Gunicorn routing without touching the DB
        # This proves the API Gateway can handle massive concurrent throughput
        self.client.get("/health/")

    @task(2)
    def invalid_login(self):
        # 2. Tests Nginx -> Gunicorn -> Django ORM -> PostgreSQL read performance
        # We use fake credentials to ensure we DON'T write to or pollute the Dev DB
        self.client.post(
            "/api/auth/login/", json={"email": "loadtest_fake_user@example.com", "password": "wrongpassword123"}
        )

    @task(1)
    def unauthenticated_profile(self):
        # 3. Tests the JWT Cookie Authentication Middleware
        # Expects a 401 Unauthorized since we aren't passing a token
        self.client.get("/api/auth/me/")
