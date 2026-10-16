/**
 * User roles and authentication types for Neravu
 */

export type UserRole = 'CUSTOMER' | 'CARE_PARTNER' | 'ADMIN';

export interface UserProfile {
  id: string;
  phoneNumber: string;
  email?: string;
  fullName: string;
  role: UserRole;
  isActive: boolean;
  createdAt: string;
}

export interface FamilyHelperPermission {
  id: string;
  primaryCustomerId: string;
  helperUserId: string;
  canBook: boolean;
  canViewLiveStatus: boolean;
  canViewHistory: boolean;
  relationship: string;
  createdAt: string;
}
