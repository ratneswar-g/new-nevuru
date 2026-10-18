import { useState } from 'react';
import type { AdminBooking } from '@neravu/shared-types';
import { api } from '../api';
import { errMsg, Feedback, inr, Pager, Panel, Status, useAsync, when } from '../ui';

const STATUSES = ['', 'QUOTED', 'CONFIRMED', 'ASSIGNED', 'ARRIVED', 'IN_TRANSIT_HOSPITAL', 'ACCOMPANIMENT',
  'RETURN_TRANSIT', 'COMPLETED', 'CLOSED', 'CANCELLED', 'INCIDENT_FLAGGED'];

export function Bookings() {
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [actionError, setActionError] = useState<string | null>(null);
  const list = useAsync(() => api.admin.listBookings(status || undefined, page), [status, page]);
  const partners = useAsync(() => api.admin.listPartners('APPROVED'), []);
  const [pick, setPick] = useState<Record<string, string>>({});

  async function act(fn: () => Promise<unknown>) {
    setActionError(null);
    try { await fn(); list.reload(); } catch (e) { setActionError(errMsg(e)); }
  }

  const row = (b: AdminBooking) => (
    <tr key={b.id}>
      <td>{b.customerName || b.customerPhone}<br /><small className="muted">{b.customerPhone}</small></td>
      <td>{b.hospitalName}<br /><small className="muted">{b.mobilityRequirement.replaceAll('_', ' ')}{b.isRoundTrip ? ' · round trip' : ' · one way'}</small></td>
      <td>{when(b.scheduledPickupTime)}</td>
      <td><Status value={b.status} /></td>
      <td>{b.carePartnerName ?? '—'}</td>
      <td>{inr(b.finalFare ?? b.quotedFare)}</td>
      <td className="actions">
        {(b.status === 'CONFIRMED' || b.status === 'ASSIGNED') && (
          <>
            <select value={pick[b.id] ?? ''} onChange={(e) => setPick({ ...pick, [b.id]: e.target.value })}>
              <option value="">Select partner…</option>
              {partners.data?.results.map((p) => (
                <option key={p.id} value={p.id}>{p.fullName}{p.isOnline ? ' ●' : ''}</option>
              ))}
            </select>
            <button disabled={!pick[b.id]} onClick={() => act(() => api.admin.assign(b.id, pick[b.id]))}>
              {b.status === 'ASSIGNED' ? 'Reassign' : 'Assign'}
            </button>
          </>
        )}
        {b.status === 'ASSIGNED' && <button onClick={() => act(() => api.admin.unassign(b.id))}>Unassign</button>}
        {b.status === 'COMPLETED' && <button onClick={() => act(() => api.admin.close(b.id))}>Close</button>}
        {!['COMPLETED', 'CLOSED', 'CANCELLED'].includes(b.status) && (
          <button className="danger" onClick={() => {
            const reason = window.prompt('Reason for cancelling this booking?');
            if (reason !== null) void act(() => api.admin.cancel(b.id, reason));
          }}>Cancel</button>
        )}
      </td>
    </tr>
  );

  return (
    <Panel title="Bookings" actions={
      <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
        {STATUSES.map((s) => <option key={s} value={s}>{s ? s.replaceAll('_', ' ') : 'All statuses'}</option>)}
      </select>}>
      <Feedback error={list.error ?? actionError} loading={list.loading} />
      <div className="scroll">
        <table>
          <thead><tr><th>Customer</th><th>Trip</th><th>Pickup</th><th>Status</th><th>Care Partner</th><th>Fare</th><th>Actions</th></tr></thead>
          <tbody>{list.data?.results.map(row)}</tbody>
        </table>
      </div>
      {list.data && list.data.count === 0 && <p className="muted">No bookings match.</p>}
      <Pager page={page} setPage={setPage} next={!!list.data?.next} prev={!!list.data?.previous} />
    </Panel>
  );
}
