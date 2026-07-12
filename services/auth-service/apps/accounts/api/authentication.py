from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomJWTCookieAuthentication(JWTAuthentication):
    """
    Custom authentication class that reads the JWT access token from an
    HttpOnly cookie in addition to the standard Authorization header.
    """

    def authenticate(self, request):
        # 1. First try to extract the token from the standard Authorization header.
        # This is useful for mobile apps or internal service-to-service calls.
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                return self.get_validated_token_and_user(raw_token)

        # 2. If no header, check if the token is present in the cookies.
        raw_token = request.COOKIES.get(getattr(settings, "JWT_AUTH_COOKIE", "access_token"))
        if raw_token is not None:
            return self.get_validated_token_and_user(raw_token)

        # 3. No token found anywhere, return None (unauthenticated)
        return None

    def get_validated_token_and_user(self, raw_token):
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        # =========================================================================
        # GLOBAL REVOCATION TIMESTAMP CHECK (INSTANT ACCESS TOKEN INVALIDATION)
        # =========================================================================
        # Check if the user has been forced out of all sessions (e.g., password change).
        # If the token was issued BEFORE this timestamp, we reject it immediately.
        revocation_timestamp = cache.get(f"jwt:revoke:{user.id}")
        if revocation_timestamp:
            # simplejwt sets 'iat' on all generated tokens by default
            token_iat = validated_token.get("iat")
            if token_iat and token_iat < revocation_timestamp:
                raise AuthenticationFailed(
                    "This token has been revoked due to a recent security change.", code="token_not_valid"
                )

        return user, validated_token
