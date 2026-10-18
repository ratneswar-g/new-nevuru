import { useState } from 'react';
import { api } from '../api';
import { errMsg, Feedback, Panel, Status, useAsync, when } from '../ui';

export function Incidents() {
  const [open, setOpen] = useState(true);
  const list = useAsync(() => api.admin.listIncidents(open ? { status: 'REPORTED' } : undefined), [open]);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [actionError, setActionError] = useState<string | null>(null);

  async function resolve(id: string, action: 'RESUME' | 'CANCEL') {
    setActionError(null);
    try { await api.admin.resolveIncident(id, notes[id] ?? '', action); list.reload(); } catch (e) { setActionError(errMsg(e)); }
  }

  return (
    <Panel title="Incidents &amp; emergencies" actions={
      <label className="row"><input type="checkbox" checked={open} onChange={(e) => setOpen(e.target.checked)} /> Open only</label>}>
      <p className="notice">Neravu is not an ambulance service. For medical emergencies, ensure the family and driver have called 108 / 112.</p>
      <Feedback error={list.error ?? actionError} loading={list.loading} />
      {list.data?.results.map((i) => (
        <article className="item" key={i.id}>
          <div className="row between">
            <b>{i.category.replaceAll('_', ' ')}</b>
            <span className="row"><Status value={i.priority} /><Status value={i.status} /></span>
          </div>
          <p>{i.narrative}</p>
          <p className="muted">Booking {i.bookingId.slice(0, 8)} · reported by {i.reporterRole} · {when(i.createdAt)}</p>
          {i.status === 'REPORTED' ? (
            <>
              <textarea placeholder="Resolution notes (required)" value={notes[i.id] ?? ''}
                        onChange={(e) => setNotes({ ...notes, [i.id]: e.target.value })} />
              <div className="row">
                <button className="primary" disabled={!(notes[i.id] ?? '').trim()} onClick={() => resolve(i.id, 'RESUME')}>Resolve &amp; resume journey</button>
                <button className="danger" disabled={!(notes[i.id] ?? '').trim()} onClick={() => resolve(i.id, 'CANCEL')}>Resolve &amp; cancel booking</button>
              </div>
            </>
          ) : <p><b>Resolution:</b> {i.resolutionNotes}</p>}
        </article>
      ))}
      {list.data && list.data.count === 0 && <p className="muted">No incidents.</p>}
    </Panel>
  );
}
