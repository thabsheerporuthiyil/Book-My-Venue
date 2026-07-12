# Proxy import so Django's model discovery works via the standard models.py convention.
from apps.venues.core.models import *  # noqa: F401, F403
