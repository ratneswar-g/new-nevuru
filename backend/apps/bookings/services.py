import hashlib
import hmac
import math
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.audit.services import record_audit
from apps.companions.models import CarePartnerProfile, CarePartnerStatus
from apps.core.exceptions import DomainError
from apps.core.geo import haversine_km
from apps.incidents.models import IncidentPriority, IncidentRecord, IncidentStatus
from apps.journeys.models import AccompanimentSession
from apps.pricing import services as pricing
from apps.users.models import FamilyHelper, User, UserRole

from .models import Booking, BookingStatus as S, OTPChallenge, OTPChallengeType
from .state_machine import (
    ALLOWED_TRANSITIONS, CUSTOMER_CANCELLABLE, FLAGGABLE_STATUSES,
    PARTNER_ACTIVE_STATUSES, RESUME_TARGETS, TERMINAL,
)

EMERGENCY_GUIDANCE = (
    'Neravu is not an ambulance service and does not provide clinical care. '
    'For a medical emergency call 108 or 112 immediately. Neravu operations has been alerted.'
)


# --------------------------------------------------------------------------- access

def lock_booking(pk) -> Booking:
    """Row-lock a booking (call inside transaction.atomic)."""
    try:
        return (Booking.objects.select_for_update(of=('self',))
                .select_related('customer', 'care_partner__user', 'rate_card').get(pk=pk))
    except Booking.DoesNotExist:
        raise DomainError('NOT_FOUND', 'Booking not found.', status_code=404)


def helper_customer_ids(user, *, permission) -> list:
    return list(FamilyHelper.objects.filter(helper_user=user, **{permission: True})
                .values_list('primary_customer_id', flat=True))


def customer_can_view(user, booking: Booking) -> bool:
    if booking.customer_id == user.id:
        return True
    return FamilyHelper.objects.filter(helper_user=user, primary_customer_id=booking.customer_id,
                                       can_view_live_status=True).exists()


def customer_can_act(user, booking: Booking, *, needs_book=False) -> bool:
    """Owner always; family helpers only with the relevant delegated permission."""
    if booking.customer_id == user.id:
        return True
    permission = 'can_book' if needs_book else 'can_view_live_status'
    return FamilyHelper.objects.filter(helper_user=user, primary_customer_id=booking.customer_id,
                                       **{permission: True}).exists()


# ----------------------------------------------------------------- core transition

def _snapshot(b: Booking) -> dict:
    return {'status': b.status, 'care_partner_id': str(b.care_partner_id) if b.care_partner_id else None}


def transition(booking: Booking, to_status, *, actor, request, resume=False, **field_updates) -> Booking:
    """The ONLY place booking.status changes. Caller must hold the row lock."""
    if resume:
        # Only incident resolution may leave INCIDENT_FLAGGED other than by cancelling,
        # and only back to the exact state held when the incident was raised.
        allowed = RESUME_TARGETS if (booking.status == S.INCIDENT_FLAGGED
                                     and to_status == booking.pre_incident_status) else set()
    else:
        allowed = ALLOWED_TRANSITIONS.get(booking.status, set())
    if to_status not in allowed:
        raise DomainError('INVALID_TRANSITION',
                          f'Cannot move booking from {booking.status} to {to_status}.',
                          details={'from': booking.status, 'to': str(to_status)})
    previous = _snapshot(booking)
    booking.status = to_status
    for k, v in field_updates.items():
        setattr(booking, k, v)
    booking.save()
    record_audit(actor=actor, action='BOOKING_STATUS_CHANGED', resource_type='Booking',
                 resource_id=booking.id, previous=previous, new=_snapshot(booking), request=request)
    return booking


# ------------------------------------------------------------------- customer side

def _estimate(rate_card, *, pickup, hospital, mobility, is_round_trip, waiting_minutes=0):
    distance = haversine_km(pickup[0], pickup[1], hospital[0], hospital[1])
    fare = pricing.compute_fare(rate_card, distance_km=distance, mobility=mobility,
                                is_round_trip=is_round_trip, waiting_minutes=waiting_minutes)
    return distance, fare


def quote(data) -> dict:
    card = pricing.get_active_rate_card()
    distance, fare = _estimate(
        card, pickup=(data['pickup_latitude'], data['pickup_longitude']),
        hospital=(data['hospital_latitude'], data['hospital_longitude']),
        mobility=data['mobility_requirement'], is_round_trip=data['is_round_trip'],
        waiting_minutes=data.get('estimated_waiting_minutes', 0))
    return {'distance_km': distance, 'distance_basis': 'STRAIGHT_LINE_ESTIMATE', 'fare': fare}


@transaction.atomic
def create_booking(*, actor, request, data) -> Booking:
    customer = actor
    on_behalf = data.get('customer_id')
    if on_behalf and str(on_behalf) != str(actor.id):
        if not FamilyHelper.objects.filter(helper_user=actor, primary_customer_id=on_behalf,
                                           can_book=True).exists():
            raise DomainError('FORBIDDEN', 'You may not book on behalf of this customer.', status_code=403)
        customer = User.objects.get(pk=on_behalf)
    if not hasattr(customer, 'customer_profile'):
        raise DomainError('PROFILE_INCOMPLETE',
                          'Emergency contact details are required before booking.', status_code=422)
    if data['scheduled_pickup_time'] <= timezone.now():
        raise DomainError('INVALID_SCHEDULE', 'Pickup time must be in the future.', status_code=400)

    card = pricing.get_active_rate_card()
    _, fare = _estimate(
        card, pickup=(data['pickup_latitude'], data['pickup_longitude']),
        hospital=(data['hospital_latitude'], data['hospital_longitude']),
        mobility=data['mobility_requirement'], is_round_trip=data['is_round_trip'],
        waiting_minutes=data.get('estimated_waiting_minutes', 0))

    fields = {k: v for k, v in data.items() if k not in ('customer_id', 'estimated_waiting_minutes')}
    booking = Booking.objects.create(customer=customer, rate_card=card, quoted_fare=fare.total_fare,
                                     status=S.REQUESTED, **fields)
    transition(booking, S.QUOTED, actor=actor, request=request)
    record_audit(actor=actor, action='BOOKING_CREATED', resource_type='Booking', resource_id=booking.id,
                 new={'quoted_fare': str(fare.total_fare), 'rate_card_version': card.version,
                      'customer_id': str(customer.id)}, request=request)
    return booking


@transaction.atomic
def confirm_booking(*, booking_id, actor, request) -> Booking:
    booking = lock_booking(booking_id)
    if not customer_can_act(actor, booking, needs_book=True):
        raise DomainError('NOT_FOUND', 'Booking not found.', status_code=404)
    return transition(booking, S.CONFIRMED, actor=actor, request=request)


@transaction.atomic
def cancel_booking(*, booking_id, actor, request, reason='') -> Booking:
    booking = lock_booking(booking_id)
    if actor.role == UserRole.ADMIN:
        if booking.status in TERMINAL or booking.status == S.COMPLETED:
            raise DomainError('INVALID_TRANSITION', f'Booking is already {booking.status}.')
    else:
        if not customer_can_act(actor, booking, needs_book=True):
            raise DomainError('NOT_FOUND', 'Booking not found.', status_code=404)
        if booking.status not in CUSTOMER_CANCELLABLE:
            raise DomainError('INVALID_TRANSITION',
                              'This booking can no longer be cancelled by the customer. Contact support.')
    return transition(booking, S.CANCELLED, actor=actor, request=request,
                      cancellation_reason=(reason or '')[:300])


# ------------------------------------------------------------------------- OTP

def _hash_otp(booking_id, challenge_type, code: str) -> str:
    msg = f'{booking_id}:{challenge_type}:{code}'.encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()


@transaction.atomic
def issue_otp(*, booking_id, challenge_type, actor, request):
    """
    Customer-side only. Returns the plaintext OTP ONCE; only its HMAC is stored.
    Re-issuing invalidates any earlier unverified challenge of the same type.
    """
    booking = lock_booking(booking_id)
    if not customer_can_view(actor, booking):
        raise DomainError('NOT_FOUND', 'Booking not found.', status_code=404)

    if challenge_type == OTPChallengeType.PICKUP:
        if booking.status != S.ARRIVED:
            raise DomainError('OTP_NOT_AVAILABLE',
                              'Pickup OTP can be issued only after your Care Partner has arrived.')
    else:
        ok = booking.status == S.RETURN_TRANSIT or (
            booking.status == S.ACCOMPANIMENT and not booking.is_round_trip)
        if not ok:
            raise DomainError('OTP_NOT_AVAILABLE',
                              'Drop-off OTP can be issued only at the end of the journey.')

    if OTPChallenge.objects.filter(booking=booking, challenge_type=challenge_type,
                                   verified_at__isnull=False).exists():
        raise DomainError('OTP_ALREADY_VERIFIED', 'This step has already been verified.')

    now = timezone.now()
    OTPChallenge.objects.filter(booking=booking, challenge_type=challenge_type,
                                verified_at__isnull=True).update(attempts_remaining=0, expires_at=now)
    code = f'{secrets.randbelow(10000):04d}'
    challenge = OTPChallenge.objects.create(
        booking=booking, challenge_type=challenge_type,
        otp_hash=_hash_otp(booking.id, challenge_type, code),
        expires_at=now + timedelta(minutes=settings.OTP_TTL_MINUTES),
        attempts_remaining=settings.OTP_MAX_ATTEMPTS,
    )
    record_audit(actor=actor, action='OTP_ISSUED', resource_type='Booking', resource_id=booking.id,
                 new={'challenge_type': challenge_type}, request=request)
    return code, challenge


def _verify_otp_locked(booking: Booking, challenge_type, code: str, *, actor, request):
    """
    Returns (ok, error) so the caller can COMMIT the attempt decrement before
    raising. Never logs or returns the code.
    """
    challenge = (OTPChallenge.objects.select_for_update()
                 .filter(booking=booking, challenge_type=challenge_type, verified_at__isnull=True)
                 .order_by('-created_at').first())
    if challenge is None:
        return False, DomainError('OTP_NOT_ISSUED', 'Ask the customer to generate the code in their app.',
                                  status_code=409)
    if challenge.expires_at <= timezone.now():
        return False, DomainError('OTP_EXPIRED', 'The code has expired. Ask the customer for a new one.',
                                  status_code=410)
    if challenge.attempts_remaining <= 0:
        return False, DomainError('OTP_LOCKED', 'Too many incorrect attempts. Ask the customer for a new code.',
                                  status_code=423)

    expected = challenge.otp_hash
    if hmac.compare_digest(expected, _hash_otp(booking.id, challenge_type, code or '')):
        challenge.verified_at = timezone.now()
        challenge.save(update_fields=['verified_at'])
        record_audit(actor=actor, action='OTP_VERIFIED', resource_type='Booking', resource_id=booking.id,
                     new={'challenge_type': challenge_type}, request=request)
        return True, None

    challenge.attempts_remaining -= 1
    challenge.save(update_fields=['attempts_remaining'])
    record_audit(actor=actor, action='OTP_VERIFY_FAILED', resource_type='Booking', resource_id=booking.id,
                 new={'challenge_type': challenge_type, 'attempts_remaining': challenge.attempts_remaining},
                 request=request)
    return False, DomainError('OTP_INVALID', 'Incorrect code.', status_code=400,
                              details={'attempts_remaining': challenge.attempts_remaining})


# ------------------------------------------------------------------- assignment

def _eligible_vehicle_exists(partner: CarePartnerProfile, mobility) -> bool:
    return any(mobility in (v.supported_mobility or [])
               for v in partner.vehicles.filter(is_verified=True, is_active=True))


@transaction.atomic
def assign_partner(*, booking_id, partner_id, actor, request) -> Booking:
    booking = lock_booking(booking_id)
    if booking.status not in (S.CONFIRMED, S.ASSIGNED):
        raise DomainError('INVALID_TRANSITION',
                          f'Cannot assign a Care Partner while booking is {booking.status}.')
    try:
        partner = (CarePartnerProfile.objects.select_for_update(of=('self',))
                   .select_related('user').get(pk=partner_id))
    except CarePartnerProfile.DoesNotExist:
        raise DomainError('NOT_FOUND', 'Care Partner not found.', status_code=404)

    if partner.status != CarePartnerStatus.APPROVED or not partner.user.is_active:
        raise DomainError('PARTNER_NOT_ELIGIBLE', 'Care Partner is not approved.')
    if not _eligible_vehicle_exists(partner, booking.mobility_requirement):
        raise DomainError('PARTNER_NOT_ELIGIBLE',
                          'Care Partner has no verified, active vehicle supporting this mobility requirement.')
    if Booking.objects.filter(care_partner=partner, status__in=PARTNER_ACTIVE_STATUSES) \
            .exclude(pk=booking.pk).exists():
        raise DomainError('PARTNER_BUSY', 'Care Partner is already engaged in another journey.')

    if booking.status == S.ASSIGNED:
        previous = _snapshot(booking)
        booking.care_partner = partner
        booking.save(update_fields=['care_partner', 'updated_at'])
        record_audit(actor=actor, action='BOOKING_PARTNER_REASSIGNED', resource_type='Booking',
                     resource_id=booking.id, previous=previous, new=_snapshot(booking), request=request)
        return booking
    return transition(booking, S.ASSIGNED, actor=actor, request=request, care_partner=partner)


@transaction.atomic
def unassign_partner(*, booking_id, actor, request) -> Booking:
    booking = lock_booking(booking_id)
    booking_prev = booking.care_partner_id
    booking = transition(booking, S.CONFIRMED, actor=actor, request=request, care_partner=None)
    record_audit(actor=actor, action='BOOKING_PARTNER_UNASSIGNED', resource_type='Booking',
                 resource_id=booking.id, previous={'care_partner_id': str(booking_prev)}, request=request)
    return booking


# ----------------------------------------------------------- partner journey steps

def _own_booking(booking_id, partner: CarePartnerProfile) -> Booking:
    booking = lock_booking(booking_id)
    if booking.care_partner_id != partner.id:
        raise DomainError('NOT_FOUND', 'Booking not found.', status_code=404)
    return booking


@transaction.atomic
def partner_arrive(*, booking_id, partner, actor, request) -> Booking:
    return transition(_own_booking(booking_id, partner), S.ARRIVED, actor=actor, request=request)


def partner_verify_pickup(*, booking_id, partner, code, actor, request) -> Booking:
    with transaction.atomic():
        booking = _own_booking(booking_id, partner)
        if booking.status != S.ARRIVED:
            raise DomainError('INVALID_TRANSITION', f'Booking is {booking.status}, expected ARRIVED.')
        ok, error = _verify_otp_locked(booking, OTPChallengeType.PICKUP, code, actor=actor, request=request)
        if ok:
            transition(booking, S.IN_TRANSIT_HOSPITAL, actor=actor, request=request)
    if not ok:
        raise error  # raised AFTER the attempt counter has been committed
    return booking


@transaction.atomic
def partner_arrive_hospital(*, booking_id, partner, actor, request) -> Booking:
    booking = _own_booking(booking_id, partner)
    transition(booking, S.ACCOMPANIMENT, actor=actor, request=request)
    now = timezone.now()
    AccompanimentSession.objects.update_or_create(
        booking=booking, defaults={'hospital_arrived_at': now, 'accompaniment_started_at': now})
    return booking


def _close_accompaniment(booking: Booking, notes: str = '') -> int:
    session = AccompanimentSession.objects.select_for_update().get(booking=booking)
    now = timezone.now()
    minutes = 0
    if session.accompaniment_started_at:
        minutes = max(0, math.ceil((now - session.accompaniment_started_at).total_seconds() / 60))
    session.accompaniment_ended_at = now
    session.waiting_duration_minutes = minutes
    if notes:
        session.non_clinical_notes = (session.non_clinical_notes + '\n' + notes).strip()[:5000]
    session.save()
    return minutes


@transaction.atomic
def partner_start_return(*, booking_id, partner, actor, request, notes='') -> Booking:
    booking = _own_booking(booking_id, partner)
    if not booking.is_round_trip:
        raise DomainError('NOT_ROUND_TRIP', 'This booking has no return journey.')
    transition(booking, S.RETURN_TRANSIT, actor=actor, request=request)
    _close_accompaniment(booking, notes)
    return booking


def partner_verify_dropoff_and_complete(*, booking_id, partner, code, actor, request, notes='') -> Booking:
    with transaction.atomic():
        booking = _own_booking(booking_id, partner)
        valid_state = booking.status == S.RETURN_TRANSIT or (
            booking.status == S.ACCOMPANIMENT and not booking.is_round_trip)
        if not valid_state:
            raise DomainError('INVALID_TRANSITION',
                              f'Booking is {booking.status}; drop-off cannot be completed now.')
        ok, error = _verify_otp_locked(booking, OTPChallengeType.DROPOFF, code, actor=actor, request=request)
        if ok:
            if booking.status == S.ACCOMPANIMENT:  # one-way trip ends at the hospital
                _close_accompaniment(booking, notes)
            session = AccompanimentSession.objects.get(booking=booking)
            distance = haversine_km(booking.pickup_latitude, booking.pickup_longitude,
                                    booking.hospital_latitude, booking.hospital_longitude)
            fare = pricing.compute_fare(booking.rate_card, distance_km=distance,
                                        mobility=booking.mobility_requirement,
                                        is_round_trip=booking.is_round_trip,
                                        waiting_minutes=session.waiting_duration_minutes)
            transition(booking, S.COMPLETED, actor=actor, request=request, final_fare=fare.total_fare)
            CarePartnerProfile.objects.filter(pk=partner.pk).update(
                completed_trips_count=F('completed_trips_count') + 1)
    if not ok:
        raise error
    return booking


# ------------------------------------------------------------------ admin side

@transaction.atomic
def close_booking(*, booking_id, actor, request) -> Booking:
    return transition(lock_booking(booking_id), S.CLOSED, actor=actor, request=request)


# ---------------------------------------------------------- incidents/emergency

@transaction.atomic
def raise_incident(*, booking_id, reporter, request, category, narrative,
                   priority=IncidentPriority.MEDIUM, emergency=False):
    booking = lock_booking(booking_id)
    is_admin = reporter.role == UserRole.ADMIN
    is_partner = reporter.role == UserRole.CARE_PARTNER and booking.care_partner and \
        booking.care_partner.user_id == reporter.id
    is_customer_side = reporter.role == UserRole.CUSTOMER and customer_can_view(reporter, booking)
    if not (is_admin or is_partner or is_customer_side):
        raise DomainError('NOT_FOUND', 'Booking not found.', status_code=404)

    if emergency:
        priority, category = IncidentPriority.CRITICAL, 'EMERGENCY_SOS'
    incident = IncidentRecord.objects.create(booking=booking, reporter=reporter, category=category,
                                             priority=priority, narrative=narrative)
    record_audit(actor=reporter, action='INCIDENT_REPORTED', resource_type='IncidentRecord',
                 resource_id=incident.id,
                 new={'booking_id': str(booking.id), 'priority': priority, 'category': category},
                 request=request)
    if emergency and booking.status in FLAGGABLE_STATUSES:
        transition(booking, S.INCIDENT_FLAGGED, actor=reporter, request=request,
                   pre_incident_status=booking.status)
    return incident


@transaction.atomic
def resolve_incident(*, incident_id, actor, request, resolution_notes, booking_action):
    try:
        incident = IncidentRecord.objects.select_for_update(of=('self',)).get(pk=incident_id)
    except IncidentRecord.DoesNotExist:
        raise DomainError('NOT_FOUND', 'Incident not found.', status_code=404)
    if incident.status in (IncidentStatus.RESOLVED, IncidentStatus.CLOSED):
        raise DomainError('INVALID_TRANSITION', 'Incident is already resolved.')
    booking = lock_booking(incident.booking_id)

    if booking.status == S.INCIDENT_FLAGGED:
        if booking_action == 'CANCEL':
            transition(booking, S.CANCELLED, actor=actor, request=request,
                       cancellation_reason='Cancelled following incident review.')
        else:
            others = IncidentRecord.objects.filter(booking=booking).exclude(pk=incident.pk) \
                .exclude(status__in=[IncidentStatus.RESOLVED, IncidentStatus.CLOSED]) \
                .filter(priority__in=[IncidentPriority.CRITICAL, IncidentPriority.HIGH])
            if others.exists():
                raise DomainError('OPEN_INCIDENTS', 'Other critical/high incidents are still open on this booking.')
            resume_to = booking.pre_incident_status
            if not resume_to:
                raise DomainError('INVALID_STATE', 'No prior journey state recorded; cancel the booking instead.')
            transition(booking, resume_to, actor=actor, request=request, resume=True, pre_incident_status='')

    previous = {'status': incident.status}
    incident.status = IncidentStatus.RESOLVED
    incident.resolution_notes = resolution_notes
    incident.resolved_at = timezone.now()
    incident.save()
    record_audit(actor=actor, action='INCIDENT_RESOLVED', resource_type='IncidentRecord',
                 resource_id=incident.id, previous=previous,
                 new={'status': incident.status, 'booking_action': booking_action}, request=request)
    return incident
