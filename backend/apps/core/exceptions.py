"""
Consistent API error contract: {"error": {"code", "message", "details"}}.
"""

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler


class DomainError(APIException):
    """Business-rule violation enforced on the server."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Operation not permitted in the current state.'
    default_code = 'DOMAIN_ERROR'

    def __init__(self, code, message, status_code=None, details=None):
        super().__init__(detail=message, code=code)
        if status_code is not None:
            self.status_code = status_code
        self.extra_details = details or {}


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = {}
    if isinstance(exc, ValidationError):
        code = 'VALIDATION_ERROR'
        message = 'One or more fields are invalid.'
        details = response.data
    elif isinstance(exc, DomainError):
        code = str(exc.get_codes())
        message = str(exc.detail)
        details = exc.extra_details
    else:
        codes = exc.get_codes() if hasattr(exc, 'get_codes') else 'ERROR'
        code = str(codes).upper() if isinstance(codes, str) else 'ERROR'
        detail = getattr(exc, 'detail', 'Request failed.')
        message = str(detail) if not isinstance(detail, (dict, list)) else 'Request failed.'
        if isinstance(detail, (dict, list)):
            details = detail

    response.data = {'error': {'code': code, 'message': message, 'details': details}}
    return response
