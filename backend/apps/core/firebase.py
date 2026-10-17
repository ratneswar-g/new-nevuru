import logging
import os

logger = logging.getLogger(__name__)


def ensure_firebase_initialized() -> bool:
    """
    Lazily initialise the Firebase Admin SDK from a service-account file path
    supplied via environment (never committed). Returns False when not
    configured; token verification then fails closed.
    """
    import firebase_admin
    from firebase_admin import credentials

    try:
        firebase_admin.get_app()
        return True
    except ValueError:
        pass

    cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH') or os.environ.get(
        'GOOGLE_APPLICATION_CREDENTIALS'
    )
    if not cred_path:
        logger.warning('Firebase Admin not configured; all token verification will fail.')
        return False
    try:
        firebase_admin.initialize_app(credentials.Certificate(cred_path))
        return True
    except Exception:
        logger.exception('Failed to initialise Firebase Admin SDK.')
        return False
