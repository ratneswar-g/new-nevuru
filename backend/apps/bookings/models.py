import uuid
from django.conf import settings
from django.db import models
from apps.users.models import MobilityRequirement


class BookingStatus(models.TextChoices):
    REQUESTED = 'REQUESTED', 'Requested'
    QUOTED = 'QUOTED', 'Quoted'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    ASSIGNED = 'ASSIGNED', 'Assigned'
    ARRIVED = 'ARRIVED', 'Arrived at Pickup'
    IN_TRANSIT_HOSPITAL = 'IN_TRANSIT_HOSPITAL', 'In Transit to Hospital'
    ACCOMPANIMENT = 'ACCOMPANIMENT', 'Hospital Accompaniment'
    RETURN_TRANSIT = 'RETURN_TRANSIT', 'Return Transit'
    COMPLETED = 'COMPLETED', 'Completed'
    CLOSED = 'CLOSED', 'Closed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    INCIDENT_FLAGGED = 'INCIDENT_FLAGGED', 'Incident Flagged'


class OTPChallengeType(models.TextChoices):
    PICKUP = 'PICKUP', 'Pickup Doorstep Verification'
    DROPOFF = 'DROPOFF', 'Drop-off Completion Verification'


class Booking(models.Model):
    """
    Primary entity representing an assisted medical journey.
    Sole owner of the Care Partner assignment relationship.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the booking'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='bookings',
        help_text='Primary customer / patient account'
    )
    care_partner = models.ForeignKey(
        'companions.CarePartnerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bookings',
        help_text='Assigned Care Partner companion (sole ownership)'
    )
    status = models.CharField(
        max_length=30,
        choices=BookingStatus.choices,
        default=BookingStatus.REQUESTED,
        db_index=True,
        help_text='Current authoritative journey state'
    )
    
    # Pickup details
    pickup_address = models.TextField(help_text='Doorstep pickup street address')
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_landmark = models.CharField(max_length=150, blank=True)

    # Hospital destination details
    hospital_name = models.CharField(max_length=150, help_text='Name of hospital or healthcare clinic')
    hospital_address = models.TextField(help_text='Hospital campus destination address')
    hospital_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    hospital_longitude = models.DecimalField(max_digits=9, decimal_places=6)

    # Journey schedule and mobility
    scheduled_pickup_time = models.DateTimeField(
        db_index=True,
        help_text='Scheduled doorstep departure time'
    )
    mobility_requirement = models.CharField(
        max_length=30,
        choices=MobilityRequirement.choices,
        default=MobilityRequirement.INDEPENDENT,
        help_text='Patient mobility requirement profile'
    )
    is_round_trip = models.BooleanField(
        default=True,
        help_text='Indicates if return journey accompaniment is included'
    )

    # Pricing and rate card association
    rate_card = models.ForeignKey(
        'pricing.RateCard',
        on_delete=models.PROTECT,
        related_name='bookings',
        help_text='Rate card rule applied to this booking'
    )
    quoted_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Authoritative quoted fare in INR'
    )
    final_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Final settled fare in INR after completion'
    )
    currency = models.CharField(
        max_length=3,
        default='INR',
        help_text='ISO currency code (fixed to INR)'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-scheduled_pickup_time']

    def __str__(self):
        return f"Booking {self.id}: {self.customer.phone_number} -> {self.hospital_name} [{self.status}]"


class OTPChallenge(models.Model):
    """
    Stores cryptographically hashed 4-digit verification OTPs for doorstep handover.
    Never stores plaintext OTP values. Inaccessible to Care Partner models or APIs.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='otp_challenges',
        help_text='Associated booking'
    )
    challenge_type = models.CharField(
        max_length=10,
        choices=OTPChallengeType.choices,
        default=OTPChallengeType.PICKUP,
        help_text='Stage of OTP verification: PICKUP or DROPOFF'
    )
    otp_hash = models.CharField(
        max_length=128,
        help_text='Cryptographic hash of the 4-digit OTP. Never plaintext.'
    )
    expires_at = models.DateTimeField(
        help_text='Expiration timestamp after which OTP challenge becomes invalid'
    )
    attempts_remaining = models.PositiveSmallIntegerField(
        default=3,
        help_text='Remaining failed attempts allowed before challenge locks'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when Care Partner correctly verified the OTP'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'OTP Challenge'
        verbose_name_plural = 'OTP Challenges'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTPChallenge {self.challenge_type} for Booking {self.booking_id} (Verified: {bool(self.verified_at)})"
