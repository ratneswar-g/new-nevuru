import json

from django.core.serializers.json import DjangoJSONEncoder

from .models import AuditLog


def _jsonable(value):
    return json.loads(json.dumps(value if value is not None else {}, cls=DjangoJSONEncoder))


def record_audit(*, actor, action, resource_type, resource_id,
                 previous=None, new=None, request=None):
    """
    Append an immutable audit entry. NEVER pass OTP values, tokens or other
    secrets in previous/new state.
    """
    ip = None
    if request is not None:
        ip = request.META.get('REMOTE_ADDR') or None
    return AuditLog.objects.create(
        actor_id=getattr(actor, 'id', None),
        actor_role=getattr(actor, 'role', '') or '',
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        previous_state=_jsonable(previous),
        new_state=_jsonable(new),
        ip_address=ip,
    )
