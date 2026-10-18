import { useState } from 'react';
import { api } from '../api';
import { Feedback, Pager, Panel, useAsync, when } from '../ui';

export function Audit() {
  const [action, setAction] = useState('');
  const [resourceId, setResourceId] = useState('');
  const [page, setPage] = useState(1);
  const list = useAsync(() => api.admin.listAuditLogs({
    action: action || undefined, resourceId: resourceId || undefined, page,
  }), [action, resourceId, page]);

  return (
    <Panel title="Audit log (append-only)" actions={
      <>
        <input placeholder="Action e.g. BOOKING_STATUS_CHANGED" value={action} onChange={(e) => { setAction(e.target.value.trim()); setPage(1); }} />
        <input placeholder="Resource UUID" value={resourceId} onChange={(e) => { setResourceId(e.target.value.trim()); setPage(1); }} />
      </>}>
      <Feedback error={list.error} loading={list.loading} />
      <div className="scroll">
        <table>
          <thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Resource</th><th>Change</th></tr></thead>
          <tbody>
            {list.data?.results.map((a) => (
              <tr key={a.id}>
                <td>{when(a.timestamp)}</td>
                <td>{a.actorRole || 'system'}<br /><small className="muted">{a.actorId?.slice(0, 8)}</small></td>
                <td>{a.action}</td>
                <td>{a.resourceType}<br /><small className="muted">{a.resourceId.slice(0, 8)}</small></td>
                <td><small>{JSON.stringify(a.previousState) !== '{}' && <>{JSON.stringify(a.previousState)} → </>}{JSON.stringify(a.newState)}</small></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pager page={page} setPage={setPage} next={!!list.data?.next} prev={!!list.data?.previous} />
    </Panel>
  );
}
