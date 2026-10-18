import { useState } from 'react';
import type { MobilityRequirement, RateCardInput } from '@neravu/shared-types';
import { api } from '../api';
import { errMsg, Feedback, inr, Panel, Status, useAsync, when } from '../ui';

const TIERS: MobilityRequirement[] = ['INDEPENDENT', 'WALKER_ASSISTANCE', 'FOLDING_WHEELCHAIR', 'COMPANION_ONLY'];
type Form = Record<'name' | 'baseFare' | 'baseDistanceKm' | 'perKmRate' | 'perMinuteWaitingRate', string> &
  { tiers: Record<MobilityRequirement, string> };
// Intentionally blank: amounts are business decisions entered by an administrator, never defaulted here.
const blank = (): Form => ({
  name: '', baseFare: '', baseDistanceKm: '', perKmRate: '', perMinuteWaitingRate: '',
  tiers: { INDEPENDENT: '', WALKER_ASSISTANCE: '', FOLDING_WHEELCHAIR: '', COMPANION_ONLY: '' },
});

export function RateCards() {
  const list = useAsync(() => api.admin.listRateCards(), []);
  const [form, setForm] = useState<Form>(blank());
  const [formError, setFormError] = useState<string | null>(null);
  const complete = form.name.trim() && form.baseFare !== '' && form.baseDistanceKm !== '' &&
    form.perKmRate !== '' && form.perMinuteWaitingRate !== '' && TIERS.every((t) => form.tiers[t] !== '');

  async function create() {
    setFormError(null);
    const input: RateCardInput = {
      name: form.name.trim(), baseFare: form.baseFare, baseDistanceKm: form.baseDistanceKm,
      perKmRate: form.perKmRate, perMinuteWaitingRate: form.perMinuteWaitingRate,
      mobilityTierSurcharges: form.tiers, effectiveFrom: new Date().toISOString(),
    };
    try { await api.admin.createRateCard(input); setForm(blank()); list.reload(); } catch (e) { setFormError(errMsg(e)); }
  }
  async function activate(id: string) {
    if (!window.confirm('Activate this rate card? It supersedes the current one for NEW bookings only.')) return;
    try { await api.admin.activateRateCard(id); list.reload(); } catch (e) { setFormError(errMsg(e)); }
  }
  const num = (k: keyof Omit<Form, 'tiers' | 'name'>, label: string) => (
    <label>{label}<input type="number" min="0" step="0.01" value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} /></label>
  );

  return (
    <>
      <Panel title="Rate cards (versioned)">
        <Feedback error={list.error} loading={list.loading} />
        <table>
          <thead><tr><th>v</th><th>Name</th><th>Base</th><th>Incl. km</th><th>Per km</th><th>Per min wait</th><th>Surcharges</th><th>Status</th><th /></tr></thead>
          <tbody>
            {list.data?.results.map((c) => (
              <tr key={c.id}>
                <td>{c.version}</td><td>{c.name}<br /><small className="muted">{when(c.effectiveFrom)}</small></td>
                <td>{inr(c.baseFare)}</td><td>{c.baseDistanceKm}</td><td>{inr(c.perKmRate)}</td><td>{inr(c.perMinuteWaitingRate)}</td>
                <td><small>{TIERS.map((t) => `${t.replaceAll('_', ' ')}: ${inr(c.mobilityTierSurcharges[t])}`).join(' · ')}</small></td>
                <td>{c.isActive ? <Status value="APPROVED" /> : <span className="muted">inactive</span>}</td>
                <td>{!c.isActive && <button onClick={() => activate(c.id)}>Activate</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.data && list.data.count === 0 && <p className="notice">No rate card exists. Customers cannot receive quotes or book until one is created and activated.</p>}
      </Panel>
      <Panel title="Create new version">
        <p className="muted">Rate cards are immutable once created. Enter every amount explicitly (INR).</p>
        <div className="form-grid">
          <label>Name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
          {num('baseFare', 'Base fare')}
          {num('baseDistanceKm', 'Included distance (km)')}
          {num('perKmRate', 'Per km beyond included')}
          {num('perMinuteWaitingRate', 'Per minute accompaniment / waiting')}
          {TIERS.map((t) => (
            <label key={t}>Surcharge: {t.replaceAll('_', ' ')}
              <input type="number" min="0" step="0.01" value={form.tiers[t]}
                     onChange={(e) => setForm({ ...form, tiers: { ...form.tiers, [t]: e.target.value } })} />
            </label>
          ))}
        </div>
        {formError && <p className="error" role="alert">{formError}</p>}
        <button className="primary" disabled={!complete} onClick={create}>Create rate card</button>
      </Panel>
    </>
  );
}
