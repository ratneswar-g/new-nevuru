import auth from '@react-native-firebase/auth';
import { createApiClient } from '@neravu/api-client';

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://10.0.2.2:8000/api/v1';

export const api = createApiClient({
  baseUrl: API_BASE_URL,
  getIdToken: async () => {
    const u = auth().currentUser;
    return u ? u.getIdToken() : null;
  },
});
