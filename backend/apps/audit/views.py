from rest_framework import serializers
from rest_framework.generics import ListAPIView

from apps.core.permissions import IsAdminRole

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'actor_id', 'actor_role', 'action', 'resource_type', 'resource_id',
                  'previous_state', 'new_state', 'timestamp']
        read_only_fields = fields


class AdminAuditLogListView(ListAPIView):
    """Read-only. IP addresses are intentionally not exposed through the API."""

    permission_classes = [IsAdminRole]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.all()
        for param, field in (('action', 'action'), ('resource_type', 'resource_type'),
                             ('resource_id', 'resource_id')):
            if self.request.query_params.get(param):
                qs = qs.filter(**{field: self.request.query_params[param]})
        return qs
