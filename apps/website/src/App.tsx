import { useEffect, useState } from 'react';
import { createApiClient } from '@neravu/api-client';
import type { MobilityRequirement, PublicPricing } from '@neravu/shared-types';

const api = createApiClient({
  baseUrl: (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000/api/v1',
  getIdToken: async () => null,
});

const MOBILITY_LABEL: Record<MobilityRequirement, string> = {
  INDEPENDENT: 'Independent — walks without help',
  WALKER_ASSISTANCE: 'Walker assistance',
  FOLDING_WHEELCHAIR: 'Folding wheelchair',
  COMPANION_ONLY: 'Companion only (no transfer help)',
};
const MOBILITY: MobilityRequirement[] = ['INDEPENDENT', 'WALKER_ASSISTANCE', 'FOLDING_WHEELCHAIR', 'COMPANION_ONLY'];

const inr = (v?: string) => (v == null ? '—' : `₹${Number(v).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`);
const card: React.CSSProperties = { backgroundColor: '#fff', borderRadius: 8, padding: '1.5rem 2rem', boxShadow: '0 2px 8px rgba(23,43,77,.08)', marginBottom: '1.25rem' };

type PricingState = { kind: 'loading' } | { kind: 'error' } | { kind: 'ready'; data: PublicPricing };

export default function App() {
  const [pricing, setPricing] = useState<PricingState>({ kind: 'loading' });

  useEffect(() => {
    let live = true;
    api.publicPricing()
      .then((data) => live && setPricing({ kind: 'ready', data }))
      .catch(() => live && setPricing({ kind: 'error' }));
    return () => { live = false; };
  }, []);

  const p = pricing.kind === 'ready' && pricing.data.available ? pricing.data : null;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#EAF5FF', color: '#172B4D', fontFamily: 'system-ui, sans-serif' }}>
      <header style={{ backgroundColor: '#1769AA', color: '#fff', padding: '1.25rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', margin: 0 }}>Neravu</h1>
        <span style={{ fontSize: '.875rem', backgroundColor: '#62B6E8', color: '#172B4D', padding: '.25rem .75rem', borderRadius: 4, fontWeight: 600 }}>
          Assisted Mobility Platform
        </span>
      </header>

      <main style={{ maxWidth: 960, margin: '2rem auto', padding: '0 1rem' }}>
        <section style={card}>
          <h2 style={{ color: '#1769AA', marginTop: 0 }}>Doorstep-to-hospital assistance, with a companion who stays</h2>
          <p style={{ lineHeight: 1.6 }}>
            A verified Care Partner collects you from home, accompanies you through hospital navigation and queues,
            and brings you back. Non-clinical support only.
          </p>
          <div style={{ padding: '1rem', backgroundColor: '#fff3cd', borderRadius: 6, color: '#856404' }} role="note">
            <strong>Safety notice:</strong> Neravu is not an ambulance service and does not provide clinical care or emergency
            medical services. In a medical emergency call <strong>108</strong> or <strong>112</strong> immediately.
          </div>
        </section>

        <section style={card}>
          <h2 style={{ color: '#1769AA', marginTop: 0 }}>How it works</h2>
          <ol style={{ lineHeight: 1.8, paddingLeft: '1.25rem' }}>
            <li>Request a journey in the Neravu app and see your fare before you confirm.</li>
            <li>Neravu assigns a verified Care Partner and vehicle suited to your mobility needs.</li>
            <li>Your Care Partner arrives; you share a one-time code to confirm the right person at your door.</li>
            <li>They accompany you at the hospital, then bring you home — confirmed with a second code.</li>
          </ol>
        </section>

        <section style={card}>
          <h2 style={{ color: '#1769AA', marginTop: 0 }}>Supported mobility needs</h2>
          <ul style={{ lineHeight: 1.8 }}>{MOBILITY.map((m) => <li key={m}>{MOBILITY_LABEL[m]}</li>)}</ul>
        </section>

        <section style={card} aria-live="polite">
          <h2 style={{ color: '#1769AA', marginTop: 0 }}>Pricing</h2>
          {pricing.kind === 'loading' && <p>Loading current pricing…</p>}
          {pricing.kind === 'error' && <p>Pricing is temporarily unavailable. Please try again shortly.</p>}
          {pricing.kind === 'ready' && !p && <p>Pricing has not been published yet. Please check back soon.</p>}
          {p && (
            <>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <tbody>
                  <tr><td>Base fare (includes first {p.baseDistanceKm} km)</td><td align="right">{inr(p.baseFare)}</td></tr>
                  <tr><td>Each additional km</td><td align="right">{inr(p.perKmRate)}</td></tr>
                  <tr><td>Hospital accompaniment, per minute</td><td align="right">{inr(p.perMinuteWaitingRate)}</td></tr>
                  {MOBILITY.map((m) => (
                    <tr key={m}><td>Assistance surcharge — {MOBILITY_LABEL[m].split(' — ')[0]}</td>
                      <td align="right">{inr(p.mobilityTierSurcharges?.[m])}</td></tr>
                  ))}
                </tbody>
              </table>
              <p style={{ fontSize: '.85rem', color: '#5b6b85' }}>
                Round trips count both legs of distance. Your exact fare is shown in the app before you confirm.
              </p>
            </>
          )}
        </section>
      </main>

      <footer style={{ textAlign: 'center', padding: '1.5rem', color: '#5b6b85', fontSize: '.85rem' }}>
        © Neravu · Non-emergency assisted mobility
      </footer>
    </div>
  );
}
