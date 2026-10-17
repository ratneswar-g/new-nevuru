from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.exceptions import DomainError
from apps.core.permissions import IsCustomerRole
from apps.incidents.serializers import IncidentSerializer
from apps.pricing.serializers import RateCardSerializer  # noqa: F401  (re-export convenience)

from . import services
from .models import Booking, BookingStatus, OTPChallengeType
from .serializers import (
    BookingCreateSerializer, BookingSerializer, CancelSerializer,
    EmergencySerializer, IncidentCreateSerializer, QuoteRequestSerializer,
)

BOOKING_RELATED = ('rate_card', 'care_partner__user')
BOOKING_PREFETCH = ('otp_challenges', 'care_partner__vehicles')
FINISHED = [BookingStatus.COMPLETED, BookingStatus.CLOSED, BookingStatus.CANCELLED]


def customer_visible_bookings(user):
    live_ids = services.helper_customer_ids(user, permission='can_view_live_status')
    history_ids = services.helper_customer_ids(user, permission='can_view_history')
    q = Q(customer=user) | (Q(customer_id__in=live_ids) & ~Q(status__in=FINISHED)) | \
        Q(customer_id__in=history_ids)
    return (Booking.objects.filter(q).select_related(*BOOKING_RELATED)
            .prefetch_related(*BOOKING_PREFETCH).order_by('-scheduled_pickup_time'))


def _fresh(booking_id):
    return (Booking.objects.select_related(*BOOKING_RELATED)
            .prefetch_related(*BOOKING_PREFETCH).get(pk=booking_id))


class QuoteView(APIView):
    permission_classes = [IsCustomerRole]

    def post(self, request):
        serializer = QuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.quote(serializer.validated_data)
        fare = result['fare']
        return Response({
            'rate_card_version': fare.rate_card_version,
            'distance_km': result['distance_km'],
            'distance_basis': result['distance_basis'],
            'base_fare': fare.base_fare,
            'distance_fare': fare.distance_fare,
            'mobility_surcharge': fare.mobility_surcharge,
            'estimated_waiting_fare': fare.waiting_fare,
            'estimated_waiting_minutes': fare.waiting_minutes,
            'total_fare': fare.total_fare,
            'currency': fare.currency,
            'note': 'Waiting time is billed at actuals on completion; distance is a straight-line estimate.',
        })


class BookingListCreateView(ListAPIView):
    permission_classes = [IsCustomerRole]
    serializer_class = BookingSerializer

    def get_queryset(self):
        qs = customer_visible_bookings(self.request.user)
        wanted = self.request.query_params.get('status')
        return qs.filter(status=wanted) if wanted else qs

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = services.create_booking(actor=request.user, request=request,
                                          data=dict(serializer.validated_data))
        return Response(BookingSerializer(_fresh(booking.id)).data, status=status.HTTP_201_CREATED)


class BookingDetailView(RetrieveAPIView):
    permission_classes = [IsCustomerRole]
    serializer_class = BookingSerializer

    def get_queryset(self):
        return customer_visible_bookings(self.request.user)


class BookingConfirmView(APIView):
    permission_classes = [IsCustomerRole]

    def post(self, request, pk):
        services.confirm_booking(booking_id=pk, actor=request.user, request=request)
        return Response(BookingSerializer(_fresh(pk)).data)


class BookingCancelView(APIView):
    permission_classes = [IsCustomerRole]

    def post(self, request, pk):
        serializer = CancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.cancel_booking(booking_id=pk, actor=request.user, request=request,
                                reason=serializer.validated_data.get('reason', ''))
        return Response(BookingSerializer(_fresh(pk)).data)


class BookingOtpIssueView(APIView):
    """
    The ONLY endpoint that ever returns a plaintext OTP, and only to the
    customer side. Care Partner endpoints have no way to read it.
    """

    permission_classes = [IsCustomerRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'otp_issue'

    def post(self, request, pk, challenge_type):
        kind = challenge_type.upper()
        if kind not in OTPChallengeType.values:
            raise DomainError('NOT_FOUND', 'Unknown OTP type.', status_code=404)
        code, challenge = services.issue_otp(booking_id=pk, challenge_type=kind,
                                             actor=request.user, request=request)
        response = Response({'challenge_type': kind, 'code': code, 'expires_at': challenge.expires_at,
                             'attempts_allowed': challenge.attempts_remaining})
        response['Cache-Control'] = 'no-store'
        return response


class BookingEmergencyView(APIView):
    permission_classes = [IsCustomerRole]

    def post(self, request, pk):
        serializer = EmergencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incident = services.raise_incident(booking_id=pk, reporter=request.user, request=request,
                                           category='EMERGENCY_SOS', emergency=True,
                                           narrative=serializer.validated_data['narrative'])
        return Response({'incident': IncidentSerializer(incident).data,
                         'guidance': services.EMERGENCY_GUIDANCE}, status=status.HTTP_201_CREATED)


class BookingIncidentView(APIView):
    permission_classes = [IsCustomerRole]

    def post(self, request, pk):
        serializer = IncidentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incident = services.raise_incident(booking_id=pk, reporter=request.user, request=request,
                                           **serializer.validated_data)
        return Response(IncidentSerializer(incident).data, status=status.HTTP_201_CREATED)
