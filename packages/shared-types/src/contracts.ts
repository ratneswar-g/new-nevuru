/**
 * Wire contracts for the Neravu REST API (/api/v1).
 *
 * Conventions (enforced by @neravu/api-client):
 *  - Property names are camelCase here; the wire format is snake_case.
 *  - Money and coordinates are DECIMAL STRINGS (e.g. "260.00") to avoid float drift.
 *  - Timestamps are ISO-8601 strings.
 *  - NOTE: only `import type` from this package so it stays erased at runtime (React Native safe).
 */

import type { UserRole } from './auth';
import type { BookingStatus, MobilityRequirement } from './booking';
import type { CarePartnerStatus, VehicleType } from './partner';

export type IncidentPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IncidentStatus = 'REPORTED' | 'UNDER_REVIEW' | 'RESOLVED' | 'CLOSED';
export type OtpChallengeType = 'PICKUP' | 'DROPOFF';
export type KycDocumentType = 'DRIVING_LICENSE' | 'AADHAAR' | 'POLICE_VERIFICATION' | 'VEHICLE_RC';

export interface ApiErrorBody {
  error: { code: string; message: string; details: Record<string, unknown> };
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/* ----------------------------------------------------------------- identity */

export interface Me {
  id: string;
  phoneNumber: string;
  email: string | null;
  firstName: string;
  lastName: string;
  fullName: string;
  role: UserRole;
  isActive: boolean;
  createdAt: string;
  hasCustomerProfile: boolean;
  carePartnerStatus: CarePartnerStatus | null;
}

export interface RegisterInput {
  role: 'CUSTOMER' | 'CARE_PARTNER';
  firstName: string;
  lastName?: string;
  email?: string;
}

export interface CustomerProfileDto {
  emergencyContactName: string;
  emergencyContactPhone: string;
  emergencyContactRelation: string;
  defaultMobilityNeed: MobilityRequirement;
  accessibilityNotes: string;
  updatedAt?: string;
}

export interface FamilyHelperGrant {
  id: string;
  helperPhoneNumber: string;
  helperName: string;
  canBook: boolean;
  canViewLiveStatus: boolean;
  canViewHistory: boolean;
  relationship: string;
  createdAt: string;
}

export interface FamilyHelperInput {
  helperPhoneNumber: string;
  canBook?: boolean;
  canViewLiveStatus?: boolean;
  canViewHistory?: boolean;
  relationship?: string;
}

/* ------------------------------------------------------------------ pricing */

export interface PublicPricing {
  available: boolean;
  currency?: 'INR';
  version?: number;
  baseFare?: string;
  baseDistanceKm?: string;
  perKmRate?: string;
  perMinuteWaitingRate?: string;
  mobilityTierSurcharges?: Record<MobilityRequirement, string>;
}

export interface RateCardDto {
  id: string;
  version: number;
  name: string;
  baseFare: string;
  baseDistanceKm: string;
  perKmRate: string;
  perMinuteWaitingRate: string;
  mobilityTierSurcharges: Record<MobilityRequirement, string>;
  effectiveFrom: string;
  effectiveTo: string | null;
  isActive: boolean;
  createdAt: string;
}

export interface RateCardInput {
  name: string;
  baseFare: string;
  baseDistanceKm: string;
  perKmRate: string;
  perMinuteWaitingRate: string;
  mobilityTierSurcharges: Record<MobilityRequirement, string>;
  effectiveFrom: string;
}

/* ----------------------------------------------------------------- bookings */

export interface TripRequestInput {
  pickupAddress: string;
  pickupLatitude: string | number;
  pickupLongitude: string | number;
  pickupLandmark?: string;
  hospitalName: string;
  hospitalAddress: string;
  hospitalLatitude: string | number;
  hospitalLongitude: string | number;
  mobilityRequirement: MobilityRequirement;
  isRoundTrip: boolean;
  estimatedWaitingMinutes?: number;
}

export interface BookingCreateInput extends TripRequestInput {
  scheduledPickupTime: string;
  /** Family helper booking on behalf of a primary customer (needs canBook). */
  customerId?: string;
}

export interface QuoteResult {
  rateCardVersion: number;
  distanceKm: string;
  distanceBasis: 'STRAIGHT_LINE_ESTIMATE';
  baseFare: string;
  distanceFare: string;
  mobilitySurcharge: string;
  estimatedWaitingFare: string;
  estimatedWaitingMinutes: number;
  totalFare: string;
  currency: 'INR';
  note: string;
}

export interface PartnerSummary {
  id: string;
  firstName: string;
  phoneNumber: string;
  vehicle: { registrationNumber: string; make: string; model: string; color: string } | null;
}

/** Customer / family helper view. Contains NO OTP values. */
export interface CustomerBooking {
  id: string;
  status: BookingStatus;
  customerId: string;
  pickupAddress: string;
  pickupLatitude: string;
  pickupLongitude: string;
  pickupLandmark: string;
  hospitalName: string;
  hospitalAddress: string;
  hospitalLatitude: string;
  hospitalLongitude: string;
  scheduledPickupTime: string;
  mobilityRequirement: MobilityRequirement;
  isRoundTrip: boolean;
  rateCardVersion: number;
  quotedFare: string;
  finalFare: string | null;
  currency: 'INR';
  carePartner: PartnerSummary | null;
  pickupVerified: boolean;
  dropoffVerified: boolean;
  cancellationReason: string;
  createdAt: string;
  updatedAt: string;
}

export interface AdminBooking extends CustomerBooking {
  customerName: string;
  customerPhone: string;
  carePartnerId: string | null;
  carePartnerName: string | null;
  preIncidentStatus: string;
}

/** Care Partner view: operational data only. No fares, no OTP, no emergency contact. */
export interface PartnerJob {
  id: string;
  status: BookingStatus;
  customer: { firstName: string; phoneNumber: string; accessibilityNotes: string };
  pickupAddress: string;
  pickupLatitude: string;
  pickupLongitude: string;
  pickupLandmark: string;
  hospitalName: string;
  hospitalAddress: string;
  hospitalLatitude: string;
  hospitalLongitude: string;
  scheduledPickupTime: string;
  mobilityRequirement: MobilityRequirement;
  isRoundTrip: boolean;
  pickupVerified: boolean;
  dropoffVerified: boolean;
  createdAt: string;
  updatedAt: string;
}

/** Returned ONLY to the customer side, once, when the customer generates a code. */
export interface OtpIssue {
  challengeType: OtpChallengeType;
  code: string;
  expiresAt: string;
  attemptsAllowed: number;
}

/* ---------------------------------------------------------------- incidents */

export interface Incident {
  id: string;
  bookingId: string;
  reporterRole: UserRole;
  category: string;
  priority: IncidentPriority;
  status: IncidentStatus;
  narrative: string;
  resolutionNotes: string;
  resolvedAt: string | null;
  createdAt: string;
}

export interface IncidentInput {
  category: string;
  narrative: string;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface EmergencyResult {
  incident: Incident;
  guidance: string;
}

/* ------------------------------------------------------------ care partners */

export interface PartnerVehicleDto {
  id: string;
  registrationNumber: string;
  make: string;
  model: string;
  color: string;
  vehicleType: VehicleType;
  seatingCapacity: number;
  supportedMobility: MobilityRequirement[];
  isVerified: boolean;
  isActive: boolean;
  insuranceExpiry: string | null;
  fitnessExpiry: string | null;
}

export interface PartnerVehicleInput {
  registrationNumber: string;
  make: string;
  model: string;
  color?: string;
  vehicleType: VehicleType;
  seatingCapacity?: number;
  supportedMobility: MobilityRequirement[];
}

export interface PartnerSelf {
  id: string;
  fullName: string;
  phoneNumber: string;
  status: CarePartnerStatus;
  isOnline: boolean;
  completedTripsCount: number;
  kycSubmittedAt: string | null;
  verifiedAt: string | null;
  vehicles: PartnerVehicleDto[];
  documentTypes: KycDocumentType[];
}

/* -------------------------------------------------------------------- admin */

export interface DashboardSummary {
  bookingsByStatus: Partial<Record<BookingStatus, number>>;
  partnersPendingVerification: number;
  partnersOnline: number;
  openIncidents: number;
}

export interface AuditLogEntry {
  id: string;
  actorId: string | null;
  actorRole: string;
  action: string;
  resourceType: string;
  resourceId: string;
  previousState: Record<string, unknown>;
  newState: Record<string, unknown>;
  timestamp: string;
}
