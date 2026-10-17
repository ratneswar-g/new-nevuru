"""
Authoritative journey state machine. Clients can never set status directly;
every status change goes through services.transition().
"""

from .models import BookingStatus as S

ALLOWED_TRANSITIONS = {
    S.REQUESTED: {S.QUOTED, S.CANCELLED},
    S.QUOTED: {S.CONFIRMED, S.CANCELLED},
    S.CONFIRMED: {S.ASSIGNED, S.CANCELLED},
    S.ASSIGNED: {S.CONFIRMED, S.ARRIVED, S.CANCELLED, S.INCIDENT_FLAGGED},
    S.ARRIVED: {S.IN_TRANSIT_HOSPITAL, S.CANCELLED, S.INCIDENT_FLAGGED},
    S.IN_TRANSIT_HOSPITAL: {S.ACCOMPANIMENT, S.INCIDENT_FLAGGED},
    S.ACCOMPANIMENT: {S.RETURN_TRANSIT, S.COMPLETED, S.INCIDENT_FLAGGED},
    S.RETURN_TRANSIT: {S.COMPLETED, S.INCIDENT_FLAGGED},
    S.COMPLETED: {S.CLOSED},
    S.CLOSED: set(),
    S.CANCELLED: set(),
    # A flagged journey is frozen: only cancellation is a normal transition.
    # Resuming is possible solely through incident resolution (RESUME_TARGETS).
    S.INCIDENT_FLAGGED: {S.CANCELLED},
}

# Statuses in which a Care Partner is actively engaged (cannot take another job).
PARTNER_ACTIVE_STATUSES = {S.ASSIGNED, S.ARRIVED, S.IN_TRANSIT_HOSPITAL,
                           S.ACCOMPANIMENT, S.RETURN_TRANSIT}

# Statuses from which an emergency/incident may flag the journey.
FLAGGABLE_STATUSES = {S.ASSIGNED, S.ARRIVED, S.IN_TRANSIT_HOSPITAL,
                      S.ACCOMPANIMENT, S.RETURN_TRANSIT}

CUSTOMER_CANCELLABLE = {S.QUOTED, S.CONFIRMED, S.ASSIGNED}
TERMINAL = {S.CLOSED, S.CANCELLED}

# States an admin incident resolution may resume to (must equal pre_incident_status).
RESUME_TARGETS = set(FLAGGABLE_STATUSES)
