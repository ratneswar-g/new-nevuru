from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2) -> Decimal:
    """
    Straight-line (great-circle) distance in km.
    This is an ESTIMATE, not road distance. A routing provider is required
    for road-distance pricing (see docs/HANDOFF.md).
    """
    lat1, lon1, lat2, lon2 = (radians(float(v)) for v in (lat1, lon1, lat2, lon2))
    d_lat, d_lon = lat2 - lat1, lon2 - lon1
    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    return Decimal(str(round(2 * EARTH_RADIUS_KM * asin(sqrt(a)), 3)))
