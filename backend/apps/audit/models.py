import uuid
from django.db import models


class AuditLog(models.Model):
    """
    Append-only immutable audit trail capturing state changes and administrative actions.
    Uses decoupled actor and resource identifiers to avoid tight foreign-key dependencies.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the audit entry'
    )
    actor_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text='UUID of user or administrator who triggered the event'
    )
    actor_role = models.CharField(
        max_length=30,
        blank=True,
        help_text='Role of the actor at the time of action'
    )
    action = models.CharField(
        max_length=100,
        db_index=True,
        help_text='Standardized action name (e.g., BOOKING_STATUS_CHANGED, RATE_CARD_ACTIVATED)'
    )
    resource_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text='Type of entity affected (e.g., Booking, CarePartnerProfile, RateCard)'
    )
    resource_id = models.UUIDField(
        db_index=True,
        help_text='UUID of the affected entity'
    )
    previous_state = models.JSONField(
        default=dict,
        blank=True,
        help_text='Snapshot of fields prior to modification'
    )
    new_state = models.JSONField(
        default=dict,
        blank=True,
        help_text='Snapshot of fields after modification'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='Client IP address initiating the action'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Exact timestamp when event was recorded'
    )

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit: [{self.action}] on {self.resource_type}:{self.resource_id} at {self.timestamp}"
