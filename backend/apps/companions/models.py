import uuid
from django.conf import settings
from django.db import models


class CarePartnerStatus(models.TextChoices):
    PENDING_VERIFICATION = 'PENDING_VERIFICATION', 'Pending Verification'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    SUSPENDED = 'SUSPENDED', 'Suspended'


class VehicleType(models.TextChoices):
    SEDAN = 'SEDAN', 'Sedan'
    HATCHBACK = 'HATCHBACK', 'Hatchback'
    SUV = 'SUV', 'SUV'
    WHEELCHAIR_ACCESSIBLE = 'WHEELCHAIR_ACCESSIBLE', 'Wheelchair Accessible Vehicle'


class CarePartnerProfile(models.Model):
    """
    Care Partner profile managing KYC vetting status, duty availability,
    and verified vehicles.
    Booking assignments are owned strictly by the Booking model.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the care partner'
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='care_partner_profile',
        help_text='Associated User account'
    )
    status = models.CharField(
        max_length=30,
        choices=CarePartnerStatus.choices,
        default=CarePartnerStatus.PENDING_VERIFICATION,
        db_index=True,
        help_text='KYC and operational approval status'
    )
    is_online = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Duty toggle indicating field availability'
    )
    completed_trips_count = models.PositiveIntegerField(
        default=0,
        help_text='Total count of completed patient journeys'
    )
    kyc_submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when verification documents were submitted'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when admin approved partner credentials'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Care Partner Profile'
        verbose_name_plural = 'Care Partner Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"CarePartner: {self.user.phone_number} [{self.status}]"


class Vehicle(models.Model):
    """
    Vehicle registered and verified for assisted patient transport.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    care_partner = models.ForeignKey(
        CarePartnerProfile,
        on_delete=models.CASCADE,
        related_name='vehicles',
        help_text='Owner Care Partner'
    )
    registration_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text='Vehicle license plate number (e.g., KA-01-AB-1234)'
    )
    make = models.CharField(max_length=50, help_text='Manufacturer (e.g., Maruti, Hyundai, Tata)')
    model = models.CharField(max_length=50, help_text='Model name (e.g., Ertiga, WagonR, Innova)')
    color = models.CharField(max_length=30, blank=True)
    vehicle_type = models.CharField(
        max_length=30,
        choices=VehicleType.choices,
        default=VehicleType.SEDAN,
        db_index=True
    )
    seating_capacity = models.PositiveSmallIntegerField(
        default=4,
        help_text='Passenger capacity excluding driver'
    )
    supported_mobility = models.JSONField(
        default=list,
        help_text='Supported mobility types: INDEPENDENT, WALKER_ASSISTANCE, FOLDING_WHEELCHAIR, COMPANION_ONLY'
    )
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Admin physical vehicle and documentation inspection status'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Availability of vehicle for operational dispatch'
    )
    insurance_expiry = models.DateField(null=True, blank=True)
    fitness_expiry = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def __str__(self):
        return f"{self.registration_number} ({self.make} {self.model})"


class CarePartnerDocument(models.Model):
    """
    KYC and compliance documents submitted for Care Partner onboarding inspection.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    care_partner = models.ForeignKey(
        CarePartnerProfile,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=50,
        help_text='Document category: DRIVING_LICENSE, AADHAAR, POLICE_VERIFICATION, VEHICLE_RC'
    )
    document_file = models.FileField(
        upload_to='kyc_documents/',
        blank=True,
        null=True,
        help_text='Encrypted document file reference'
    )
    document_identifier = models.CharField(
        max_length=100,
        blank=True,
        help_text='Government registration or document number'
    )
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Care Partner Document'
        verbose_name_plural = 'Care Partner Documents'

    def __str__(self):
        return f"Doc: {self.document_type} for {self.care_partner.user.phone_number}"
