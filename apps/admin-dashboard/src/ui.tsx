import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { ApiError } from '@neravu/api-client';

export const errMsg = (e: unknown): string =>
  e instanceof ApiError ? e.message : e instanceof Error ? e.message : 'Something went wrong.';

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(() => {
    setLoading(true);
    fn().then((d) => { setData(d); setError(null); }).catch((e) => setError(errMsg(e))).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { run(); }, [run]);
  return { data, error, loading, reload: run };
}

export function Panel({ title, actions, children }: { title: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <section className="panel">
      <header className="panel-head"><h2>{title}</h2><div className="row">{actions}</div></header>
      {children}
    </section>
  );
}

export function Status({ value }: { value: string }) {
  const tone =
    ['COMPLETED', 'CLOSED', 'APPROVED', 'RESOLVED'].includes(value) ? 'ok'
      : ['CANCELLED', 'REJECTED', 'SUSPENDED', 'INCIDENT_FLAGGED', 'CRITICAL'].includes(value) ? 'bad'
        : ['REQUESTED', 'QUOTED', 'PENDING_VERIFICATION', 'REPORTED', 'HIGH'].includes(value) ? 'warn' : 'info';
  return <span className={`badge ${tone}`}>{value.replaceAll('_', ' ')}</span>;
}

export function Feedback({ error, loading }: { error: string | null; loading: boolean }) {
  if (error) return <p className="error" role="alert">{error}</p>;
  if (loading) return <p className="muted">Loading…</p>;
  return null;
}

export const inr = (v: string | null | undefined) => (v == null ? '—' : `₹${Number(v).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`);
export const when = (iso: string | null | undefined) =>
  iso ? new Date(iso).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' }) : '—';

export function Pager({ page, setPage, next, prev }: { page: number; setPage: (n: number) => void; next: boolean; prev: boolean }) {
  return (
    <div className="row pager">
      <button disabled={!prev} onClick={() => setPage(page - 1)}>← Prev</button>
      <span className="muted">Page {page}</span>
      <button disabled={!next} onClick={() => setPage(page + 1)}>Next →</button>
    </div>
  );
}
