"""
Domain constants for the accounts app.

Use these string constants in service, selector, and permission code
instead of hardcoding role strings directly.
"""


class UserGlobalRole:
    """Global platform role assigned to every user."""

    USER = "USER"
    ADMIN = "ADMIN"

    CHOICES = [
        (USER, "User"),
        (ADMIN, "Admin"),
    ]

    ALL = [USER, ADMIN]
