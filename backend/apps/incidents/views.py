from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings import services as booking_services
from apps.core.permissions import IsAdminRole

from .models import IncidentRecord
from .serializers import IncidentResolveSerializer, IncidentSerializer


class AdminIncidentListView(ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = IncidentSerializer

    def get_queryset(self):
        qs = IncidentRecord.objects.select_related('reporter').order_by('-created_at')
        for key in ('status', 'priority'):
            if self.request.query_params.get(key):
                qs = qs.filter(**{key: self.request.query_params[key]})
        return qs


class AdminIncidentResolveView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        s = IncidentResolveSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        incident = booking_services.resolve_incident(incident_id=pk, actor=request.user, request=request,
                                                     **s.validated_data)
        return Response(IncidentSerializer(incident).data)
