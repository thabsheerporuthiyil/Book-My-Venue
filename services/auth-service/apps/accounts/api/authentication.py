from django.conf import settings
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
        return self.get_user(validated_token), validated_token
