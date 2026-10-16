import uuid
from django.db import models


class RateCard(models.Model):
    """
    Versioned rate card defining configurable pricing parameters for assisted medical journeys.
    Maintains historical rate versions for audit and accurate past booking reconciliation.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the rate card'
    )
    version = models.PositiveIntegerField(
        unique=True,
        db_index=True,
        help_text='Sequential version number (e.g., 1, 2, 3)'
    )
    name = models.CharField(
        max_length=100,
        help_text='Descriptive label for this rate card configuration'
    )
    base_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Base booking fare in INR'
    )
    base_distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=4.0,
        help_text='Included transit distance in kilometers'
    )
    per_km_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text='Incremental fee per kilometer beyond base distance in INR'
    )
    per_minute_waiting_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text='Fee per minute of hospital accompaniment / waiting in INR'
    )
    mobility_tier_surcharges = models.JSONField(
        default=dict,
        help_text='Surcharge amounts in INR mapped by MobilityRequirement'
    )
    effective_from = models.DateTimeField(
        help_text='Start timestamp when this rate card becomes active'
    )
    effective_to = models.DateTimeField(
        null=True,
        blank=True,
        help_text='End timestamp when this rate card is superseded'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Indicates if this rate card is eligible for current quotes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rate Card'
        verbose_name_plural = 'Rate Cards'
        ordering = ['-version']

    def __str__(self):
        return f"RateCard v{self.version}: {self.name} ({'ACTIVE' if self.is_active else 'INACTIVE'})"
