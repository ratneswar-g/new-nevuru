from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from apps.audit.services import record_audit
from apps.core.exceptions import DomainError
from apps.users.models import MobilityRequirement

from .models import RateCard

TWOPLACES = Decimal('0.01')


def _q(value) -> Decimal:
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class FareBreakdown:
    rate_card_version: int
    base_fare: Decimal
    distance_fare: Decimal
    mobility_surcharge: Decimal
    waiting_fare: Decimal
    total_fare: Decimal
    billable_distance_km: Decimal
    total_distance_km: Decimal
    waiting_minutes: int
    currency: str = 'INR'


def get_active_rate_card(at=None) -> RateCard:
    """
    Return the rate card in force. No fallback amounts exist: if an admin has
    not activated a rate card, pricing is unavailable.
    """
    at = at or timezone.now()
    card = (
        RateCard.objects.filter(is_active=True, effective_from__lte=at)
        .filter(Q(effective_to__isnull=True) | Q(effective_to__gt=at))
        .order_by('-version')
        .first()
    )
    if card is None:
        raise DomainError('RATE_CARD_UNAVAILABLE',
                          'Pricing is not available right now.', status_code=503)
    return card


def compute_fare(rate_card: RateCard, *, distance_km, mobility, is_round_trip,
                 waiting_minutes=0) -> FareBreakdown:
    """
    fare = base_fare
         + max(0, total_distance - base_distance_km) * per_km_rate
         + mobility_tier_surcharge
         + waiting_minutes * per_minute_waiting_rate
    total_distance is doubled for round trips (return transit leg).
    """
    one_way = Decimal(str(distance_km))
    total_distance = one_way * 2 if is_round_trip else one_way
    billable = max(Decimal('0'), total_distance - rate_card.base_distance_km)
    base = _q(rate_card.base_fare)
    distance_fare = _q(billable * rate_card.per_km_rate)
    surcharge = _q(Decimal(str((rate_card.mobility_tier_surcharges or {}).get(mobility, 0))))
    waiting_fare = _q(Decimal(int(waiting_minutes)) * rate_card.per_minute_waiting_rate)
    return FareBreakdown(
        rate_card_version=rate_card.version,
        base_fare=base,
        distance_fare=distance_fare,
        mobility_surcharge=surcharge,
        waiting_fare=waiting_fare,
        total_fare=base + distance_fare + surcharge + waiting_fare,
        billable_distance_km=billable,
        total_distance_km=total_distance,
        waiting_minutes=int(waiting_minutes),
    )


@transaction.atomic
def create_rate_card(*, actor, request, name, base_fare, base_distance_km, per_km_rate,
                     per_minute_waiting_rate, mobility_tier_surcharges, effective_from) -> RateCard:
    """Admin supplies every amount explicitly; nothing is defaulted."""
    next_version = (RateCard.objects.aggregate(m=Max('version'))['m'] or 0) + 1
    card = RateCard.objects.create(
        version=next_version, name=name, base_fare=base_fare,
        base_distance_km=base_distance_km, per_km_rate=per_km_rate,
        per_minute_waiting_rate=per_minute_waiting_rate,
        mobility_tier_surcharges=mobility_tier_surcharges,
        effective_from=effective_from, is_active=False,
    )
    record_audit(actor=actor, action='RATE_CARD_CREATED', resource_type='RateCard',
                 resource_id=card.id, new={'version': card.version, 'name': card.name}, request=request)
    return card


@transaction.atomic
def activate_rate_card(card: RateCard, *, actor, request) -> RateCard:
    now = timezone.now()
    previous = list(RateCard.objects.select_for_update().filter(is_active=True).exclude(pk=card.pk))
    for old in previous:
        old.is_active = False
        old.effective_to = now
        old.save(update_fields=['is_active', 'effective_to', 'updated_at'])
    card.is_active = True
    card.effective_to = None
    if card.effective_from > now:
        pass  # future-dated activation is honoured by get_active_rate_card
    card.save(update_fields=['is_active', 'effective_to', 'updated_at'])
    record_audit(actor=actor, action='RATE_CARD_ACTIVATED', resource_type='RateCard',
                 resource_id=card.id,
                 previous={'superseded_versions': [o.version for o in previous]},
                 new={'version': card.version}, request=request)
    return card


REQUIRED_MOBILITY_KEYS = [m.value for m in MobilityRequirement]
