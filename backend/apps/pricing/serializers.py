from decimal import Decimal

from rest_framework import serializers

from .models import RateCard
from .services import REQUIRED_MOBILITY_KEYS


class RateCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateCard
        fields = [
            'id', 'version', 'name', 'base_fare', 'base_distance_km', 'per_km_rate',
            'per_minute_waiting_rate', 'mobility_tier_surcharges', 'effective_from',
            'effective_to', 'is_active', 'created_at',
        ]
        read_only_fields = fields


class RateCardCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    base_fare = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'))
    base_distance_km = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=Decimal('0'))
    per_km_rate = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0'))
    per_minute_waiting_rate = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0'))
    mobility_tier_surcharges = serializers.DictField(child=serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=Decimal('0')))
    effective_from = serializers.DateTimeField()

    def validate_mobility_tier_surcharges(self, value):
        missing = [k for k in REQUIRED_MOBILITY_KEYS if k not in value]
        extra = [k for k in value if k not in REQUIRED_MOBILITY_KEYS]
        if missing or extra:
            raise serializers.ValidationError(
                f'Surcharges must define exactly {REQUIRED_MOBILITY_KEYS}; missing={missing}, unknown={extra}.')
        return {k: str(v) for k, v in value.items()}
