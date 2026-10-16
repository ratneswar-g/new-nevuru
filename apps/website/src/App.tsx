import type { MobilityRequirement } from '@neravu/shared-types';

export default function App() {
  const supportedMobilities: MobilityRequirement[] = [
    'INDEPENDENT',
    'WALKER_ASSISTANCE',
    'FOLDING_WHEELCHAIR',
    'COMPANION_ONLY',
  ];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#EAF5FF', color: '#172B4D', fontFamily: 'system-ui, sans-serif' }}>
      <header style={{ backgroundColor: '#1769AA', color: '#ffffff', padding: '1.25rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Neravu</h1>
        <span style={{ fontSize: '0.875rem', backgroundColor: '#62B6E8', color: '#172B4D', padding: '0.25rem 0.75rem', borderRadius: '4px', fontWeight: 600 }}>
          Assisted Mobility Platform
        </span>
      </header>

      <main style={{ maxWidth: '960px', margin: '2rem auto', padding: '0 1rem' }}>
        <section style={{ backgroundColor: '#ffffff', borderRadius: '8px', padding: '2rem', boxShadow: '0 2px 8px rgba(23, 43, 77, 0.08)' }}>
          <h2 style={{ color: '#1769AA', marginTop: 0 }}>Assisted Medical Transport & Non-Clinical Patient Accompaniment</h2>
          <p style={{ lineHeight: 1.6 }}>
            Neravu provides doorstep-to-hospital assisted transportation paired with compassionate non-clinical companions for hospital navigation, queue waiting, and return journeys.
          </p>

          <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#EAF5FF', borderRadius: '6px', borderLeft: '4px solid #1769AA' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem' }}>Supported Mobility Needs</h3>
            <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
              {supportedMobilities.map((need) => (
                <li key={need} style={{ margin: '0.25rem 0' }}>{need}</li>
              ))}
            </ul>
          </div>

          <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#fff3cd', borderRadius: '6px', color: '#856404' }}>
            <strong>Safety Notice:</strong> Neravu is not an ambulance service and does not provide clinical care or emergency medical services. For clinical emergencies, call 108 or 112 immediately.
          </div>
        </section>
      </main>
    </div>
  );
}
