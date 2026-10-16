import uuid
from django.conf import settings
from django.db import models


class IncidentPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    CRITICAL = 'CRITICAL', 'Critical / Safety Escalation'


class IncidentStatus(models.TextChoices):
    REPORTED = 'REPORTED', 'Reported'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    RESOLVED = 'RESOLVED', 'Resolved'
    CLOSED = 'CLOSED', 'Closed'


class IncidentRecord(models.Model):
    """
    Operational incident or safety escalation logged during an assisted transit journey.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the incident'
    )
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='incidents',
        help_text='Booking during which incident occurred'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reported_incidents',
        help_text='User who initiated the incident report (Customer, Care Partner, or Admin)'
    )
    category = models.CharField(
        max_length=50,
        help_text='Incident category (e.g., VEHICLE_BREAKDOWN, UNEXPECTED_DELAY, MEDICAL_DISTRESS_DIVERT)'
    )
    priority = models.CharField(
        max_length=20,
        choices=IncidentPriority.choices,
        default=IncidentPriority.MEDIUM,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=IncidentStatus.choices,
        default=IncidentStatus.REPORTED,
        db_index=True
    )
    narrative = models.TextField(
        help_text='Detailed factual description of the incident event'
    )
    resolution_notes = models.TextField(
        blank=True,
        help_text='Administrative actions taken to resolve or follow up'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when administrative resolution was recorded'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Incident Record'
        verbose_name_plural = 'Incident Records'
        ordering = ['-created_at']

    def __str__(self):
        return f"Incident [{self.priority}] on Booking {self.booking_id}: {self.category} ({self.status})"
