import logging
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Custom DRF Authentication backend for verifying Firebase ID tokens
    via the official Firebase Admin SDK (with revocation checking)
    and resolving users exclusively via stable Firebase UID mapping.
    """

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode('utf-8')
        
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        token = parts[1]

        try:
            claims = self._verify_token(token)
        except Exception:
            logger.warning("Firebase token verification failed.")
            raise AuthenticationFailed('Invalid, expired, or revoked authentication token.')

        firebase_uid = claims.get('uid') or claims.get('sub')
        if not firebase_uid:
            raise AuthenticationFailed('Invalid token claims: missing UID.')

        # Authoritative lookup exclusively by stable firebase_uid
        User = get_user_model()
        try:
            user = User.objects.get(firebase_uid=firebase_uid)
        except User.DoesNotExist:
            raise AuthenticationFailed('Authentication failed: user not registered.')

        if not user.is_active:
            raise AuthenticationFailed('User account is inactive.')

        return (user, claims)

    def _verify_token(self, token):
        """
        Verify Firebase ID token using firebase_admin SDK with check_revoked=True.
        Fails closed if Firebase Admin is not initialized or configured.
        """
        from firebase_admin import auth
        from apps.core.firebase import ensure_firebase_initialized

        ensure_firebase_initialized()
        try:
            # Verify ID token with revocation check enabled
            decoded_token = auth.verify_id_token(token, check_revoked=True)
            return decoded_token
        except Exception:
            raise AuthenticationFailed('Token verification error.')

    def authenticate_header(self, request):
        return 'Bearer realm="api"'


def verify_request_identity(request):
    """
    Verify the Bearer Firebase ID token on a request WITHOUT requiring an
    existing Neravu user. Used only by the registration endpoint.
    """
    auth_header = authentication.get_authorization_header(request).decode('utf-8')
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise AuthenticationFailed('Authentication credentials were not provided.')
    try:
        claims = FirebaseAuthentication()._verify_token(parts[1])
    except Exception:
        raise AuthenticationFailed('Invalid, expired, or revoked authentication token.')
    if not (claims.get('uid') or claims.get('sub')):
        raise AuthenticationFailed('Invalid token claims: missing UID.')
    return claims
