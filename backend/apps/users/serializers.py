from rest_framework import serializers

from .models import CustomerProfile, FamilyHelper, User, UserRole


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    has_customer_profile = serializers.SerializerMethodField()
    care_partner_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'created_at', 'has_customer_profile',
            'care_partner_status',
        ]
        read_only_fields = ['id', 'phone_number', 'role', 'is_active', 'created_at']

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip()

    def get_has_customer_profile(self, obj):
        return hasattr(obj, 'customer_profile')

    def get_care_partner_status(self, obj):
        profile = getattr(obj, 'care_partner_profile', None)
        return profile.status if profile else None


class RegisterSerializer(serializers.Serializer):
    # Role is the ONLY privilege-related client input and ADMIN is never accepted.
    role = serializers.ChoiceField(choices=[UserRole.CUSTOMER, UserRole.CARE_PARTNER])
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation', 'default_mobility_need',
            'accessibility_notes', 'updated_at',
        ]
        read_only_fields = ['updated_at']


class FamilyHelperSerializer(serializers.ModelSerializer):
    helper_phone_number = serializers.CharField(source='helper_user.phone_number', read_only=True)
    helper_name = serializers.SerializerMethodField()

    class Meta:
        model = FamilyHelper
        fields = [
            'id', 'helper_phone_number', 'helper_name', 'can_book',
            'can_view_live_status', 'can_view_history', 'relationship', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_helper_name(self, obj):
        return f'{obj.helper_user.first_name} {obj.helper_user.last_name}'.strip()


class FamilyHelperCreateSerializer(serializers.Serializer):
    helper_phone_number = serializers.CharField(max_length=15)
    can_book = serializers.BooleanField(default=False)
    can_view_live_status = serializers.BooleanField(default=True)
    can_view_history = serializers.BooleanField(default=False)
    relationship = serializers.CharField(max_length=50, required=False, allow_blank=True)
