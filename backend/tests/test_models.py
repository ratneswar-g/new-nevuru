import uuid
from decimal import Decimal
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.auth import get_user_model
import pytest

from apps.users.models import UserRole, MobilityRequirement, CustomerProfile, FamilyHelper
from apps.companions.models import CarePartnerProfile, CarePartnerStatus, Vehicle, VehicleType, CarePartnerDocument
from apps.pricing.models import RateCard
from apps.bookings.models import Booking, BookingStatus, OTPChallenge, OTPChallengeType
from apps.journeys.models import AccompanimentSession
from apps.incidents.models import IncidentRecord, IncidentPriority, IncidentStatus
from apps.audit.models import AuditLog

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_customer_user(self):
        user = User.objects.create_user(
            phone_number='+919876543210',
            first_name='Ananya',
            last_name='Sharma',
            role=UserRole.CUSTOMER
        )
        assert isinstance(user.id, uuid.UUID)
        assert user.phone_number == '+919876543210'
        assert user.role == UserRole.CUSTOMER
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.created_at is not None

    def test_phone_number_unique_constraint(self):
        User.objects.create_user(phone_number='+919876543211', role=UserRole.CUSTOMER)
        with pytest.raises(IntegrityError):
            User.objects.create_user(phone_number='+919876543211', role=UserRole.CUSTOMER)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            phone_number='+919999999999',
            password='TestAdminSecurePassword123!'
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == UserRole.ADMIN
        assert admin.check_password('TestAdminSecurePassword123!') is True


@pytest.mark.django_db
class TestCustomerAndHelperModels:
    def test_customer_profile_creation(self):
        user = User.objects.create_user(phone_number='+919123456780', role=UserRole.CUSTOMER)
        profile = CustomerProfile.objects.create(
            user=user,
            emergency_contact_name='Rohan Sharma',
            emergency_contact_phone='+919123456789',
            emergency_contact_relation='Son',
            default_mobility_need=MobilityRequirement.FOLDING_WHEELCHAIR,
            accessibility_notes='Uses folding wheelchair; needs arm support when standing.'
        )
        assert profile.user == user
        assert profile.default_mobility_need == MobilityRequirement.FOLDING_WHEELCHAIR
        assert profile.emergency_contact_relation == 'Son'

    def test_family_helper_granular_permissions(self):
        patient = User.objects.create_user(phone_number='+919123456781', role=UserRole.CUSTOMER)
        helper = User.objects.create_user(phone_number='+919123456782', role=UserRole.CUSTOMER)

        link = FamilyHelper.objects.create(
            primary_customer=patient,
            helper_user=helper,
            can_book=True,
            can_view_live_status=True,
            can_view_history=False,
            relationship='Daughter'
        )
        assert link.can_book is True
        assert link.can_view_live_status is True
        assert link.can_view_history is False

        # Verify unique_together constraint
        with pytest.raises(IntegrityError):
            FamilyHelper.objects.create(
                primary_customer=patient,
                helper_user=helper,
                can_book=False
            )


@pytest.mark.django_db
class TestCarePartnerAndVehicleModels:
    def test_care_partner_profile_and_vehicle(self):
        partner_user = User.objects.create_user(phone_number='+919876500001', role=UserRole.CARE_PARTNER)
        profile = CarePartnerProfile.objects.create(
            user=partner_user,
            status=CarePartnerStatus.APPROVED,
            is_online=True
        )
        assert profile.status == CarePartnerStatus.APPROVED
        assert profile.is_online is True

        vehicle = Vehicle.objects.create(
            care_partner=profile,
            registration_number='KA01AB1234',
            make='Maruti Suzuki',
            model='Ertiga',
            vehicle_type=VehicleType.SEDAN,
            seating_capacity=6,
            supported_mobility=[MobilityRequirement.INDEPENDENT, MobilityRequirement.FOLDING_WHEELCHAIR],
            is_verified=True
        )
        assert vehicle.care_partner == profile
        assert vehicle.registration_number == 'KA01AB1234'
        assert MobilityRequirement.FOLDING_WHEELCHAIR in vehicle.supported_mobility


@pytest.mark.django_db
class TestPricingAndRateCard:
    def test_rate_card_versioning(self):
        rc1 = RateCard.objects.create(
            version=1,
            name='Standard Bangalore Baseline',
            base_fare=Decimal('350.00'),
            base_distance_km=Decimal('4.00'),
            per_km_rate=Decimal('25.00'),
            per_minute_waiting_rate=Decimal('3.00'),
            mobility_tier_surcharges={
                MobilityRequirement.INDEPENDENT: '0.00',
                MobilityRequirement.FOLDING_WHEELCHAIR: '100.00'
            },
            effective_from=timezone.now(),
            is_active=True
        )
        assert rc1.version == 1
        assert rc1.base_fare == Decimal('350.00')

        # Version must be unique
        with pytest.raises(IntegrityError):
            RateCard.objects.create(
                version=1,
                name='Duplicate Version Rate Card',
                base_fare=Decimal('400.00'),
                base_distance_km=Decimal('4.00'),
                per_km_rate=Decimal('28.00'),
                per_minute_waiting_rate=Decimal('3.50'),
                effective_from=timezone.now()
            )


@pytest.mark.django_db
class TestBookingJourneyAndIncidentModels:
    def test_booking_sole_assignment_ownership(self):
        customer = User.objects.create_user(phone_number='+919111111111', role=UserRole.CUSTOMER)
        partner_user = User.objects.create_user(phone_number='+919222222222', role=UserRole.CARE_PARTNER)
        partner_profile = CarePartnerProfile.objects.create(user=partner_user, status=CarePartnerStatus.APPROVED)

        rate_card = RateCard.objects.create(
            version=101,
            name='Test Rate Card',
            base_fare=Decimal('300.00'),
            base_distance_km=Decimal('4.00'),
            per_km_rate=Decimal('20.00'),
            per_minute_waiting_rate=Decimal('2.50'),
            effective_from=timezone.now()
        )

        booking = Booking.objects.create(
            customer=customer,
            care_partner=partner_profile,
            status=BookingStatus.ASSIGNED,
            pickup_address='12, 4th Main, Indiranagar, Bengaluru',
            pickup_latitude=Decimal('12.978300'),
            pickup_longitude=Decimal('77.640800'),
            hospital_name='Manipal Hospital HAL Airport Road',
            hospital_address='98, HAL Old Airport Rd, Kodihalli, Bengaluru',
            hospital_latitude=Decimal('12.959200'),
            hospital_longitude=Decimal('77.653400'),
            scheduled_pickup_time=timezone.now(),
            mobility_requirement=MobilityRequirement.FOLDING_WHEELCHAIR,
            rate_card=rate_card,
            quoted_fare=Decimal('550.00')
        )
        assert booking.care_partner == partner_profile
        assert booking.status == BookingStatus.ASSIGNED

        # Test OTP Challenge with cryptographic hash
        otp_challenge = OTPChallenge.objects.create(
            booking=booking,
            challenge_type=OTPChallengeType.PICKUP,
            otp_hash='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
            attempts_remaining=3
        )
        assert otp_challenge.attempts_remaining == 3
        assert len(otp_challenge.otp_hash) == 64

        # Test AccompanimentSession
        session = AccompanimentSession.objects.create(
            booking=booking,
            hospital_arrived_at=timezone.now(),
            accompaniment_started_at=timezone.now(),
            waiting_duration_minutes=45,
            non_clinical_notes='Accompanied patient to 2nd Floor Cardiology OPD; assisted wheelchair navigation.'
        )
        assert session.booking == booking
        assert session.waiting_duration_minutes == 45

        # Test IncidentRecord
        incident = IncidentRecord.objects.create(
            booking=booking,
            reporter=customer,
            category='UNEXPECTED_OPD_DELAY',
            priority=IncidentPriority.MEDIUM,
            status=IncidentStatus.REPORTED,
            narrative='OPD consultation running 40 minutes behind schedule; patient requested extended wait.'
        )
        assert incident.booking == booking
        assert incident.priority == IncidentPriority.MEDIUM


@pytest.mark.django_db
class TestDecoupledAuditLog:
    def test_audit_log_decoupled_entry(self):
        resource_uuid = uuid.uuid4()
        actor_uuid = uuid.uuid4()

        entry = AuditLog.objects.create(
            actor_id=actor_uuid,
            actor_role='ADMIN',
            action='RATE_CARD_ACTIVATED',
            resource_type='RateCard',
            resource_id=resource_uuid,
            previous_state={'is_active': False},
            new_state={'is_active': True},
            ip_address='192.168.1.100'
        )
        assert entry.resource_type == 'RateCard'
        assert entry.resource_id == resource_uuid
        assert entry.action == 'RATE_CARD_ACTIVATED'
        assert entry.new_state['is_active'] is True
