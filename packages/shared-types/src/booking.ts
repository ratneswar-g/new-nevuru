/**
 * Booking, journey state machine, and mobility requirement types
 */

export type BookingStatus =
  | 'REQUESTED'
  | 'QUOTED'
  | 'CONFIRMED'
  | 'ASSIGNED'
  | 'ARRIVED'
  | 'IN_TRANSIT_HOSPITAL'
  | 'ACCOMPANIMENT'
  | 'RETURN_TRANSIT'
  | 'COMPLETED'
  | 'CLOSED'
  | 'CANCELLED'
  | 'INCIDENT_FLAGGED';

export type MobilityRequirement =
  | 'INDEPENDENT'
  | 'WALKER_ASSISTANCE'
  | 'FOLDING_WHEELCHAIR'
  | 'COMPANION_ONLY';

export interface LocationPoint {
  address: string;
  latitude: number;
  longitude: number;
  landmark?: string;
}

export interface Booking {
  id: string;
  customerId: string;
  carePartnerId?: string;
  status: BookingStatus;
  pickupLocation: LocationPoint;
  hospitalDestination: LocationPoint;
  scheduledPickupTime: string;
  mobilityRequirement: MobilityRequirement;
  isRoundTrip: boolean;
  rateCardId: string;
  quotedFare: number;
  finalFare?: number;
  currency: 'INR';
  createdAt: string;
  updatedAt: string;
}

export interface OTPChallenge {
  bookingId: string;
  type: 'PICKUP' | 'DROPOFF';
  expiresAt: string;
  verifiedAt?: string;
  attemptsRemaining: number;
}
