from datetime import timedelta

import pytest
from apps.accounts.models import User
from apps.accounts.tasks import delete_unverified_ghost_users
from django.utils import timezone

pytestmark = pytest.mark.django_db


class TestGarbageCollection:
    def test_delete_unverified_ghost_users(self):
        now = timezone.now()

        # 1. Old unverified user (Should be deleted)
        old_unverified = User.objects.create_user(
            email="old.unverified@example.com",
            password="TestPassword123!",
            full_name="Old Unverified",
        )
        old_unverified.is_verified = False
        old_unverified.date_joined = now - timedelta(hours=50)
        old_unverified.save()

        # 2. New unverified user (Should NOT be deleted, less than 24 hrs)
        new_unverified = User.objects.create_user(
            email="new.unverified@example.com",
            password="TestPassword123!",
            full_name="New Unverified",
        )
        new_unverified.is_verified = False
        new_unverified.date_joined = now - timedelta(hours=10)
        new_unverified.save()

        # 3. Old verified user (Should NOT be deleted)
        old_verified = User.objects.create_user(
            email="old.verified@example.com",
            password="TestPassword123!",
            full_name="Old Verified",
        )
        old_verified.is_verified = True
        old_verified.date_joined = now - timedelta(hours=100)
        old_verified.save()

        # Execute task
        deleted_count = delete_unverified_ghost_users()

        assert deleted_count == 1

        # Verify db state
        assert not User.objects.filter(email="old.unverified@example.com").exists()
        assert User.objects.filter(email="new.unverified@example.com").exists()
        assert User.objects.filter(email="old.verified@example.com").exists()
