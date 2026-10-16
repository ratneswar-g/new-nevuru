import uuid
from django.db import models


class AccompanimentSession(models.Model):
    """
    Tracks the non-clinical hospital accompaniment phase of a journey,
    including arrival, department navigation, queue waiting duration, and completion.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the accompaniment session'
    )
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='accompaniment_session',
        help_text='Associated booking journey'
    )
    hospital_arrived_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when companion and patient arrived at hospital premises'
    )
    accompaniment_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when active hospital physical assistance began'
    )
    accompaniment_ended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when hospital consultation concluded and return transit began'
    )
    waiting_duration_minutes = models.PositiveIntegerField(
        default=0,
        help_text='Total billable minutes spent accompanying patient in consultation/queue'
    )
    non_clinical_notes = models.TextField(
        blank=True,
        help_text='Log of physical assistance, department navigation, and queue updates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Accompaniment Session'
        verbose_name_plural = 'Accompaniment Sessions'

    def __str__(self):
        return f"AccompanimentSession for Booking {self.booking_id} (Wait: {self.waiting_duration_minutes} min)"
