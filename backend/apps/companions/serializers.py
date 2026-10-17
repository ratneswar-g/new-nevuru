from rest_framework import serializers

from .models import CarePartnerProfile, Vehicle

MOBILITY_VALUES = ['INDEPENDENT', 'WALKER_ASSISTANCE', 'FOLDING_WHEELCHAIR', 'COMPANION_ONLY']


class VehicleSerializer(serializers.ModelSerializer):
    supported_mobility = serializers.ListField(child=serializers.ChoiceField(choices=MOBILITY_VALUES))

    class Meta:
        model = Vehicle
        fields = ['id', 'registration_number', 'make', 'model', 'color', 'vehicle_type',
                  'seating_capacity', 'supported_mobility', 'is_verified', 'is_active',
                  'insurance_expiry', 'fitness_expiry']
        read_only_fields = ['id', 'is_verified']  # verification is admin-only


class CarePartnerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    vehicles = VehicleSerializer(many=True, read_only=True)
    document_types = serializers.SerializerMethodField()

    class Meta:
        model = CarePartnerProfile
        fields = ['id', 'full_name', 'phone_number', 'status', 'is_online', 'completed_trips_count',
                  'kyc_submitted_at', 'verified_at', 'vehicles', 'document_types']

    def get_full_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'.strip()

    def get_document_types(self, obj):
        return [d.document_type for d in obj.documents.all()]


class DutySerializer(serializers.Serializer):
    is_online = serializers.BooleanField()


class KycSubmitSerializer(serializers.Serializer):
    DOC_TYPES = ['DRIVING_LICENSE', 'AADHAAR', 'POLICE_VERIFICATION', 'VEHICLE_RC']
    document_type = serializers.ChoiceField(choices=DOC_TYPES)
    document_identifier = serializers.CharField(max_length=100)
