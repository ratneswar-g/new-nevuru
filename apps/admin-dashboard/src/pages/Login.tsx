import { useState } from 'react';
import type { ConfirmationResult } from 'firebase/auth';
import { sendCode } from '../firebase';
import { errMsg } from '../ui';

export function Login() {
  const [phone, setPhone] = useState('+91');
  const [code, setCode] = useState('');
  const [confirm, setConfirm] = useState<ConfirmationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    setBusy(true); setError(null);
    try { setConfirm(await sendCode(phone.trim(), 'recaptcha-slot')); } catch (e) { setError(errMsg(e)); }
    setBusy(false);
  }
  async function verify() {
    if (!confirm) return;
    setBusy(true); setError(null);
    try { await confirm.confirm(code.trim()); } catch (e) { setError(errMsg(e)); setBusy(false); }
  }

  return (
    <main className="login">
      <h1>Neravu Operations</h1>
      <p className="muted">Administrator sign-in</p>
      {!confirm ? (
        <>
          <label>Phone number (E.164)
            <input value={phone} onChange={(e) => setPhone(e.target.value)} inputMode="tel" autoComplete="tel" />
          </label>
          <button className="primary" disabled={busy || phone.length < 8} onClick={send}>Send code</button>
        </>
      ) : (
        <>
          <label>6-digit code
            <input value={code} onChange={(e) => setCode(e.target.value)} inputMode="numeric" maxLength={6} />
          </label>
          <button className="primary" disabled={busy || code.length < 6} onClick={verify}>Verify &amp; sign in</button>
        </>
      )}
      {error && <p className="error" role="alert">{error}</p>}
      <div id="recaptcha-slot" />
    </main>
  );
}
