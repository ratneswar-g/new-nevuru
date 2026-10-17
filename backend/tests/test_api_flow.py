import json
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.conf import settings
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.bookings.models import Booking, OTPChallenge
from apps.companions.models import CarePartnerProfile
from apps.core.geo import haversine_km
from apps.pricing.models import RateCard
from apps.pricing.services import compute_fare
from apps.users.models import User

from .conftest import booking_payload, make_client

API = '/api/v1'
pytestmark = pytest.mark.django_db


def _create_confirmed(customer, payload_over=None):
    c = make_client(customer)
    r = c.post(f'{API}/bookings/', booking_payload(**(payload_over or {})), format='json')
    assert r.status_code == 201, r.content
    bid = r.json()['id']
    assert c.post(f'{API}/bookings/{bid}/confirm/').status_code == 200
    return c, bid


def _assigned(customer, admin, partner_profile, **over):
    c, bid = _create_confirmed(customer, over)
    r = make_client(admin).post(f'{API}/admin/bookings/{bid}/assign/',
                                {'care_partner_id': str(partner_profile.id)}, format='json')
    assert r.status_code == 200, r.content
    return c, bid


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for i in obj:
            yield from _keys(i)


# ------------------------------------------------------------------ registration

class TestRegistration:
    def _post(self, body, claims):
        with patch('firebase_admin.auth.verify_id_token', return_value=claims):
            return make_client().post(f'{API}/auth/register/', body, format='json',
                                      HTTP_AUTHORIZATION='Bearer tok')

    def test_creates_customer_with_phone_from_token(self):
        r = self._post({'role': 'CUSTOMER', 'first_name': 'Asha', 'phone_number': '+910000000000'},
                       {'uid': 'u1', 'phone_number': '+919800000001'})
        assert r.status_code == 201
        assert r.json()['phone_number'] == '+919800000001'
        assert User.objects.get(firebase_uid='u1').role == 'CUSTOMER'

    def test_admin_role_cannot_be_self_assigned(self):
        r = self._post({'role': 'ADMIN', 'first_name': 'X'}, {'uid': 'u2', 'phone_number': '+919800000002'})
        assert r.status_code == 400
        assert not User.objects.filter(firebase_uid='u2').exists()

    def test_care_partner_starts_pending(self):
        r = self._post({'role': 'CARE_PARTNER', 'first_name': 'P'}, {'uid': 'u3', 'phone_number': '+919800000003'})
        assert r.status_code == 201
        assert CarePartnerProfile.objects.get(user__firebase_uid='u3').status == 'PENDING_VERIFICATION'

    def test_duplicate_rejected_and_envelope_shape(self):
        claims = {'uid': 'u4', 'phone_number': '+919800000004'}
        self._post({'role': 'CUSTOMER', 'first_name': 'A'}, claims)
        r = self._post({'role': 'CUSTOMER', 'first_name': 'A'}, claims)
        assert r.status_code == 409
        assert set(r.json()['error']) == {'code', 'message', 'details'}
        assert r.json()['error']['code'] == 'ALREADY_REGISTERED'

    def test_missing_token_rejected(self):
        assert make_client().post(f'{API}/auth/register/', {'role': 'CUSTOMER', 'first_name': 'A'},
                                  format='json').status_code in (401, 403)


# ------------------------------------------------------------------ permissions

class TestRolePermissions:
    def test_unauthenticated_blocked(self):
        assert make_client().get(f'{API}/bookings/').status_code in (401, 403)

    def test_customer_cannot_use_admin_or_partner_endpoints(self, customer):
        c = make_client(customer)
        assert c.get(f'{API}/admin/bookings/').status_code == 403
        assert c.post(f'{API}/admin/rate-cards/', {}, format='json').status_code == 403
        assert c.get(f'{API}/partner/bookings/').status_code == 403
        assert c.get(f'{API}/admin/audit-logs/').status_code == 403

    def test_partner_cannot_use_customer_or_admin_endpoints(self, partner):
        c = make_client(partner[0])
        assert c.get(f'{API}/bookings/').status_code == 403
        assert c.get(f'{API}/admin/partners/').status_code == 403

    def test_unapproved_partner_blocked_from_jobs_and_duty(self, db):
        from .conftest import _partner
        u, _ = _partner('+919000000090', 'f-pend', approved=False)
        c = make_client(u)
        assert c.get(f'{API}/partner/bookings/').status_code == 403
        assert c.post(f'{API}/partner/duty/', {'is_online': True}, format='json').status_code == 403
        assert c.get(f'{API}/partner/me/').status_code == 200

    def test_admin_cannot_use_customer_booking_endpoint(self, admin):
        assert make_client(admin).get(f'{API}/bookings/').status_code == 403


# ---------------------------------------------------------------------- pricing

class TestPricing:
    def test_fare_formula_one_way_and_round_trip(self, rate_card):
        one = compute_fare(rate_card, distance_km=Decimal('10'), mobility='WALKER_ASSISTANCE',
                           is_round_trip=False)
        assert (one.base_fare, one.distance_fare, one.mobility_surcharge, one.total_fare) == \
            (Decimal('100.00'), Decimal('60.00'), Decimal('50.00'), Decimal('210.00'))
        rt = compute_fare(rate_card, distance_km=Decimal('10'), mobility='WALKER_ASSISTANCE',
                          is_round_trip=True, waiting_minutes=30)
        assert rt.distance_fare == Decimal('160.00') and rt.waiting_fare == Decimal('60.00')
        assert rt.total_fare == Decimal('370.00')

    def test_no_rate_card_means_no_pricing(self, customer, payload):
        c = make_client(customer)
        r = c.post(f'{API}/bookings/quote/', payload(), format='json')
        assert r.status_code == 503 and r.json()['error']['code'] == 'RATE_CARD_UNAVAILABLE'
        assert c.post(f'{API}/bookings/', payload(), format='json').status_code == 503
        assert Booking.objects.count() == 0

    def test_quote_matches_formula_and_is_stateless(self, customer, rate_card, payload):
        r = make_client(customer).post(f'{API}/bookings/quote/', payload(), format='json')
        assert r.status_code == 200
        d = haversine_km('17.385', '78.4867', '17.44', '78.3489')
        expected = compute_fare(rate_card, distance_km=d, mobility='WALKER_ASSISTANCE', is_round_trip=True)
        assert Decimal(str(r.json()['total_fare'])) == expected.total_fare
        assert r.json()['distance_basis'] == 'STRAIGHT_LINE_ESTIMATE'
        assert Booking.objects.count() == 0

    def test_rate_card_admin_create_and_activate_supersedes(self, admin, rate_card):
        body = {'name': 'v2', 'base_fare': '120', 'base_distance_km': '3', 'per_km_rate': '12',
                'per_minute_waiting_rate': '3', 'effective_from': timezone.now().isoformat(),
                'mobility_tier_surcharges': {'INDEPENDENT': '0', 'WALKER_ASSISTANCE': '60',
                                             'FOLDING_WHEELCHAIR': '160', 'COMPANION_ONLY': '0'}}
        c = make_client(admin)
        r = c.post(f'{API}/admin/rate-cards/', body, format='json')
        assert r.status_code == 201 and r.json()['version'] == rate_card.version + 1
        assert c.post(f'{API}/admin/rate-cards/{r.json()["id"]}/activate/').status_code == 200
        assert RateCard.objects.filter(is_active=True).count() == 1
        rate_card.refresh_from_db()
        assert rate_card.is_active is False and rate_card.effective_to is not None

    def test_rate_card_requires_all_mobility_tiers(self, admin):
        r = make_client(admin).post(f'{API}/admin/rate-cards/', {
            'name': 'bad', 'base_fare': '1', 'base_distance_km': '1', 'per_km_rate': '1',
            'per_minute_waiting_rate': '1', 'effective_from': timezone.now().isoformat(),
            'mobility_tier_surcharges': {'INDEPENDENT': '0'}}, format='json')
        assert r.status_code == 400

    def test_old_booking_keeps_its_rate_card(self, customer, admin, rate_card, payload):
        c, bid = _create_confirmed(customer)
        from apps.pricing.services import activate_rate_card, create_rate_card
        v2 = create_rate_card(actor=admin, request=None, name='v2', base_fare=Decimal('999'),
                              base_distance_km=Decimal('1'), per_km_rate=Decimal('1'),
                              per_minute_waiting_rate=Decimal('1'),
                              mobility_tier_surcharges={k: '0' for k in
                                                        ['INDEPENDENT', 'WALKER_ASSISTANCE',
                                                         'FOLDING_WHEELCHAIR', 'COMPANION_ONLY']},
                              effective_from=timezone.now())
        activate_rate_card(v2, actor=admin, request=None)
        assert c.get(f'{API}/bookings/{bid}/').json()['rate_card_version'] == rate_card.version


# --------------------------------------------------------------- booking basics

class TestBookingCreation:
    def test_profile_required(self, db, rate_card, payload):
        u = User.objects.create_user('+919000000077', role='CUSTOMER', firebase_uid='f-np')
        r = make_client(u).post(f'{API}/bookings/', payload(), format='json')
        assert r.status_code == 422 and r.json()['error']['code'] == 'PROFILE_INCOMPLETE'

    def test_past_pickup_rejected(self, customer, rate_card, payload):
        r = make_client(customer).post(f'{API}/bookings/', payload(
            scheduled_pickup_time=(timezone.now() - timezone.timedelta(hours=1)).isoformat()), format='json')
        assert r.status_code == 400

    def test_client_cannot_set_status_or_fare(self, customer, rate_card, payload):
        r = make_client(customer).post(f'{API}/bookings/', payload(
            status='COMPLETED', quoted_fare='1.00', care_partner='x'), format='json')
        assert r.status_code == 201
        body = r.json()
        assert body['status'] == 'QUOTED' and Decimal(str(body['quoted_fare'])) > Decimal('1')

    def test_customers_cannot_see_each_others_bookings(self, customer, other_customer, rate_card):
        _, bid = _create_confirmed(customer)
        assert make_client(other_customer).get(f'{API}/bookings/{bid}/').status_code == 404
        assert make_client(other_customer).post(f'{API}/bookings/{bid}/cancel/').status_code == 404
        assert make_client(other_customer).get(f'{API}/bookings/').json()['count'] == 0


# --------------------------------------------------------------- full journey

class TestJourney:
    def test_full_round_trip_happy_path(self, customer, admin, partner, rate_card):
        user, prof = partner
        c, bid = _assigned(customer, admin, prof)
        p = make_client(user)

        assert p.post(f'{API}/partner/bookings/{bid}/arrive/').json()['status'] == 'ARRIVED'

        # Customer generates pickup code; partner enters it.
        issued = c.post(f'{API}/bookings/{bid}/otp/pickup/').json()
        code = issued['code']
        assert len(code) == 4 and code.isdigit()
        r = p.post(f'{API}/partner/bookings/{bid}/verify-pickup/', {'code': code}, format='json')
        assert r.status_code == 200 and r.json()['status'] == 'IN_TRANSIT_HOSPITAL'
        assert r.json()['pickup_verified'] is True

        assert p.post(f'{API}/partner/bookings/{bid}/arrive-hospital/').json()['status'] == 'ACCOMPANIMENT'
        assert p.post(f'{API}/partner/bookings/{bid}/start-return/', {'notes': 'Cleared OPD'},
                      format='json').json()['status'] == 'RETURN_TRANSIT'

        code2 = c.post(f'{API}/bookings/{bid}/otp/dropoff/').json()['code']
        r = p.post(f'{API}/partner/bookings/{bid}/complete/', {'code': code2}, format='json')
        assert r.status_code == 200 and r.json()['status'] == 'COMPLETED'

        b = Booking.objects.get(pk=bid)
        assert b.final_fare is not None and b.final_fare >= b.quoted_fare
        prof.refresh_from_db()
        assert prof.completed_trips_count == 1
        assert make_client(admin).post(f'{API}/admin/bookings/{bid}/close/').json()['status'] == 'CLOSED'

        actions = set(AuditLog.objects.filter(resource_id=bid).values_list('action', flat=True))
        assert {'BOOKING_CREATED', 'BOOKING_STATUS_CHANGED', 'OTP_ISSUED', 'OTP_VERIFIED'} <= actions
        assert AuditLog.objects.filter(action='BOOKING_STATUS_CHANGED', resource_id=bid).count() >= 9

    def test_one_way_trip_completes_from_accompaniment(self, customer, admin, partner, rate_card):
        user, prof = partner
        c, bid = _assigned(customer, admin, prof, is_round_trip=False)
        p = make_client(user)
        p.post(f'{API}/partner/bookings/{bid}/arrive/')
        p.post(f'{API}/partner/bookings/{bid}/verify-pickup/',
               {'code': c.post(f'{API}/bookings/{bid}/otp/pickup/').json()['code']}, format='json')
        p.post(f'{API}/partner/bookings/{bid}/arrive-hospital/')
        assert p.post(f'{API}/partner/bookings/{bid}/start-return/').status_code == 409  # no return leg
        code = c.post(f'{API}/bookings/{bid}/otp/dropoff/').json()['code']
        assert p.post(f'{API}/partner/bookings/{bid}/complete/', {'code': code},
                      format='json').json()['status'] == 'COMPLETED'

    def test_server_rejects_skipped_and_out_of_order_steps(self, customer, admin, partner, rate_card):
        user, prof = partner
        c, bid = _assigned(customer, admin, prof)
        p = make_client(user)
        for path in ('arrive-hospital', 'start-return'):
            r = p.post(f'{API}/partner/bookings/{bid}/{path}/')
            assert r.status_code == 409 and r.json()['error']['code'] == 'INVALID_TRANSITION'
        assert p.post(f'{API}/partner/bookings/{bid}/verify-pickup/', {'code': '1234'},
                      format='json').status_code == 409
        assert p.post(f'{API}/partner/bookings/{bid}/complete/', {'code': '1234'},
                      format='json').status_code == 409
        assert c.post(f'{API}/bookings/{bid}/otp/pickup/').status_code == 409  # partner not arrived yet
        assert Booking.objects.get(pk=bid).status == 'ASSIGNED'

    def test_customer_cannot_cancel_after_arrival(self, customer, admin, partner, rate_card):
        user, prof = partner
        c, bid = _assigned(customer, admin, prof)
        make_client(user).post(f'{API}/partner/bookings/{bid}/arrive/')
        assert c.post(f'{API}/bookings/{bid}/cancel/').status_code == 409
        assert make_client(admin).post(f'{API}/admin/bookings/{bid}/cancel/', {'reason': 'ops'},
                                       format='json').json()['status'] == 'CANCELLED'

    def test_terminal_states_are_final(self, customer, admin, rate_card):
        c, bid = _create_confirmed(customer)
        assert c.post(f'{API}/bookings/{bid}/cancel/').status_code == 200
        assert c.post(f'{API}/bookings/{bid}/confirm/').status_code == 409
        assert make_client(admin).post(f'{API}/admin/bookings/{bid}/close/').status_code == 409

    def test_partner_cannot_touch_another_partners_booking(self, customer, admin, partner, partner2, rate_card):
        _, prof = partner
        _, bid = _assigned(customer, admin, prof)
        other = make_client(partner2[0])
        assert other.get(f'{API}/partner/bookings/{bid}/').status_code == 404
        assert other.post(f'{API}/partner/bookings/{bid}/arrive/').status_code == 404


# --------------------------------------------------------------------- OTP

class TestOtpSecurity:
    def _to_arrived(self, customer, admin, partner):
        user, prof = partner
        c, bid = _assigned(customer, admin, prof)
        p = make_client(user)
        p.post(f'{API}/partner/bookings/{bid}/arrive/')
        return c, p, bid

    def test_otp_never_exposed_to_partner_or_stored_plaintext(self, customer, admin, partner, rate_card):
        c, p, bid = self._to_arrived(customer, admin, partner)
        with patch('apps.bookings.services.secrets.randbelow', return_value=7391):
            code = c.post(f'{API}/bookings/{bid}/otp/pickup/').json()['code']
        assert code == '7391'

        responses = [p.get(f'{API}/partner/bookings/{bid}/'), p.get(f'{API}/partner/bookings/'),
                     p.get(f'{API}/partner/me/'), p.post(f'{API}/partner/bookings/{bid}/verify-pickup/',
                                                         {'code': '0000'}, format='json')]
        for r in responses:
            body = json.dumps(r.json())
            assert '7391' not in body
            assert not any('otp' in k.lower() or 'hash' in k.lower() for k in _keys(r.json())), body

        ch = OTPChallenge.objects.get(booking_id=bid)
        assert ch.otp_hash != '7391' and '7391' not in ch.otp_hash and len(ch.otp_hash) == 64
        # customer detail view also never carries the code
        assert '7391' not in json.dumps(c.get(f'{API}/bookings/{bid}/').json())

    def test_wrong_attempts_persist_and_lock(self, customer, admin, partner, rate_card):
        c, p, bid = self._to_arrived(customer, admin, partner)
        with patch('apps.bookings.services.secrets.randbelow', return_value=4321):
            c.post(f'{API}/bookings/{bid}/otp/pickup/')
        url = f'{API}/partner/bookings/{bid}/verify-pickup/'
        r = p.post(url, {'code': '1111'}, format='json')
        assert r.status_code == 400 and r.json()['error']['details']['attempts_remaining'] == 2
        assert OTPChallenge.objects.get(booking_id=bid).attempts_remaining == 2  # decrement committed
        p.post(url, {'code': '2222'}, format='json')
        r = p.post(url, {'code': '3333'}, format='json')
        assert r.json()['error']['details']['attempts_remaining'] == 0
        r = p.post(url, {'code': '4321'}, format='json')  # correct code, but locked
        assert r.status_code == 423 and r.json()['error']['code'] == 'OTP_LOCKED'
        assert Booking.objects.get(pk=bid).status == 'ARRIVED'

        # customer issues a fresh code -> flow recovers; old code is dead
        with patch('apps.bookings.services.secrets.randbelow', return_value=5555):
            c.post(f'{API}/bookings/{bid}/otp/pickup/')
        assert p.post(url, {'code': '4321'}, format='json').status_code == 400
        assert p.post(url, {'code': '5555'}, format='json').status_code == 200

    def test_expired_otp_rejected(self, customer, admin, partner, rate_card):
        c, p, bid = self._to_arrived(customer, admin, partner)
        code = c.post(f'{API}/bookings/{bid}/otp/pickup/').json()['code']
        OTPChallenge.objects.filter(booking_id=bid).update(expires_at=timezone.now() - timezone.timedelta(seconds=1))
        r = p.post(f'{API}/partner/bookings/{bid}/verify-pickup/', {'code': code}, format='json')
        assert r.status_code == 410 and r.json()['error']['code'] == 'OTP_EXPIRED'

    def test_no_code_issued_and_malformed_code(self, customer, admin, partner, rate_card):
        _, p, bid = self._to_arrived(customer, admin, partner)
        url = f'{API}/partner/bookings/{bid}/verify-pickup/'
        assert p.post(url, {'code': '1234'}, format='json').json()['error']['code'] == 'OTP_NOT_ISSUED'
        assert p.post(url, {'code': 'abcd'}, format='json').status_code == 400
        assert p.post(url, {}, format='json').status_code == 400

    def test_partner_cannot_issue_otp_and_stranger_customer_cannot(self, customer, other_customer,
                                                                  admin, partner, rate_card):
        c, p, bid = self._to_arrived(customer, admin, partner)
        assert p.post(f'{API}/bookings/{bid}/otp/pickup/').status_code == 403
        assert make_client(other_customer).post(f'{API}/bookings/{bid}/otp/pickup/').status_code == 404

    def test_audit_never_contains_otp_value(self, customer, admin, partner, rate_card):
        c, p, bid = self._to_arrived(customer, admin, partner)
        with patch('apps.bookings.services.secrets.randbelow', return_value=6208):
            c.post(f'{API}/bookings/{bid}/otp/pickup/')
        p.post(f'{API}/partner/bookings/{bid}/verify-pickup/', {'code': '6208'}, format='json')
        blob = json.dumps(list(AuditLog.objects.values('new_state', 'previous_state')), default=str)
        assert '6208' not in blob


# --------------------------------------------------------------- assignment

class TestAssignment:
    def test_only_admin_assigns(self, customer, partner, rate_card):
        c, bid = _create_confirmed(customer)
        r = c.post(f'{API}/admin/bookings/{bid}/assign/', {'care_partner_id': str(partner[1].id)}, format='json')
        assert r.status_code == 403
        assert make_client(partner[0]).post(f'{API}/admin/bookings/{bid}/assign/', {}, format='json').status_code == 403

    def test_unapproved_or_unverified_vehicle_partner_rejected(self, customer, admin, rate_card):
        from .conftest import _partner
        _, pending = _partner('+919000000081', 'f-pe81', approved=False)
        _, noveh = _partner('+919000000082', 'f-nv82', vehicle=False)
        _, unver = _partner('+919000000083', 'f-uv83', verified=False)
        _, bid = _create_confirmed(customer)
        a = make_client(admin)
        for prof in (pending, noveh, unver):
            r = a.post(f'{API}/admin/bookings/{bid}/assign/', {'care_partner_id': str(prof.id)}, format='json')
            assert r.status_code == 409 and r.json()['error']['code'] == 'PARTNER_NOT_ELIGIBLE'
        assert Booking.objects.get(pk=bid).status == 'CONFIRMED'

    def test_vehicle_must_support_mobility_need(self, customer, admin, partner, rate_card):
        partner[1].vehicles.update(supported_mobility=['INDEPENDENT'])
        _, bid = _create_confirmed(customer)
        r = make_client(admin).post(f'{API}/admin/bookings/{bid}/assign/',
                                    {'care_partner_id': str(partner[1].id)}, format='json')
        assert r.json()['error']['code'] == 'PARTNER_NOT_ELIGIBLE'

    def test_busy_partner_rejected_and_reassign_before_arrival(self, customer, admin, partner, partner2, rate_card):
        _, bid1 = _assigned(customer, admin, partner[1])
        _, bid2 = _create_confirmed(customer)
        a = make_client(admin)
        r = a.post(f'{API}/admin/bookings/{bid2}/assign/', {'care_partner_id': str(partner[1].id)}, format='json')
        assert r.json()['error']['code'] == 'PARTNER_BUSY'
        r = a.post(f'{API}/admin/bookings/{bid1}/assign/', {'care_partner_id': str(partner2[1].id)}, format='json')
        assert r.status_code == 200 and r.json()['care_partner_id'] == str(partner2[1].id)
        assert AuditLog.objects.filter(action='BOOKING_PARTNER_REASSIGNED', resource_id=bid1).exists()
        assert make_client(partner[0]).get(f'{API}/partner/bookings/{bid1}/').status_code == 404

    def test_cannot_assign_unconfirmed_booking(self, customer, admin, partner, rate_card):
        c = make_client(customer)
        bid = c.post(f'{API}/bookings/', booking_payload(), format='json').json()['id']  # QUOTED only
        r = make_client(admin).post(f'{API}/admin/bookings/{bid}/assign/',
                                    {'care_partner_id': str(partner[1].id)}, format='json')
        assert r.status_code == 409


# ------------------------------------------------------- partner onboarding admin

class TestPartnerOnboarding:
    def test_approval_flow_and_online_requires_verified_vehicle(self, admin, db):
        from .conftest import _partner
        u, prof = _partner('+919000000070', 'f-onb0', approved=False, verified=False)
        pc, a = make_client(u), make_client(admin)
        assert pc.post(f'{API}/partner/kyc/', {'document_type': 'AADHAAR', 'document_identifier': 'XXXX'},
                       format='json').status_code == 204
        assert a.post(f'{API}/admin/partners/{prof.id}/approve/').json()['status'] == 'APPROVED'
        # real requests load the user fresh; force_authenticate reuses a cached instance
        pc = make_client(User.objects.get(pk=u.pk))
        assert pc.post(f'{API}/partner/duty/', {'is_online': True}, format='json').status_code == 409
        vid = prof.vehicles.first().id
        assert a.post(f'{API}/admin/vehicles/{vid}/verify/').json()['is_verified'] is True
        assert pc.post(f'{API}/partner/duty/', {'is_online': True}, format='json').json() == {'is_online': True}
        a.post(f'{API}/admin/partners/{prof.id}/suspend/')
        prof.refresh_from_db()
        assert prof.status == 'SUSPENDED' and prof.is_online is False

    def test_partner_cannot_self_verify_vehicle(self, partner):
        c = make_client(partner[0])
        r = c.post(f'{API}/partner/vehicles/', {
            'registration_number': 'TS09ZZ9999', 'make': 'Tata', 'model': 'X', 'vehicle_type': 'SEDAN',
            'supported_mobility': ['INDEPENDENT'], 'is_verified': True}, format='json')
        assert r.status_code == 201 and r.json()['is_verified'] is False


# --------------------------------------------------------- emergency / incidents

class TestEmergency:
    def _in_transit(self, customer, admin, partner):
        user, prof = partner
        c, bid = _assigned(customer, admin, prof)
        p = make_client(user)
        p.post(f'{API}/partner/bookings/{bid}/arrive/')
        p.post(f'{API}/partner/bookings/{bid}/verify-pickup/',
               {'code': c.post(f'{API}/bookings/{bid}/otp/pickup/').json()['code']}, format='json')
        return c, p, bid

    def test_customer_sos_flags_booking_and_gives_108_112_guidance(self, customer, admin, partner, rate_card):
        c, p, bid = self._in_transit(customer, admin, partner)
        r = c.post(f'{API}/bookings/{bid}/emergency/', {'narrative': 'Feeling unwell'}, format='json')
        assert r.status_code == 201
        assert r.json()['incident']['priority'] == 'CRITICAL'
        assert '108' in r.json()['guidance'] and 'not an ambulance' in r.json()['guidance']
        b = Booking.objects.get(pk=bid)
        assert b.status == 'INCIDENT_FLAGGED' and b.pre_incident_status == 'IN_TRANSIT_HOSPITAL'
        # journey is frozen while flagged
        assert p.post(f'{API}/partner/bookings/{bid}/arrive-hospital/').status_code == 409

    def test_partner_sos_and_admin_resume(self, customer, admin, partner, rate_card):
        c, p, bid = self._in_transit(customer, admin, partner)
        inc = p.post(f'{API}/partner/bookings/{bid}/emergency/', {}, format='json').json()['incident']
        a = make_client(admin)
        listed = a.get(f'{API}/admin/incidents/?priority=CRITICAL').json()
        assert listed['count'] == 1 and listed['results'][0]['id'] == inc['id']
        assert p.post(f'{API}/admin/incidents/{inc["id"]}/resolve/', {'resolution_notes': 'x'}, format='json'
                      ).status_code == 403
        r = a.post(f'{API}/admin/incidents/{inc["id"]}/resolve/',
                   {'resolution_notes': 'Family contacted, patient fine', 'booking_action': 'RESUME'}, format='json')
        assert r.status_code == 200 and r.json()['status'] == 'RESOLVED'
        assert Booking.objects.get(pk=bid).status == 'IN_TRANSIT_HOSPITAL'
        assert p.post(f'{API}/partner/bookings/{bid}/arrive-hospital/').status_code == 200

    def test_admin_cancel_resolution(self, customer, admin, partner, rate_card):
        c, p, bid = self._in_transit(customer, admin, partner)
        inc = c.post(f'{API}/bookings/{bid}/emergency/', {}, format='json').json()['incident']
        make_client(admin).post(f'{API}/admin/incidents/{inc["id"]}/resolve/',
                                {'resolution_notes': 'Diverted to ER', 'booking_action': 'CANCEL'}, format='json')
        assert Booking.objects.get(pk=bid).status == 'CANCELLED'

    def test_non_emergency_report_does_not_freeze_journey(self, customer, admin, partner, rate_card):
        c, p, bid = self._in_transit(customer, admin, partner)
        r = p.post(f'{API}/partner/bookings/{bid}/incidents/', {'category': 'UNEXPECTED_DELAY',
                   'narrative': 'Traffic', 'priority': 'LOW'}, format='json')
        assert r.status_code == 201
        assert Booking.objects.get(pk=bid).status == 'IN_TRANSIT_HOSPITAL'

    def test_outsider_cannot_raise_incident(self, customer, other_customer, admin, partner, rate_card):
        c, p, bid = self._in_transit(customer, admin, partner)
        assert make_client(other_customer).post(f'{API}/bookings/{bid}/emergency/', {}, format='json'
                                                ).status_code == 404

    def test_emergency_before_assignment_records_incident_without_state_change(self, customer, rate_card):
        c, bid = _create_confirmed(customer)
        assert c.post(f'{API}/bookings/{bid}/emergency/', {}, format='json').status_code == 201
        assert Booking.objects.get(pk=bid).status == 'CONFIRMED'


# ----------------------------------------------------------------- family helper

class TestFamilyHelper:
    def test_helper_visibility_and_booking_rights(self, customer, other_customer, rate_card):
        c = make_client(customer)
        r = c.post(f'{API}/me/family-helpers/', {'helper_phone_number': other_customer.phone_number,
                                                 'can_book': False, 'can_view_live_status': True}, format='json')
        assert r.status_code == 201
        _, bid = _create_confirmed(customer)
        h = make_client(other_customer)
        assert h.get(f'{API}/bookings/{bid}/').status_code == 200          # live status granted
        assert h.post(f'{API}/bookings/{bid}/cancel/').status_code == 404  # no can_book
        r = h.post(f'{API}/bookings/', booking_payload(customer_id=str(customer.id)), format='json')
        assert r.status_code == 403
        c.post(f'{API}/me/family-helpers/', {'helper_phone_number': other_customer.phone_number,
                                             'can_book': True}, format='json')
        r = h.post(f'{API}/bookings/', booking_payload(customer_id=str(customer.id)), format='json')
        assert r.status_code == 201 and r.json()['customer_id'] == str(customer.id)

    def test_revoke(self, customer, other_customer):
        c = make_client(customer)
        gid = c.post(f'{API}/me/family-helpers/', {'helper_phone_number': other_customer.phone_number},
                     format='json').json()['id']
        assert c.delete(f'{API}/me/family-helpers/{gid}/').status_code == 204
        assert c.get(f'{API}/me/family-helpers/').json()['count'] == 0


# ------------------------------------------------------------------------ audit

class TestAudit:
    def test_audit_log_is_append_only(self, admin):
        from apps.audit.services import record_audit
        entry = record_audit(actor=admin, action='X', resource_type='T', resource_id=admin.id)
        entry.action = 'Y'
        with pytest.raises(PermissionError):
            entry.save()
        with pytest.raises(PermissionError):
            entry.delete()
        with pytest.raises(PermissionError):
            AuditLog.objects.all().update(action='Z')
        with pytest.raises(PermissionError):
            AuditLog.objects.all().delete()

    def test_admin_can_read_audit_without_ip(self, admin, customer, rate_card):
        _create_confirmed(customer)
        r = make_client(admin).get(f'{API}/admin/audit-logs/?action=BOOKING_CREATED')
        assert r.status_code == 200 and r.json()['count'] == 1
        assert 'ip_address' not in r.json()['results'][0]

    def test_rate_card_actions_audited(self, rate_card):
        assert AuditLog.objects.filter(action='RATE_CARD_ACTIVATED').exists()


class TestSettingsSafety:
    def test_default_auth_is_firebase_and_no_open_default(self):
        rf = settings.REST_FRAMEWORK
        assert rf['DEFAULT_AUTHENTICATION_CLASSES'] == ['apps.users.authentication.FirebaseAuthentication']
        assert rf['DEFAULT_PERMISSION_CLASSES'] == ['rest_framework.permissions.IsAuthenticated']
