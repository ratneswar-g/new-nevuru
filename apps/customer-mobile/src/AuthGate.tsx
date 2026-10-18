import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Text, TextInput, View } from 'react-native';
import auth, { type FirebaseAuthTypes } from '@react-native-firebase/auth';
import type { Me } from '@neravu/shared-types';
import { ApiError } from '@neravu/api-client';
import { api } from './api';
import { s } from './theme';
import { Btn, errMsg, ErrorText } from './ui';

/** Phone sign-in -> load Neravu account -> register as CUSTOMER if none exists. */
export function AuthGate({ role, title, children }: {
  role: 'CUSTOMER' | 'CARE_PARTNER'; title: string; children: (me: Me, signOut: () => void) => React.ReactElement;
}) {
  const [fbUser, setFbUser] = useState<FirebaseAuthTypes.User | null | undefined>(undefined);
  const [me, setMe] = useState<Me | null>(null);
  const [needsRegister, setNeedsRegister] = useState(false);
  const [phone, setPhone] = useState('+91');
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [confirm, setConfirm] = useState<FirebaseAuthTypes.ConfirmationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => auth().onAuthStateChanged(setFbUser), []);

  useEffect(() => {
    if (!fbUser) { setMe(null); setNeedsRegister(false); return; }
    let live = true;
    api.me().then((m) => live && setMe(m)).catch((e) => {
      if (!live) return;
      if (e instanceof ApiError && e.status === 401) setNeedsRegister(true); else setError(errMsg(e));
    });
    return () => { live = false; };
  }, [fbUser]);

  const run = async (fn: () => Promise<void>) => { setBusy(true); setError(null); try { await fn(); } catch (e) { setError(errMsg(e)); } setBusy(false); };
  const signOut = () => { void auth().signOut(); setConfirm(null); setCode(''); };

  if (fbUser === undefined) return <View style={s.screen}><ActivityIndicator style={{ marginTop: 80 }} /></View>;

  if (!fbUser) {
    return (
      <View style={[s.screen, s.pad]}>
        <Text style={s.h2}>{title}</Text>
        {!confirm ? (
          <>
            <Text style={s.muted}>Phone number (with country code)</Text>
            <TextInput style={s.input} value={phone} onChangeText={setPhone} keyboardType="phone-pad" autoComplete="tel" />
            <Btn label="Send code" busy={busy} disabled={phone.length < 8} onPress={() => run(async () => setConfirm(await auth().signInWithPhoneNumber(phone.trim())))} />
          </>
        ) : (
          <>
            <Text style={s.muted}>Enter the 6-digit code sent by SMS</Text>
            <TextInput style={s.input} value={code} onChangeText={setCode} keyboardType="number-pad" maxLength={6} />
            <Btn label="Verify" busy={busy} disabled={code.length < 6} onPress={() => run(async () => { await confirm.confirm(code.trim()); })} />
          </>
        )}
        <ErrorText msg={error} />
      </View>
    );
  }

  if (needsRegister) {
    return (
      <View style={[s.screen, s.pad]}>
        <Text style={s.h2}>Create your account</Text>
        <TextInput style={s.input} placeholder="First name" value={name} onChangeText={setName} />
        <Btn label="Continue" busy={busy} disabled={!name.trim()} onPress={() => run(async () => {
          setMe(await api.register({ role, firstName: name.trim() })); setNeedsRegister(false);
        })} />
        <Btn label="Sign out" kind="alt" onPress={signOut} />
        <ErrorText msg={error} />
      </View>
    );
  }

  if (!me) return <View style={[s.screen, s.pad]}><ActivityIndicator /><ErrorText msg={error} /><Btn label="Sign out" kind="alt" onPress={signOut} /></View>;

  if (me.role !== role) {
    return (
      <View style={[s.screen, s.pad]}>
        <Text style={s.error}>This phone number is registered as {me.role}. Use the matching Neravu app.</Text>
        <Btn label="Sign out" kind="alt" onPress={signOut} />
      </View>
    );
  }
  return children(me, signOut);
}
