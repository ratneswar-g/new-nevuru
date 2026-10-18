import { api } from '../api';
import { Feedback, Panel, useAsync } from '../ui';

export function Dashboard() {
  const { data, error, loading, reload } = useAsync(() => api.admin.dashboard(), []);
  return (
    <Panel title="Operations overview" actions={<button onClick={reload}>Refresh</button>}>
      <Feedback error={error} loading={loading} />
      {data && (
        <>
          <div className="cards">
            <div className="card"><b>{data.partnersPendingVerification}</b><span>Partners awaiting verification</span></div>
            <div className="card"><b>{data.partnersOnline}</b><span>Approved partners online</span></div>
            <div className={`card ${data.openIncidents ? 'alert' : ''}`}><b>{data.openIncidents}</b><span>Open incidents</span></div>
          </div>
          <h3>Bookings by status</h3>
          <table>
            <tbody>
              {Object.entries(data.bookingsByStatus).map(([s, n]) => (
                <tr key={s}><td>{s.replaceAll('_', ' ')}</td><td>{n}</td></tr>
              ))}
              {Object.keys(data.bookingsByStatus).length === 0 && <tr><td className="muted">No bookings yet.</td></tr>}
            </tbody>
          </table>
        </>
      )}
    </Panel>
  );
}
