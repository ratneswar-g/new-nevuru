from django.db.models import Count
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.companions.models import CarePartnerProfile, CarePartnerStatus
from apps.core.permissions import IsAdminRole
from apps.incidents.models import IncidentRecord, IncidentStatus

from . import services
from .models import Booking
from .serializers import AdminBookingSerializer, CancelSerializer
from .views import BOOKING_PREFETCH, BOOKING_RELATED, _fresh
from rest_framework import serializers


def _admin_qs():
    return (Booking.objects.select_related('customer', *BOOKING_RELATED)
            .prefetch_related(*BOOKING_PREFETCH))


class AdminBookingListView(ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminBookingSerializer

    def get_queryset(self):
        qs = _admin_qs()
        wanted = self.request.query_params.get('status')
        return qs.filter(status=wanted) if wanted else qs


class AdminBookingDetailView(RetrieveAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminBookingSerializer

    def get_queryset(self):
        return _admin_qs()


class AssignSerializer(serializers.Serializer):
    care_partner_id = serializers.UUIDField()


class AdminBookingAssignView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        s = AssignSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        services.assign_partner(booking_id=pk, partner_id=s.validated_data['care_partner_id'],
                                actor=request.user, request=request)
        return Response(AdminBookingSerializer(_fresh(pk)).data)


class AdminBookingUnassignView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        services.unassign_partner(booking_id=pk, actor=request.user, request=request)
        return Response(AdminBookingSerializer(_fresh(pk)).data)


class AdminBookingCancelView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        s = CancelSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        services.cancel_booking(booking_id=pk, actor=request.user, request=request,
                                reason=s.validated_data.get('reason', ''))
        return Response(AdminBookingSerializer(_fresh(pk)).data)


class AdminBookingCloseView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        services.close_booking(booking_id=pk, actor=request.user, request=request)
        return Response(AdminBookingSerializer(_fresh(pk)).data)


class AdminDashboardView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        by_status = {row['status']: row['n'] for row in
                     Booking.objects.values('status').annotate(n=Count('id'))}
        return Response({
            'bookings_by_status': by_status,
            'partners_pending_verification': CarePartnerProfile.objects.filter(
                status=CarePartnerStatus.PENDING_VERIFICATION).count(),
            'partners_online': CarePartnerProfile.objects.filter(
                status=CarePartnerStatus.APPROVED, is_online=True).count(),
            'open_incidents': IncidentRecord.objects.exclude(
                status__in=[IncidentStatus.RESOLVED, IncidentStatus.CLOSED]).count(),
        })
