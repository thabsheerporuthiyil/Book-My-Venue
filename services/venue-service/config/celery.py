"""
Celery configuration for Book My Venue — Venue Service.

Reserved for future async tasks (e.g., image processing, search indexing).
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("venue_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
