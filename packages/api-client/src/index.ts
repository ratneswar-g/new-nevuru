import type {
  AdminBooking, ApiErrorBody, AuditLogEntry, BookingCreateInput, CustomerBooking, CustomerProfileDto,
  DashboardSummary, EmergencyResult, FamilyHelperGrant, FamilyHelperInput, Incident, IncidentInput, Me,
  OtpChallengeType, OtpIssue, Page, PartnerJob, PartnerSelf, PartnerVehicleDto, PartnerVehicleInput,
  PublicPricing, QuoteResult, RateCardDto, RateCardInput, RegisterInput, TripRequestInput, KycDocumentType,
} from '@neravu/shared-types';
import { camelizeKeys, snakeizeKeys } from './case';

export { camelizeKeys, snakeizeKeys } from './case';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;
  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export interface ApiClientOptions {
  /** e.g. http://localhost:8000/api/v1 (no trailing slash) */
  baseUrl: string;
  /** Returns a fresh Firebase ID token, or null when signed out. */
  getIdToken: () => Promise<string | null>;
  onUnauthorized?: () => void;
  fetchImpl?: typeof fetch;
}

type Query = Record<string, string | number | undefined>;

export function createApiClient(opts: ApiClientOptions) {
  const doFetch = opts.fetchImpl ?? ((...a: Parameters<typeof fetch>) => fetch(...a));

  async function call<T>(method: string, path: string, body?: unknown, query?: Query, auth = true): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (auth) {
      const token = await opts.getIdToken();
      if (token) headers.Authorization = `Bearer ${token}`;
    }
    const qs = query
      ? '?' + Object.entries(query).filter(([, v]) => v !== undefined && v !== '')
          .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join('&')
      : '';
    let res: Response;
    try {
      res = await doFetch(`${opts.baseUrl}${path}${qs}`, {
        method, headers, body: body === undefined ? undefined : JSON.stringify(snakeizeKeys(body)),
      });
    } catch {
      throw new ApiError(0, 'NETWORK_ERROR', 'Cannot reach the Neravu service. Check your connection.');
    }
    if (res.status === 204) return undefined as T;
    let json: unknown = null;
    try { json = await res.json(); } catch { /* non-JSON body */ }
    if (!res.ok) {
      if (res.status === 401) opts.onUnauthorized?.();
      const e = (camelizeKeys<Partial<ApiErrorBody>>(json) as { error?: ApiErrorBody['error'] } | null)?.error;
      // Detail keys of validation errors are field names; keep them as the server sent them (camelized).
      throw new ApiError(res.status, e?.code ?? `HTTP_${res.status}`, e?.message ?? res.statusText, e?.details ?? {});
    }
    return camelizeKeys<T>(json);
  }

  const get = <T>(p: string, q?: Query) => call<T>('GET', p, undefined, q);
  const post = <T>(p: string, b?: unknown) => call<T>('POST', p, b ?? {});

  return {
    // ---- public
    publicPricing: () => call<PublicPricing>('GET', '/public/pricing/', undefined, undefined, false),

    // ---- identity
    register: (input: RegisterInput) => post<Me>('/auth/register/', input),
    me: () => get<Me>('/me/'),
    updateMe: (patch: Partial<Pick<Me, 'firstName' | 'lastName' | 'email'>>) => call<Me>('PATCH', '/me/', patch),

    customer: {
      getProfile: () => get<CustomerProfileDto>('/me/customer-profile/'),
      saveProfile: (p: CustomerProfileDto) => call<CustomerProfileDto>('PUT', '/me/customer-profile/', p),
      listHelpers: () => get<Page<FamilyHelperGrant>>('/me/family-helpers/'),
      addHelper: (i: FamilyHelperInput) => post<FamilyHelperGrant>('/me/family-helpers/', i),
      removeHelper: (id: string) => call<void>('DELETE', `/me/family-helpers/${id}/`),
      quote: (i: TripRequestInput) => post<QuoteResult>('/bookings/quote/', i),
      createBooking: (i: BookingCreateInput) => post<CustomerBooking>('/bookings/', i),
      listBookings: (status?: string) => get<Page<CustomerBooking>>('/bookings/', { status }),
      getBooking: (id: string) => get<CustomerBooking>(`/bookings/${id}/`),
      confirm: (id: string) => post<CustomerBooking>(`/bookings/${id}/confirm/`),
      cancel: (id: string, reason?: string) => post<CustomerBooking>(`/bookings/${id}/cancel/`, { reason }),
      issueOtp: (id: string, type: OtpChallengeType) =>
        post<OtpIssue>(`/bookings/${id}/otp/${type.toLowerCase()}/`),
      emergency: (id: string, narrative?: string) =>
        post<EmergencyResult>(`/bookings/${id}/emergency/`, narrative ? { narrative } : {}),
      reportIncident: (id: string, i: IncidentInput) => post<Incident>(`/bookings/${id}/incidents/`, i),
    },

    partner: {
      me: () => get<PartnerSelf>('/partner/me/'),
      submitKyc: (documentType: KycDocumentType, documentIdentifier: string) =>
        call<void>('POST', '/partner/kyc/', { documentType, documentIdentifier }),
      listVehicles: () => get<Page<PartnerVehicleDto>>('/partner/vehicles/'),
      addVehicle: (i: PartnerVehicleInput) => post<PartnerVehicleDto>('/partner/vehicles/', i),
      setDuty: (isOnline: boolean) => post<{ isOnline: boolean }>('/partner/duty/', { isOnline }),
      listJobs: (status?: string) => get<Page<PartnerJob>>('/partner/bookings/', { status }),
      getJob: (id: string) => get<PartnerJob>(`/partner/bookings/${id}/`),
      arrive: (id: string) => post<PartnerJob>(`/partner/bookings/${id}/arrive/`),
      verifyPickup: (id: string, code: string) => post<PartnerJob>(`/partner/bookings/${id}/verify-pickup/`, { code }),
      arriveHospital: (id: string) => post<PartnerJob>(`/partner/bookings/${id}/arrive-hospital/`),
      startReturn: (id: string, notes?: string) => post<PartnerJob>(`/partner/bookings/${id}/start-return/`, { notes }),
      complete: (id: string, code: string, notes?: string) =>
        post<PartnerJob>(`/partner/bookings/${id}/complete/`, { code, notes }),
      emergency: (id: string, narrative?: string) =>
        post<EmergencyResult>(`/partner/bookings/${id}/emergency/`, narrative ? { narrative } : {}),
      reportIncident: (id: string, i: IncidentInput) => post<Incident>(`/partner/bookings/${id}/incidents/`, i),
    },

    admin: {
      dashboard: () => get<DashboardSummary>('/admin/dashboard/'),
      listBookings: (status?: string, page?: number) => get<Page<AdminBooking>>('/admin/bookings/', { status, page }),
      getBooking: (id: string) => get<AdminBooking>(`/admin/bookings/${id}/`),
      assign: (id: string, carePartnerId: string) => post<AdminBooking>(`/admin/bookings/${id}/assign/`, { carePartnerId }),
      unassign: (id: string) => post<AdminBooking>(`/admin/bookings/${id}/unassign/`),
      cancel: (id: string, reason?: string) => post<AdminBooking>(`/admin/bookings/${id}/cancel/`, { reason }),
      close: (id: string) => post<AdminBooking>(`/admin/bookings/${id}/close/`),
      listPartners: (status?: string) => get<Page<PartnerSelf>>('/admin/partners/', { status }),
      approvePartner: (id: string) => post<PartnerSelf>(`/admin/partners/${id}/approve/`),
      rejectPartner: (id: string) => post<PartnerSelf>(`/admin/partners/${id}/reject/`),
      suspendPartner: (id: string) => post<PartnerSelf>(`/admin/partners/${id}/suspend/`),
      verifyVehicle: (id: string) => post<PartnerVehicleDto>(`/admin/vehicles/${id}/verify/`),
      listIncidents: (q?: { status?: string; priority?: string }) => get<Page<Incident>>('/admin/incidents/', q),
      resolveIncident: (id: string, resolutionNotes: string, bookingAction: 'RESUME' | 'CANCEL') =>
        post<Incident>(`/admin/incidents/${id}/resolve/`, { resolutionNotes, bookingAction }),
      listRateCards: () => get<Page<RateCardDto>>('/admin/rate-cards/'),
      createRateCard: (i: RateCardInput) => post<RateCardDto>('/admin/rate-cards/', i),
      activateRateCard: (id: string) => post<RateCardDto>(`/admin/rate-cards/${id}/activate/`),
      listAuditLogs: (q?: { action?: string; resourceType?: string; resourceId?: string; page?: number }) =>
        get<Page<AuditLogEntry>>('/admin/audit-logs/', {
          action: q?.action, resource_type: q?.resourceType, resource_id: q?.resourceId, page: q?.page,
        }),
    },
  };
}

export type NeravuApi = ReturnType<typeof createApiClient>;
