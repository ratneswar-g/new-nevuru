from decimal import Decimal

from rest_framework import serializers

from apps.users.models import MobilityRequirement

from .models import Booking, OTPChallengeType


def _verified(booking, challenge_type) -> bool:
    return any(c.challenge_type == challenge_type and c.verified_at is not None
               for c in booking.otp_challenges.all())


class _LocationInput(serializers.Serializer):
    pickup_address = serializers.CharField()
    pickup_latitude = serializers.DecimalField(max_digits=9, decimal_places=6,
                                               min_value=Decimal('-90'), max_value=Decimal('90'))
    pickup_longitude = serializers.DecimalField(max_digits=9, decimal_places=6,
                                                min_value=Decimal('-180'), max_value=Decimal('180'))
    pickup_landmark = serializers.CharField(max_length=150, required=False, allow_blank=True)
    hospital_name = serializers.CharField(max_length=150)
    hospital_address = serializers.CharField()
    hospital_latitude = serializers.DecimalField(max_digits=9, decimal_places=6,
                                                 min_value=Decimal('-90'), max_value=Decimal('90'))
    hospital_longitude = serializers.DecimalField(max_digits=9, decimal_places=6,
                                                  min_value=Decimal('-180'), max_value=Decimal('180'))
    mobility_requirement = serializers.ChoiceField(choices=MobilityRequirement.choices)
    is_round_trip = serializers.BooleanField(default=True)
    estimated_waiting_minutes = serializers.IntegerField(min_value=0, max_value=720, required=False, default=0)


class QuoteRequestSerializer(_LocationInput):
    pass


class BookingCreateSerializer(_LocationInput):
    scheduled_pickup_time = serializers.DateTimeField()
    customer_id = serializers.UUIDField(required=False)


class _PartnerSummary(serializers.Serializer):
    """What a customer may see about their assigned Care Partner."""

    def to_representation(self, partner):
        vehicle = next((v for v in partner.vehicles.all() if v.is_verified and v.is_active), None)
        return {
            'id': str(partner.id),
            'first_name': partner.user.first_name,
            'phone_number': partner.user.phone_number,
            'vehicle': None if vehicle is None else {
                'registration_number': vehicle.registration_number,
                'make': vehicle.make, 'model': vehicle.model, 'color': vehicle.color,
            },
        }


class BookingSerializer(serializers.ModelSerializer):
    """Customer / family-helper view. Never contains OTP values or hashes."""

    rate_card_version = serializers.IntegerField(source='rate_card.version', read_only=True)
    care_partner = serializers.SerializerMethodField()
    pickup_verified = serializers.SerializerMethodField()
    dropoff_verified = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'status', 'customer_id', 'pickup_address', 'pickup_latitude', 'pickup_longitude',
            'pickup_landmark', 'hospital_name', 'hospital_address', 'hospital_latitude',
            'hospital_longitude', 'scheduled_pickup_time', 'mobility_requirement', 'is_round_trip',
            'rate_card_version', 'quoted_fare', 'final_fare', 'currency', 'care_partner',
            'pickup_verified', 'dropoff_verified', 'cancellation_reason', 'created_at', 'updated_at',
        ]

    def get_care_partner(self, obj):
        if obj.care_partner is None:
            return None
        return _PartnerSummary(obj.care_partner).data

    def get_pickup_verified(self, obj):
        return _verified(obj, OTPChallengeType.PICKUP)

    def get_dropoff_verified(self, obj):
        return _verified(obj, OTPChallengeType.DROPOFF)


class PartnerBookingSerializer(serializers.ModelSerializer):
    """Care Partner view: operational data only; no fares, OTPs or emergency contacts."""

    customer = serializers.SerializerMethodField()
    pickup_verified = serializers.SerializerMethodField()
    dropoff_verified = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'status', 'customer', 'pickup_address', 'pickup_latitude', 'pickup_longitude',
            'pickup_landmark', 'hospital_name', 'hospital_address', 'hospital_latitude',
            'hospital_longitude', 'scheduled_pickup_time', 'mobility_requirement', 'is_round_trip',
            'pickup_verified', 'dropoff_verified', 'created_at', 'updated_at',
        ]

    def get_customer(self, obj):
        profile = getattr(obj.customer, 'customer_profile', None)
        return {
            'first_name': obj.customer.first_name,
            'phone_number': obj.customer.phone_number,
            'accessibility_notes': profile.accessibility_notes if profile else '',
        }

    def get_pickup_verified(self, obj):
        return _verified(obj, OTPChallengeType.PICKUP)

    def get_dropoff_verified(self, obj):
        return _verified(obj, OTPChallengeType.DROPOFF)


class AdminBookingSerializer(BookingSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    care_partner_id = serializers.UUIDField(read_only=True)
    care_partner_name = serializers.SerializerMethodField()

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + [
            'customer_name', 'customer_phone', 'care_partner_id', 'care_partner_name',
            'pre_incident_status',
        ]

    def get_customer_name(self, obj):
        return f'{obj.customer.first_name} {obj.customer.last_name}'.strip()

    def get_care_partner_name(self, obj):
        if obj.care_partner is None:
            return None
        return f'{obj.care_partner.user.first_name} {obj.care_partner.user.last_name}'.strip()


class OTPCodeSerializer(serializers.Serializer):
    code = serializers.RegexField(r'^\d{4}$', error_messages={'invalid': 'Enter the 4-digit code.'})
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=300)


class IncidentCreateSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=50)
    narrative = serializers.CharField(max_length=4000)
    priority = serializers.ChoiceField(choices=['LOW', 'MEDIUM', 'HIGH'], default='MEDIUM')


class EmergencySerializer(serializers.Serializer):
    narrative = serializers.CharField(max_length=4000, required=False, allow_blank=True,
                                      default='Emergency SOS triggered.')
