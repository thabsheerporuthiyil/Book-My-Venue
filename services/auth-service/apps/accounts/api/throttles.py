"""
Custom DRF throttle classes for the accounts API.
"""

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Restricts login attempts to 5 per minute per IP address.

    Scope maps to REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login"]
    defined in config/settings/base.py.

    Usage:
        class LoginAPIView(APIView):
            throttle_classes = [LoginRateThrottle]
    """

    scope = "login"


class ResendOTPRateThrottle(AnonRateThrottle):
    """
    Restricts OTP resends to 3 per minute per IP address.
    Mitigates SMS/Email pumping and spam attacks.
    """

    scope = "resend_otp"
