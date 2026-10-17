from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_audit
from apps.bookings import services as booking_services
from apps.bookings.models import Booking
from apps.bookings.serializers import (
    EmergencySerializer, IncidentCreateSerializer, OTPCodeSerializer, PartnerBookingSerializer,
)
from apps.core.exceptions import DomainError
from apps.core.permissions import IsAdminRole, IsApprovedCarePartner, IsCarePartnerRole
from apps.incidents.serializers import IncidentSerializer

from .models import CarePartnerDocument, CarePartnerProfile, CarePartnerStatus, Vehicle
from .serializers import (
    CarePartnerSerializer, DutySerializer, KycSubmitSerializer, VehicleSerializer,
)

PARTNER_RELATED = ('customer__customer_profile',)
PARTNER_PREFETCH = ('otp_challenges',)


def _profile(request) -> CarePartnerProfile:
    return CarePartnerProfile.objects.select_related('user').get(user=request.user)


def _partner_booking(partner, pk):
    return (Booking.objects.select_related('customer__customer_profile')
            .prefetch_related('otp_challenges').get(pk=pk, care_partner=partner))


class PartnerMeView(APIView):
    permission_classes = [IsCarePartnerRole]

    def get(self, request):
        profile = CarePartnerProfile.objects.prefetch_related('vehicles', 'documents') \
            .select_related('user').get(user=request.user)
        return Response(CarePartnerSerializer(profile).data)


class PartnerKycSubmitView(APIView):
    """Records document identifiers. File upload storage is not implemented yet."""

    permission_classes = [IsCarePartnerRole]

    def post(self, request):
        s = KycSubmitSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        profile = _profile(request)
        if profile.status in (CarePartnerStatus.APPROVED, CarePartnerStatus.SUSPENDED):
            raise DomainError('INVALID_STATE', f'Account is {profile.status}.')
        CarePartnerDocument.objects.update_or_create(
            care_partner=profile, document_type=s.validated_data['document_type'],
            defaults={'document_identifier': s.validated_data['document_identifier'], 'is_verified': False})
        profile.kyc_submitted_at = timezone.now()
        profile.status = CarePartnerStatus.PENDING_VERIFICATION
        profile.save(update_fields=['kyc_submitted_at', 'status', 'updated_at'])
        record_audit(actor=request.user, action='KYC_SUBMITTED', resource_type='CarePartnerProfile',
                     resource_id=profile.id, new={'document_type': s.validated_data['document_type']},
                     request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PartnerVehicleListCreateView(ListAPIView):
    permission_classes = [IsCarePartnerRole]
    serializer_class = VehicleSerializer

    def get_queryset(self):
        return Vehicle.objects.filter(care_partner__user=self.request.user)

    def post(self, request):
        s = VehicleSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vehicle = s.save(care_partner=_profile(request), is_verified=False)
        record_audit(actor=request.user, action='VEHICLE_ADDED', resource_type='Vehicle',
                     resource_id=vehicle.id, new={'registration_number': vehicle.registration_number},
                     request=request)
        return Response(VehicleSerializer(vehicle).data, status=status.HTTP_201_CREATED)


class PartnerDutyView(APIView):
    permission_classes = [IsApprovedCarePartner]

    def post(self, request):
        s = DutySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        profile = _profile(request)
        if s.validated_data['is_online'] and not profile.vehicles.filter(is_verified=True, is_active=True).exists():
            raise DomainError('NO_VERIFIED_VEHICLE', 'A verified vehicle is required to go online.')
        previous = profile.is_online
        profile.is_online = s.validated_data['is_online']
        profile.save(update_fields=['is_online', 'updated_at'])
        record_audit(actor=request.user, action='PARTNER_DUTY_CHANGED', resource_type='CarePartnerProfile',
                     resource_id=profile.id, previous={'is_online': previous},
                     new={'is_online': profile.is_online}, request=request)
        return Response({'is_online': profile.is_online})


class PartnerBookingListView(ListAPIView):
    permission_classes = [IsApprovedCarePartner]
    serializer_class = PartnerBookingSerializer

    def get_queryset(self):
        qs = (Booking.objects.filter(care_partner__user=self.request.user)
              .select_related('customer__customer_profile').prefetch_related('otp_challenges')
              .order_by('-scheduled_pickup_time'))
        wanted = self.request.query_params.get('status')
        return qs.filter(status=wanted) if wanted else qs


class PartnerBookingDetailView(RetrieveAPIView):
    permission_classes = [IsApprovedCarePartner]
    serializer_class = PartnerBookingSerializer

    def get_queryset(self):
        return (Booking.objects.filter(care_partner__user=self.request.user)
                .select_related('customer__customer_profile').prefetch_related('otp_challenges'))


class _PartnerAction(APIView):
    permission_classes = [IsApprovedCarePartner]

    def respond(self, request, pk):
        return Response(PartnerBookingSerializer(_partner_booking(_profile(request), pk)).data)


class PartnerArriveView(_PartnerAction):
    def post(self, request, pk):
        booking_services.partner_arrive(booking_id=pk, partner=_profile(request),
                                        actor=request.user, request=request)
        return self.respond(request, pk)


class PartnerVerifyPickupView(_PartnerAction):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'otp_verify'

    def post(self, request, pk):
        s = OTPCodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        booking_services.partner_verify_pickup(
            booking_id=pk, partner=_profile(request), code=s.validated_data['code'],
            actor=request.user, request=request)
        return self.respond(request, pk)


class PartnerArriveHospitalView(_PartnerAction):
    def post(self, request, pk):
        booking_services.partner_arrive_hospital(booking_id=pk, partner=_profile(request),
                                                 actor=request.user, request=request)
        return self.respond(request, pk)


class PartnerStartReturnView(_PartnerAction):
    def post(self, request, pk):
        notes = (request.data.get('notes') or '')[:1000] if hasattr(request.data, 'get') else ''
        booking_services.partner_start_return(booking_id=pk, partner=_profile(request),
                                              actor=request.user, request=request, notes=notes)
        return self.respond(request, pk)


class PartnerCompleteView(_PartnerAction):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'otp_verify'

    def post(self, request, pk):
        s = OTPCodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        booking_services.partner_verify_dropoff_and_complete(
            booking_id=pk, partner=_profile(request), code=s.validated_data['code'],
            notes=s.validated_data.get('notes', ''), actor=request.user, request=request)
        return self.respond(request, pk)


class PartnerEmergencyView(_PartnerAction):
    def post(self, request, pk):
        s = EmergencySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        incident = booking_services.raise_incident(
            booking_id=pk, reporter=request.user, request=request, category='EMERGENCY_SOS',
            emergency=True, narrative=s.validated_data['narrative'])
        return Response({'incident': IncidentSerializer(incident).data,
                         'guidance': booking_services.EMERGENCY_GUIDANCE}, status=status.HTTP_201_CREATED)


class PartnerIncidentView(_PartnerAction):
    def post(self, request, pk):
        s = IncidentCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        incident = booking_services.raise_incident(booking_id=pk, reporter=request.user,
                                                   request=request, **s.validated_data)
        return Response(IncidentSerializer(incident).data, status=status.HTTP_201_CREATED)


# ------------------------------------------------------------------------ admin

class AdminPartnerListView(ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = CarePartnerSerializer

    def get_queryset(self):
        qs = CarePartnerProfile.objects.select_related('user').prefetch_related('vehicles', 'documents')
        wanted = self.request.query_params.get('status')
        return qs.filter(status=wanted) if wanted else qs


class _AdminPartnerStatus(APIView):
    permission_classes = [IsAdminRole]
    new_status = None
    action_name = ''
    allowed_from = ()

    def post(self, request, pk):
        profile = CarePartnerProfile.objects.select_related('user').filter(pk=pk).first()
        if profile is None:
            raise DomainError('NOT_FOUND', 'Care Partner not found.', status_code=404)
        if profile.status not in self.allowed_from:
            raise DomainError('INVALID_STATE', f'Cannot {self.action_name} a partner who is {profile.status}.')
        previous = profile.status
        profile.status = self.new_status
        update = ['status', 'updated_at']
        if self.new_status == CarePartnerStatus.APPROVED:
            profile.verified_at = timezone.now()
            update.append('verified_at')
        if self.new_status in (CarePartnerStatus.REJECTED, CarePartnerStatus.SUSPENDED):
            profile.is_online = False
            update.append('is_online')
        profile.save(update_fields=update)
        record_audit(actor=request.user, action=f'PARTNER_{self.action_name.upper()}',
                     resource_type='CarePartnerProfile', resource_id=profile.id,
                     previous={'status': previous}, new={'status': profile.status}, request=request)
        profile = CarePartnerProfile.objects.prefetch_related('vehicles', 'documents') \
            .select_related('user').get(pk=pk)
        return Response(CarePartnerSerializer(profile).data)


PS = CarePartnerStatus


class AdminPartnerApproveView(_AdminPartnerStatus):
    new_status, action_name = PS.APPROVED, 'approve'
    allowed_from = (PS.PENDING_VERIFICATION, PS.SUSPENDED)


class AdminPartnerRejectView(_AdminPartnerStatus):
    new_status, action_name = PS.REJECTED, 'reject'
    allowed_from = (PS.PENDING_VERIFICATION,)


class AdminPartnerSuspendView(_AdminPartnerStatus):
    new_status, action_name = PS.SUSPENDED, 'suspend'
    allowed_from = (PS.APPROVED,)


class AdminVehicleVerifyView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        vehicle = Vehicle.objects.filter(pk=pk).first()
        if vehicle is None:
            raise DomainError('NOT_FOUND', 'Vehicle not found.', status_code=404)
        vehicle.is_verified = True
        vehicle.save(update_fields=['is_verified', 'updated_at'])
        record_audit(actor=request.user, action='VEHICLE_VERIFIED', resource_type='Vehicle',
                     resource_id=vehicle.id, request=request)
        return Response(VehicleSerializer(vehicle).data)
