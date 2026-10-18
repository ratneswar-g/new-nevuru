import { useState, type ReactElement } from 'react';
import { AuthProvider, useAuth } from './auth';
import { Audit } from './pages/Audit';
import { Bookings } from './pages/Bookings';
import { Dashboard } from './pages/Dashboard';
import { Incidents } from './pages/Incidents';
import { Login } from './pages/Login';
import { Partners } from './pages/Partners';
import { RateCards } from './pages/RateCards';
import { API_BASE_URL } from './api';

const TABS: Record<string, () => ReactElement> = {
  Overview: Dashboard, Bookings, 'Care Partners': Partners, Incidents, 'Rate cards': RateCards, Audit,
};

function Shell() {
  const { state, signOut } = useAuth();
  const [tab, setTab] = useState<keyof typeof TABS>('Overview');

  if (state.status === 'unconfigured') {
    return <main className="login"><h1>Neravu Operations</h1>
      <p className="error">Firebase is not configured. Copy <code>environments/.env.example.admin</code> to <code>apps/admin-dashboard/.env.local</code> and fill in the VITE_FIREBASE_* values.</p></main>;
  }
  if (state.status === 'loading') return <main className="login"><p className="muted">Loading…</p></main>;
  if (state.status === 'signed-out') return <Login />;
  if (state.status === 'forbidden') {
    return <main className="login"><h1>Access denied</h1><p className="error">{state.reason}</p>
      <button onClick={signOut}>Sign out</button></main>;
  }

  const Page = TABS[tab];
  return (
    <div className="layout">
      <aside>
        <h1>Neravu</h1>
        <nav>{Object.keys(TABS).map((t) => (
          <button key={t} className={t === tab ? 'active' : ''} onClick={() => setTab(t)}>{t}</button>))}</nav>
        <div className="foot">
          <small>{state.me.fullName || state.me.phoneNumber}</small>
          <small className="muted">API: {API_BASE_URL}</small>
          <button onClick={signOut}>Sign out</button>
        </div>
      </aside>
      <main><Page /></main>
    </div>
  );
}

export default function App() {
  return <AuthProvider><Shell /></AuthProvider>;
}
