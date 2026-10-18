import { useState } from 'react';
import { api } from '../api';
import { errMsg, Feedback, Panel, Status, useAsync, when } from '../ui';

export function Partners() {
  const [status, setStatus] = useState('PENDING_VERIFICATION');
  const [actionError, setActionError] = useState<string | null>(null);
  const list = useAsync(() => api.admin.listPartners(status || undefined), [status]);

  async function act(fn: () => Promise<unknown>) {
    setActionError(null);
    try { await fn(); list.reload(); } catch (e) { setActionError(errMsg(e)); }
  }

  return (
    <Panel title="Care Partners" actions={
      <select value={status} onChange={(e) => setStatus(e.target.value)}>
        {['', 'PENDING_VERIFICATION', 'APPROVED', 'REJECTED', 'SUSPENDED'].map((s) =>
          <option key={s} value={s}>{s ? s.replaceAll('_', ' ') : 'All'}</option>)}
      </select>}>
      <Feedback error={list.error ?? actionError} loading={list.loading} />
      {list.data?.results.map((p) => (
        <article className="item" key={p.id}>
          <div className="row between">
            <div><b>{p.fullName || p.phoneNumber}</b> <small className="muted">{p.phoneNumber}</small></div>
            <Status value={p.status} />
          </div>
          <p className="muted">
            KYC submitted: {when(p.kycSubmittedAt)} · Documents: {p.documentTypes.join(', ') || 'none'} · Trips: {p.completedTripsCount}
          </p>
          <ul className="plain">
            {p.vehicles.map((v) => (
              <li key={v.id} className="row between">
                <span>{v.registrationNumber} — {v.make} {v.model} ({v.vehicleType}) · supports {v.supportedMobility.join(', ') || 'nothing'}</span>
                {v.isVerified ? <Status value="APPROVED" /> : <button onClick={() => act(() => api.admin.verifyVehicle(v.id))}>Mark verified</button>}
              </li>
            ))}
            {p.vehicles.length === 0 && <li className="muted">No vehicles registered.</li>}
          </ul>
          <div className="row">
            {(p.status === 'PENDING_VERIFICATION' || p.status === 'SUSPENDED') &&
              <button className="primary" onClick={() => act(() => api.admin.approvePartner(p.id))}>Approve</button>}
            {p.status === 'PENDING_VERIFICATION' &&
              <button className="danger" onClick={() => act(() => api.admin.rejectPartner(p.id))}>Reject</button>}
            {p.status === 'APPROVED' &&
              <button className="danger" onClick={() => act(() => api.admin.suspendPartner(p.id))}>Suspend</button>}
          </div>
        </article>
      ))}
      {list.data && list.data.count === 0 && <p className="muted">No Care Partners in this state.</p>}
    </Panel>
  );
}
