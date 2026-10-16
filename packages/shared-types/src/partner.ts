/**
 * Care Partner, verification status, and vehicle types
 */

import { MobilityRequirement } from './booking';

export type CarePartnerStatus =
  | 'PENDING_VERIFICATION'
  | 'APPROVED'
  | 'REJECTED'
  | 'SUSPENDED';

export type VehicleType =
  | 'SEDAN'
  | 'HATCHBACK'
  | 'SUV'
  | 'WHEELCHAIR_ACCESSIBLE';

export interface Vehicle {
  id: string;
  carePartnerId: string;
  registrationNumber: string;
  make: string;
  model: string;
  color: string;
  vehicleType: VehicleType;
  seatingCapacity: number;
  supportedMobility: MobilityRequirement[];
  isVerified: boolean;
  insuranceExpiry: string;
  fitnessExpiry: string;
}

export interface CarePartnerProfile {
  id: string;
  userId: string;
  fullName: string;
  phoneNumber: string;
  status: CarePartnerStatus;
  isOnline: boolean;
  currentLatitude?: number;
  currentLongitude?: number;
  rating?: number;
  completedTripsCount: number;
  activeVehicleId?: string;
  kycSubmittedAt?: string;
  verifiedAt?: string;
}
