from datetime import datetime, timezone

from django.conf import settings


def set_jwt_cookies(response, access_token, refresh_token=None):
    """
    Attaches the JWT tokens to the HTTP response as HttpOnly cookies.
    """
    # Access Token Cookie
    access_token_max_age = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
    response.set_cookie(
        key=getattr(settings, "JWT_AUTH_COOKIE", "access_token"),
        value=access_token,
        max_age=int(access_token_max_age),
        expires=datetime.now(timezone.utc) + settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
        domain=getattr(settings, "JWT_AUTH_COOKIE_DOMAIN", None),
        path=getattr(settings, "JWT_AUTH_COOKIE_PATH", "/"),
        secure=getattr(settings, "JWT_AUTH_COOKIE_SECURE", True),
        httponly=getattr(settings, "JWT_AUTH_COOKIE_HTTPONLY", True),
        samesite=getattr(settings, "JWT_AUTH_COOKIE_SAMESITE", "Lax"),
    )

    # Refresh Token Cookie (if provided)
    if refresh_token:
        refresh_token_max_age = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
        response.set_cookie(
            key=getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh_token"),
            value=refresh_token,
            max_age=int(refresh_token_max_age),
            expires=datetime.now(timezone.utc) + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            domain=getattr(settings, "JWT_AUTH_COOKIE_DOMAIN", None),
            path=getattr(settings, "JWT_AUTH_COOKIE_PATH", "/"),
            secure=getattr(settings, "JWT_AUTH_COOKIE_SECURE", True),
            httponly=getattr(settings, "JWT_AUTH_COOKIE_HTTPONLY", True),
            samesite=getattr(settings, "JWT_AUTH_COOKIE_SAMESITE", "Lax"),
        )
    return response


def delete_jwt_cookies(response):
    """
    Removes the JWT tokens from the HTTP response.
    """
    response.delete_cookie(
        getattr(settings, "JWT_AUTH_COOKIE", "access_token"),
        domain=getattr(settings, "JWT_AUTH_COOKIE_DOMAIN", None),
        path=getattr(settings, "JWT_AUTH_COOKIE_PATH", "/"),
    )
    response.delete_cookie(
        getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh_token"),
        domain=getattr(settings, "JWT_AUTH_COOKIE_DOMAIN", None),
        path=getattr(settings, "JWT_AUTH_COOKIE_PATH", "/"),
    )
    return response
