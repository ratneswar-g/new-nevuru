from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_audit
from apps.companions.models import CarePartnerProfile
from apps.core.exceptions import DomainError
from apps.core.permissions import IsCustomerRole

from .authentication import verify_request_identity
from .models import FamilyHelper, User, UserRole
from .serializers import (
    CustomerProfileSerializer,
    FamilyHelperCreateSerializer,
    FamilyHelperSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    """
    Create the Neravu account for an already-verified Firebase identity.
    Phone number and UID come ONLY from the verified token, never the body.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def post(self, request):
        claims = verify_request_identity(request)
        uid = claims.get('uid') or claims.get('sub')
        phone = claims.get('phone_number')
        if not phone:
            raise DomainError('PHONE_NOT_VERIFIED',
                              'Token carries no verified phone number.', status_code=400)

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if User.objects.filter(firebase_uid=uid).exists() or User.objects.filter(phone_number=phone).exists():
            raise DomainError('ALREADY_REGISTERED', 'An account already exists for this identity.')

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    phone_number=phone,
                    firebase_uid=uid,
                    role=data['role'],
                    first_name=data['first_name'],
                    last_name=data.get('last_name', ''),
                    email=data.get('email') or None,
                )
                if data['role'] == UserRole.CARE_PARTNER:
                    CarePartnerProfile.objects.create(user=user)
                record_audit(actor=user, action='USER_REGISTERED', resource_type='User',
                             resource_id=user.id, new={'role': user.role}, request=request)
        except IntegrityError:
            raise DomainError('ALREADY_REGISTERED', 'An account already exists for this identity.')

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CustomerProfileView(APIView):
    permission_classes = [IsCustomerRole]

    def get(self, request):
        profile = getattr(request.user, 'customer_profile', None)
        if profile is None:
            raise DomainError('PROFILE_NOT_FOUND', 'Customer profile not created yet.', status_code=404)
        return Response(CustomerProfileSerializer(profile).data)

    def put(self, request):
        profile = getattr(request.user, 'customer_profile', None)
        serializer = CustomerProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        if profile is None:
            serializer.save(user=request.user)
            code = status.HTTP_201_CREATED
        else:
            serializer.save()
            code = status.HTTP_200_OK
        return Response(serializer.data, status=code)


class FamilyHelperListCreateView(ListAPIView):
    permission_classes = [IsCustomerRole]
    serializer_class = FamilyHelperSerializer

    def get_queryset(self):
        return FamilyHelper.objects.filter(primary_customer=self.request.user).select_related('helper_user').order_by('-created_at')

    def post(self, request):
        serializer = FamilyHelperCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            helper = User.objects.get(phone_number=data['helper_phone_number'],
                                      role=UserRole.CUSTOMER, is_active=True)
        except User.DoesNotExist:
            raise DomainError('HELPER_NOT_FOUND',
                              'No registered customer account with that phone number.', status_code=404)
        if helper.id == request.user.id:
            raise DomainError('INVALID_HELPER', 'You cannot add yourself as a helper.', status_code=400)
        obj, created = FamilyHelper.objects.update_or_create(
            primary_customer=request.user, helper_user=helper,
            defaults={k: v for k, v in data.items() if k != 'helper_phone_number'},
        )
        record_audit(actor=request.user, action='FAMILY_HELPER_GRANTED', resource_type='FamilyHelper',
                     resource_id=obj.id,
                     new={'can_book': obj.can_book, 'can_view_live_status': obj.can_view_live_status,
                          'can_view_history': obj.can_view_history}, request=request)
        return Response(FamilyHelperSerializer(obj).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class FamilyHelperDeleteView(APIView):
    permission_classes = [IsCustomerRole]

    def delete(self, request, pk):
        deleted = FamilyHelper.objects.filter(pk=pk, primary_customer=request.user).first()
        if deleted is None:
            raise DomainError('NOT_FOUND', 'Helper grant not found.', status_code=404)
        record_audit(actor=request.user, action='FAMILY_HELPER_REVOKED', resource_type='FamilyHelper',
                     resource_id=deleted.id, request=request)
        deleted.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
