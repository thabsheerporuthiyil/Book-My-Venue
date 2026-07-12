"""
Unit tests for apps.accounts.core.services.registration

Tests customer and vendor registration business logic.
"""

import pytest
from apps.accounts.core.exceptions import UserAlreadyExistsError
from apps.accounts.core.models import CustomerProfile
from apps.accounts.core.services.registration import register_customer
from apps.accounts.models import User

pytestmark = pytest.mark.unit


class TestRegisterCustomer:
    def test_creates_user_with_correct_fields(self, db):
        user = register_customer(
            email="new@test.com",
            full_name="New Customer",
            password="StrongPass123!",
            phone="1234567890",
        )

        assert user.email == "new@test.com"
        assert user.full_name == "New Customer"
        assert user.phone == "1234567890"
        assert user.check_password("StrongPass123!")
        assert user.global_role == "USER"

    def test_creates_customer_profile(self, db):
        user = register_customer(
            email="profile@test.com",
            full_name="Profile User",
            password="StrongPass123!",
        )

        assert CustomerProfile.objects.filter(user=user).exists()

    def test_email_is_normalized(self, db):
        user = register_customer(
            email="  UPPER@TEST.COM  ",
            full_name="Upper Case",
            password="StrongPass123!",
        )

        assert user.email == "upper@test.com"

    def test_duplicate_email_raises_error(self, db):
        register_customer(
            email="dupe@test.com",
            full_name="First User",
            password="StrongPass123!",
        )

        with pytest.raises(UserAlreadyExistsError):
            register_customer(
                email="dupe@test.com",
                full_name="Second User",
                password="AnotherPass123!",
            )

    def test_is_atomic_on_failure(self, db, mocker):
        """If CustomerProfile creation fails, the User should NOT be saved."""
        mocker.patch(
            "apps.accounts.core.services.registration.CustomerProfile.objects.create",
            side_effect=Exception("DB error"),
        )

        with pytest.raises(Exception, match="DB error"):
            register_customer(
                email="atomic@test.com",
                full_name="Atomic Test",
                password="StrongPass123!",
            )

        assert not User.objects.filter(email="atomic@test.com").exists()
