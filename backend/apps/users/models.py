import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserRole(models.TextChoices):
    CUSTOMER = 'CUSTOMER', 'Customer'
    CARE_PARTNER = 'CARE_PARTNER', 'Care Partner'
    ADMIN = 'ADMIN', 'Admin'


class MobilityRequirement(models.TextChoices):
    INDEPENDENT = 'INDEPENDENT', 'Independent'
    WALKER_ASSISTANCE = 'WALKER_ASSISTANCE', 'Walker Assistance'
    FOLDING_WHEELCHAIR = 'FOLDING_WHEELCHAIR', 'Folding Wheelchair'
    COMPANION_ONLY = 'COMPANION_ONLY', 'Companion Only'


class UserManager(BaseUserManager):
    """
    Custom manager for User model where phone_number is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The phone number must be provided.')
        
        phone_number = str(phone_number).strip()
        extra_fields.setdefault('role', UserRole.CUSTOMER)
        
        email = extra_fields.get('email')
        if email:
            extra_fields['email'] = self.normalize_email(email)
            
        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for Neravu Platform.
    Uses UUID as primary key and phone_number as primary authentication identifier.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the user'
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        help_text='E.164 compliant phone number (primary identifier)'
    )
    firebase_uid = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='Stable Firebase UID linking external auth identity'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text='Optional contact email address'
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text='Given name'
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text='Family name'
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        db_index=True,
        help_text='Platform role (CUSTOMER, CARE_PARTNER, ADMIN)'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user account is active'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into the Django admin site'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when the user account was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when the user account was last updated'
    )

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} ({self.role})"


class CustomerProfile(models.Model):
    """
    Customer profile containing strictly operational, emergency contact,
    and non-clinical accessibility preferences.
    Explicitly excludes clinical records, diagnoses, and medical histories.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the customer profile'
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        help_text='Associated User account'
    )
    emergency_contact_name = models.CharField(
        max_length=100,
        help_text='Full name of primary emergency contact'
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        help_text='Phone number of primary emergency contact'
    )
    emergency_contact_relation = models.CharField(
        max_length=50,
        help_text='Relationship to patient (e.g., Daughter, Spouse, Son)'
    )
    default_mobility_need = models.CharField(
        max_length=30,
        choices=MobilityRequirement.choices,
        default=MobilityRequirement.INDEPENDENT,
        help_text='Default mobility preference for transport coordination'
    )
    accessibility_notes = models.CharField(
        max_length=300,
        blank=True,
        help_text='Non-clinical physical assistance instructions (e.g., uses folding walker, needs arm support on steps)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'

    def __str__(self):
        return f"CustomerProfile: {self.user.phone_number} ({self.default_mobility_need})"


class FamilyHelper(models.Model):
    """
    Granular permission relationship granting a family member or helper
    delegated access to book, track, or review history for a primary customer.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    primary_customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='family_helpers',
        help_text='Patient or primary customer delegating access'
    )
    helper_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='helping_profiles',
        help_text='Helper or family member receiving delegated access'
    )
    can_book = models.BooleanField(
        default=False,
        help_text='Permission to create and confirm bookings on behalf of patient'
    )
    can_view_live_status = models.BooleanField(
        default=True,
        help_text='Permission to track live transit and hospital accompaniment status'
    )
    can_view_history = models.BooleanField(
        default=False,
        help_text='Permission to view past journey summaries and receipts'
    )
    relationship = models.CharField(
        max_length=50,
        blank=True,
        help_text='Relationship description (e.g., Son, Caretaker, Neighbor)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Family Helper'
        verbose_name_plural = 'Family Helpers'
        unique_together = ('primary_customer', 'helper_user')

    def __str__(self):
        return f"Helper: {self.helper_user.phone_number} -> Patient: {self.primary_customer.phone_number}"
