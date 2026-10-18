from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import DomainError
from apps.core.permissions import IsAdminRole

from . import services
from .models import RateCard
from .serializers import RateCardCreateSerializer, RateCardSerializer


class AdminRateCardListCreateView(ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = RateCardSerializer
    queryset = RateCard.objects.all()

    def post(self, request):
        serializer = RateCardCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = services.create_rate_card(actor=request.user, request=request, **serializer.validated_data)
        return Response(RateCardSerializer(card).data, status=status.HTTP_201_CREATED)


class AdminRateCardActivateView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        card = RateCard.objects.filter(pk=pk).first()
        if card is None:
            raise DomainError('NOT_FOUND', 'Rate card not found.', status_code=404)
        card = services.activate_rate_card(card, actor=request.user, request=request)
        return Response(RateCardSerializer(card).data)


class PublicPricingView(APIView):
    """Public, read-only view of the rate card currently in force (if any)."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public'

    def get(self, request):
        try:
            card = services.get_active_rate_card()
        except DomainError:
            return Response({'available': False})
        return Response({
            'available': True, 'currency': 'INR', 'version': card.version,
            'base_fare': card.base_fare, 'base_distance_km': card.base_distance_km,
            'per_km_rate': card.per_km_rate, 'per_minute_waiting_rate': card.per_minute_waiting_rate,
            'mobility_tier_surcharges': card.mobility_tier_surcharges,
        })
