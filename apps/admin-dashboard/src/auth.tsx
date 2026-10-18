import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { ApiError } from '@neravu/api-client';
import type { Me } from '@neravu/shared-types';
import { api } from './api';
import { firebaseConfigured, logout, watchAuth } from './firebase';

export type AuthState =
  | { status: 'loading' }
  | { status: 'unconfigured' }
  | { status: 'signed-out' }
  | { status: 'forbidden'; reason: string }
  | { status: 'ready'; me: Me };

const Ctx = createContext<{ state: AuthState; signOut: () => Promise<void> }>({
  state: { status: 'loading' }, signOut: async () => {},
});
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(firebaseConfigured ? { status: 'loading' } : { status: 'unconfigured' });

  useEffect(() => {
    if (!firebaseConfigured) return;
    return watchAuth(async (user) => {
      if (!user) return setState({ status: 'signed-out' });
      setState({ status: 'loading' });
      try {
        const me = await api.me();
        if (me.role !== 'ADMIN') {
          return setState({ status: 'forbidden', reason: 'This account is not an administrator.' });
        }
        setState({ status: 'ready', me });
      } catch (e) {
        const msg = e instanceof ApiError
          ? (e.status === 401 ? 'No administrator account is linked to this sign-in.' : e.message)
          : 'Unexpected error.';
        setState({ status: 'forbidden', reason: msg });
      }
    });
  }, []);

  return <Ctx.Provider value={{ state, signOut: logout }}>{children}</Ctx.Provider>;
}
