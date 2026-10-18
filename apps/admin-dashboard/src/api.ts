import { createApiClient } from '@neravu/api-client';
import { getIdToken } from './firebase';

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000/api/v1';

export const api = createApiClient({ baseUrl: API_BASE_URL, getIdToken });
