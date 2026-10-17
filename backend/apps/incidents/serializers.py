from rest_framework import serializers

from .models import IncidentRecord


class IncidentSerializer(serializers.ModelSerializer):
    reporter_role = serializers.CharField(source='reporter.role', read_only=True)

    class Meta:
        model = IncidentRecord
        fields = ['id', 'booking_id', 'reporter_role', 'category', 'priority', 'status',
                  'narrative', 'resolution_notes', 'resolved_at', 'created_at']
        read_only_fields = fields


class IncidentResolveSerializer(serializers.Serializer):
    resolution_notes = serializers.CharField(max_length=4000)
    booking_action = serializers.ChoiceField(choices=['RESUME', 'CANCEL'], default='RESUME')
