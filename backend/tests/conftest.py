"""
Shared fixtures. Rate card amounts here are TEST FIXTURES ONLY and are not
product pricing; production pricing is entered by an admin.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.companions.models import CarePartnerProfile, CarePartnerStatus, Vehicle
from apps.pricing import services as pricing
from apps.users.models import CustomerProfile, User, UserRole

ALL_MOBILITY = ['INDEPENDENT', 'WALKER_ASSISTANCE', 'FOLDING_WHEELCHAIR', 'COMPANION_ONLY']


def make_client(user=None):
    c = APIClient()
    if user is not None:
        c.force_authenticate(user=user)
    return c


@pytest.fixture
def admin(db):
    return User.objects.create_user('+919000000001', role=UserRole.ADMIN, first_name='Ada', firebase_uid='f-admin')


def _customer(phone, uid, name='Cust'):
    u = User.objects.create_user(phone, role=UserRole.CUSTOMER, first_name=name, firebase_uid=uid)
    CustomerProfile.objects.create(user=u, emergency_contact_name='Em', emergency_contact_phone='+919111111111',
                                   emergency_contact_relation='Son', accessibility_notes='uses walker')
    return u


@pytest.fixture
def customer(db):
    return _customer('+919000000002', 'f-cust')


@pytest.fixture
def other_customer(db):
    return _customer('+919000000003', 'f-cust2', 'Other')


def _partner(phone, uid, *, approved=True, vehicle=True, verified=True, name='Pat'):
    u = User.objects.create_user(phone, role=UserRole.CARE_PARTNER, first_name=name, firebase_uid=uid)
    p = CarePartnerProfile.objects.create(
        user=u, status=CarePartnerStatus.APPROVED if approved else CarePartnerStatus.PENDING_VERIFICATION)
    if vehicle:
        Vehicle.objects.create(care_partner=p, registration_number=f'KA01{uid[-4:].upper()}', make='Maruti',
                               model='Ertiga', vehicle_type='SUV', supported_mobility=ALL_MOBILITY,
                               is_verified=verified)
    return u, p


@pytest.fixture
def partner(db):
    return _partner('+919000000004', 'f-part-1')


@pytest.fixture
def partner2(db):
    return _partner('+919000000005', 'f-part-2', name='Quinn')


@pytest.fixture
def rate_card(db, admin):
    card = pricing.create_rate_card(
        actor=admin, request=None, name='TEST-ONLY', base_fare=Decimal('100'), base_distance_km=Decimal('4'),
        per_km_rate=Decimal('10'), per_minute_waiting_rate=Decimal('2'),
        mobility_tier_surcharges={'INDEPENDENT': '0', 'WALKER_ASSISTANCE': '50',
                                  'FOLDING_WHEELCHAIR': '150', 'COMPANION_ONLY': '0'},
        effective_from=timezone.now() - timedelta(days=1))
    return pricing.activate_rate_card(card, actor=admin, request=None)


def booking_payload(**over):
    p = {
        'pickup_address': '12 Test Street', 'pickup_latitude': '17.385000', 'pickup_longitude': '78.486700',
        'hospital_name': 'Test Hospital', 'hospital_address': '1 Hospital Road',
        'hospital_latitude': '17.440000', 'hospital_longitude': '78.348900',
        'scheduled_pickup_time': (timezone.now() + timedelta(hours=3)).isoformat(),
        'mobility_requirement': 'WALKER_ASSISTANCE', 'is_round_trip': True,
    }
    p.update(over)
    return p


@pytest.fixture
def payload():
    return booking_payload
