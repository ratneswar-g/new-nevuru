/**
 * Pricing, rate cards, and fare estimates
 */

import { MobilityRequirement } from './booking';

export interface RateCardRule {
  id: string;
  version: number;
  name: string;
  baseFare: number;
  baseDistanceKm: number;
  perKmRate: number;
  perMinuteWaitingRate: number;
  mobilityTierSurcharges: Record<MobilityRequirement, number>;
  effectiveFrom: string;
  effectiveTo?: string;
  isActive: boolean;
}

export interface FareEstimate {
  quoteId: string;
  rateCardVersion: number;
  baseFare: number;
  distanceFare: number;
  estimatedDistanceKm: number;
  estimatedWaitingFare: number;
  estimatedWaitingMinutes: number;
  mobilitySurcharge: number;
  totalFare: number;
  currency: 'INR';
  expiresAt: string;
}
