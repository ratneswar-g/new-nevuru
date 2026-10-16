import type { CarePartnerStatus, BookingStatus } from '@neravu/shared-types';

export default function App() {
  const partnerStatuses: CarePartnerStatus[] = [
    'PENDING_VERIFICATION',
    'APPROVED',
    'REJECTED',
    'SUSPENDED',
  ];

  const bookingStages: BookingStatus[] = [
    'REQUESTED',
    'QUOTED',
    'CONFIRMED',
    'ASSIGNED',
    'ARRIVED',
    'IN_TRANSIT_HOSPITAL',
    'ACCOMPANIMENT',
    'RETURN_TRANSIT',
    'COMPLETED',
    'CLOSED',
  ];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#EAF5FF', color: '#172B4D', fontFamily: 'system-ui, sans-serif' }}>
      <header style={{ backgroundColor: '#172B4D', color: '#ffffff', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>Neravu Operations</h1>
          <span style={{ fontSize: '0.75rem', color: '#62B6E8' }}>Admin Oversight & Partner Verification</span>
        </div>
        <span style={{ fontSize: '0.75rem', backgroundColor: '#1769AA', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
          Role: ADMIN
        </span>
      </header>

      <main style={{ maxWidth: '1000px', margin: '2rem auto', padding: '0 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <section style={{ backgroundColor: '#ffffff', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(23, 43, 77, 0.08)' }}>
          <h2 style={{ color: '#1769AA', fontSize: '1.125rem', marginTop: 0 }}>Care Partner Verification Lifecycle</h2>
          <p style={{ fontSize: '0.875rem', color: '#42526E' }}>Admin KYC verification states enforced before duty assignment:</p>
          <ul style={{ paddingLeft: '1.25rem', fontSize: '0.875rem' }}>
            {partnerStatuses.map((status) => (
              <li key={status} style={{ margin: '0.375rem 0' }}><code>{status}</code></li>
            ))}
          </ul>
        </section>

        <section style={{ backgroundColor: '#ffffff', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(23, 43, 77, 0.08)' }}>
          <h2 style={{ color: '#1769AA', fontSize: '1.125rem', marginTop: 0 }}>Journey State Supervision</h2>
          <p style={{ fontSize: '0.875rem', color: '#42526E' }}>Authoritative state transitions monitored by dispatch:</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
            {bookingStages.map((stage) => (
              <span key={stage} style={{ fontSize: '0.75rem', backgroundColor: '#EAF5FF', color: '#1769AA', padding: '0.25rem 0.5rem', borderRadius: '4px', border: '1px solid #62B6E8' }}>
                {stage}
              </span>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
