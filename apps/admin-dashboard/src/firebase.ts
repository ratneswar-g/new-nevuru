import { initializeApp } from 'firebase/app';
import {
  getAuth, onAuthStateChanged, RecaptchaVerifier, signInWithPhoneNumber, signOut,
  type Auth, type ConfirmationResult, type User,
} from 'firebase/auth';

const cfg = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY as string | undefined,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN as string | undefined,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID as string | undefined,
  appId: import.meta.env.VITE_FIREBASE_APP_ID as string | undefined,
};

export const firebaseConfigured = Boolean(cfg.apiKey && cfg.authDomain && cfg.projectId && cfg.appId);

let auth: Auth | null = null;
function getFirebaseAuth(): Auth {
  if (!firebaseConfigured) throw new Error('Firebase is not configured. Set VITE_FIREBASE_* in .env.local.');
  if (!auth) auth = getAuth(initializeApp(cfg as Record<string, string>));
  return auth;
}

export function watchAuth(cb: (user: User | null) => void): () => void {
  return onAuthStateChanged(getFirebaseAuth(), cb);
}

export async function getIdToken(): Promise<string | null> {
  if (!firebaseConfigured) return null;
  const u = getFirebaseAuth().currentUser;
  return u ? u.getIdToken() : null;
}

let verifier: RecaptchaVerifier | null = null;

export async function sendCode(phone: string, containerId: string): Promise<ConfirmationResult> {
  const a = getFirebaseAuth();
  verifier?.clear();
  verifier = new RecaptchaVerifier(a, containerId, { size: 'invisible' });
  return signInWithPhoneNumber(a, phone, verifier);
}

export const logout = () => signOut(getFirebaseAuth());
