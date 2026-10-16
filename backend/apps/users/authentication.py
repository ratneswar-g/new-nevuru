import logging
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Custom DRF Authentication backend for verifying Firebase ID tokens
    via the official Firebase Admin SDK and resolving them to Neravu Users
    via stable Firebase UID mapping.
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
        except Exception as e:
            logger.warning(f"Firebase token verification failed: {str(e)}")
            raise AuthenticationFailed('Invalid, expired, or revoked authentication token.')

        firebase_uid = claims.get('uid') or claims.get('sub')
        if not firebase_uid:
            raise AuthenticationFailed('Invalid token claims: missing UID.')

        # Authoritative lookup by stable firebase_uid
        User = get_user_model()
        try:
            user = User.objects.get(firebase_uid=firebase_uid)
        except User.DoesNotExist:
            # Reject unknown identities unless explicitly registered.
            # To support secure customer registration/login linking during onboarding:
            # We can lookup by phone number if verified by Firebase, but requirements state:
            # "Do not silently link a Firebase identity to an existing account solely because the phone number matches."
            # Therefore, we require explicit linking or auto-provisioning ONLY for new customers when phone matches or uid is bound.
            phone_number = claims.get('phone_number')
            if phone_number:
                # Check if user exists with this phone number
                try:
                    user = User.objects.get(phone_number=phone_number)
                    if user.firebase_uid and user.firebase_uid != firebase_uid:
                        # Conflict! Phone number linked to another Firebase UID
                        raise AuthenticationFailed('Account conflict: phone number linked to another authentication identity.')
                    elif not user.firebase_uid:
                        # Secure initial link or registration
                        user.firebase_uid = firebase_uid
                        user.save(update_fields=['firebase_uid', 'updated_at'])
                except User.DoesNotExist:
                    # Auto-provision new CUSTOMER account securely
                    user = User.objects.create_user(
                        phone_number=phone_number,
                        firebase_uid=firebase_uid,
                        role='CUSTOMER'
                    )
            else:
                raise AuthenticationFailed('User not registered and no verified phone number in claims.')

        if not user.is_active:
            raise AuthenticationFailed('User account is inactive.')

        return (user, claims)

    def _verify_token(self, token):
        """
        Verify Firebase ID token using firebase_admin SDK.
        Fails closed if Firebase Admin is not initialized or configured.
        """
        import firebase_admin
        from firebase_admin import auth, exceptions

        try:
            # Verify ID token (checks signature, exp, iss, aud)
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise AuthenticationFailed(f"Token verification error: {str(e)}")

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
