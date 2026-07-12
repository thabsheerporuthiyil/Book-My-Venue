import os
import sys

import django

# Add the project root (parent directory of scripts/) to sys.path so Python can find 'config'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.accounts.models import User  # noqa: E402
from apps.tenants.core.models import Tenant  # noqa: E402


def clean():
    print("🧹 Cleaning database...")

    # 1. Delete all tenants (Cascade will delete Memberships, Domains, and Provisions)
    deleted_tenants, _ = Tenant.objects.all().delete()
    print(f"✅ Deleted {deleted_tenants} tenants.")

    # 2. Delete all users (Cascade will delete CustomerProfiles, etc)
    deleted_users, _ = User.objects.all().delete()
    print(f"✅ Deleted {deleted_users} users.")

    # 3. Drop isolated PostgreSQL tenant schemas
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%';")
        schemas = cursor.fetchall()
        for schema in schemas:
            schema_name = schema[0]
            cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;")
            print(f"✅ Dropped old tenant schema: {schema_name}")

    # Note: We intentionally DO NOT delete ServiceRegistry records
    # because those are configuration, not user data.

    print("✨ Database is now completely clean!")


if __name__ == "__main__":
    clean()
