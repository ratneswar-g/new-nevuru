import React, { useCallback, useEffect, useState } from 'react';
import { Alert, SafeAreaView, ScrollView, Text, TextInput, View } from 'react-native';
import type { BookingStatus, CustomerBooking, CustomerProfileDto, MobilityRequirement, Me, QuoteResult } from '@neravu/shared-types';
import { api } from './src/api';
import { AuthGate } from './src/AuthGate';
import { C, s } from './src/theme';
import { Btn, EmergencyNotice, errMsg, ErrorText, inr } from './src/ui';

const MOBILITY: MobilityRequirement[] = ['INDEPENDENT', 'WALKER_ASSISTANCE', 'FOLDING_WHEELCHAIR', 'COMPANION_ONLY'];
const LIVE: BookingStatus[] = ['ARRIVED', 'IN_TRANSIT_HOSPITAL', 'ACCOMPANIMENT', 'RETURN_TRANSIT', 'INCIDENT_FLAGGED'];

// ------------------------------------------------------------------ profile
function ProfileForm({ onSaved }: { onSaved: () => void }) {
  const [f, setF] = useState<CustomerProfileDto>({ emergencyContactName: '', emergencyContactPhone: '+91', emergencyContactRelation: '', defaultMobilityNeed: 'INDEPENDENT', accessibilityNotes: '' });
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null);
  const ok = f.emergencyContactName.trim() && f.emergencyContactPhone.length > 8 && f.emergencyContactRelation.trim();
  return (
    <View style={s.card}>
      <Text style={s.h2}>Emergency contact (required to book)</Text>
      <TextInput style={s.input} placeholder="Contact name" value={f.emergencyContactName} onChangeText={(v) => setF({ ...f, emergencyContactName: v })} />
      <TextInput style={s.input} placeholder="Contact phone" keyboardType="phone-pad" value={f.emergencyContactPhone} onChangeText={(v) => setF({ ...f, emergencyContactPhone: v })} />
      <TextInput style={s.input} placeholder="Relationship (e.g. Son)" value={f.emergencyContactRelation} onChangeText={(v) => setF({ ...f, emergencyContactRelation: v })} />
      <TextInput style={s.input} placeholder="Non-clinical assistance notes (e.g. uses folding walker)" maxLength={300} value={f.accessibilityNotes} onChangeText={(v) => setF({ ...f, accessibilityNotes: v })} />
      <Text style={s.muted}>Do not enter medical history or diagnoses.</Text>
      <Btn label="Save profile" busy={busy} disabled={!ok} onPress={async () => { setBusy(true); setErr(null); try { await api.customer.saveProfile(f); onSaved(); } catch (e) { setErr(errMsg(e)); } setBusy(false); }} />
      <ErrorText msg={err} />
    </View>
  );
}

// -------------------------------------------------------------- new booking
function NewBooking({ onCreated }: { onCreated: () => void }) {
  const [f, setF] = useState({ pickupAddress: '', pLat: '', pLng: '', hospitalName: '', hospitalAddress: '', hLat: '', hLng: '', when: '' });
  const [mobility, setMobility] = useState<MobilityRequirement>('INDEPENDENT');
  const [round, setRound] = useState(true);
  const [quote, setQuote] = useState<QuoteResult | null>(null);
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null);
  const trip = () => ({ pickupAddress: f.pickupAddress, pickupLatitude: f.pLat, pickupLongitude: f.pLng, hospitalName: f.hospitalName, hospitalAddress: f.hospitalAddress, hospitalLatitude: f.hLat, hospitalLongitude: f.hLng, mobilityRequirement: mobility, isRoundTrip: round });
  const complete = f.pickupAddress && f.pLat && f.pLng && f.hospitalName && f.hospitalAddress && f.hLat && f.hLng;
  const field = (k: keyof typeof f, ph: string, kb?: 'numeric') => <TextInput style={s.input} placeholder={ph} keyboardType={kb === 'numeric' ? 'numbers-and-punctuation' : 'default'} value={f[k]} onChangeText={(v) => { setF({ ...f, [k]: v }); setQuote(null); }} />;
  const run = async (fn: () => Promise<void>) => { setBusy(true); setErr(null); try { await fn(); } catch (e) { setErr(errMsg(e)); } setBusy(false); };

  return (
    <View style={s.card}>
      <Text style={s.h2}>Request a journey</Text>
      {field('pickupAddress', 'Pickup address')}
      <View style={s.row}>{field('pLat', 'Pickup lat', 'numeric')}{field('pLng', 'Pickup lng', 'numeric')}</View>
      {field('hospitalName', 'Hospital name')}{field('hospitalAddress', 'Hospital address')}
      <View style={s.row}>{field('hLat', 'Hospital lat', 'numeric')}{field('hLng', 'Hospital lng', 'numeric')}</View>
      <Text style={s.muted}>Map search is not built yet; enter coordinates.</Text>
      {field('when', 'Pickup time, ISO e.g. 2026-10-20T09:30:00+05:30')}
      <View style={s.row}>{MOBILITY.map((m) => (
        <Text key={m} onPress={() => { setMobility(m); setQuote(null); }} style={[s.chip, mobility === m && s.chipOn, { color: mobility === m ? '#fff' : C.primary }]}>{m.replaceAll('_', ' ')}</Text>))}</View>
      <View style={s.row}>
        <Text onPress={() => { setRound(true); setQuote(null); }} style={[s.chip, round && s.chipOn, { color: round ? '#fff' : C.primary }]}>Round trip</Text>
        <Text onPress={() => { setRound(false); setQuote(null); }} style={[s.chip, !round && s.chipOn, { color: !round ? '#fff' : C.primary }]}>One way</Text>
      </View>
      <Btn label="Get fare" kind="alt" busy={busy} disabled={!complete} onPress={() => run(async () => setQuote(await api.customer.quote(trip())))} />
      {quote && (
        <View style={s.notice}>
          <Text style={s.text}>Estimated fare: {inr(quote.totalFare)}</Text>
          <Text style={s.muted}>Base {inr(quote.baseFare)} · distance {inr(quote.distanceFare)} · assistance {inr(quote.mobilitySurcharge)}</Text>
          <Text style={s.muted}>{quote.note}</Text>
        </View>)}
      <Btn label="Book this journey" busy={busy} disabled={!quote || !f.when} onPress={() => run(async () => {
        const b = await api.customer.createBooking({ ...trip(), scheduledPickupTime: new Date(f.when).toISOString() });
        await api.customer.confirm(b.id); onCreated();
      })} />
      <ErrorText msg={err} />
    </View>
  );
}

// ------------------------------------------------------------ booking card
function BookingCard({ b, reload }: { b: CustomerBooking; reload: () => void }) {
  const [otp, setOtp] = useState<{ type: string; code: string } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const act = async (fn: () => Promise<void>) => { setErr(null); try { await fn(); reload(); } catch (e) { setErr(errMsg(e)); } };
  const live = LIVE.includes(b.status);
  const gen = (type: 'PICKUP' | 'DROPOFF') => act(async () => { const r = await api.customer.issueOtp(b.id, type); setOtp({ type, code: r.code }); });

  return (
    <View style={s.card}>
      <Text style={s.h2}>{b.hospitalName}</Text>
      <Text style={s.text}>Status: {b.status.replaceAll('_', ' ')}</Text>
      <Text style={s.muted}>{new Date(b.scheduledPickupTime).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} · {b.isRoundTrip ? 'round trip' : 'one way'} · {inr(b.finalFare ?? b.quotedFare)}</Text>
      {b.carePartner && <Text style={s.text}>Care Partner: {b.carePartner.firstName} ({b.carePartner.phoneNumber}){b.carePartner.vehicle ? ` · ${b.carePartner.vehicle.color} ${b.carePartner.vehicle.make} ${b.carePartner.vehicle.registrationNumber}` : ''}</Text>}
      {b.status === 'ARRIVED' && !b.pickupVerified && <Btn label="Generate pickup code" onPress={() => gen('PICKUP')} />}
      {(b.status === 'RETURN_TRANSIT' || (b.status === 'ACCOMPANIMENT' && !b.isRoundTrip)) && !b.dropoffVerified && <Btn label="Generate drop-off code" onPress={() => gen('DROPOFF')} />}
      {otp && <View style={s.notice}><Text style={s.noticeText}>Share this {otp.type.toLowerCase()} code ONLY with your Care Partner, in person:</Text><Text style={s.otp}>{otp.code}</Text></View>}
      {['QUOTED', 'CONFIRMED', 'ASSIGNED'].includes(b.status) && <Btn label="Cancel booking" kind="alt" onPress={() => act(() => api.customer.cancel(b.id, 'Cancelled by customer').then(() => undefined))} />}
      {b.status === 'QUOTED' && <Btn label="Confirm booking" onPress={() => act(() => api.customer.confirm(b.id).then(() => undefined))} />}
      {(live || b.status === 'ASSIGNED') && b.status !== 'INCIDENT_FLAGGED' && (
        <Btn label="SOS / Emergency" kind="danger" onPress={() => Alert.alert('Emergency', 'This alerts Neravu operations and pauses the journey. It does NOT call an ambulance — call 108/112 now if you need medical help.', [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Send alert', style: 'destructive', onPress: () => act(async () => { const r = await api.customer.emergency(b.id); Alert.alert('Alert sent', r.guidance); }) },
        ])} />)}
      {b.status === 'INCIDENT_FLAGGED' && <Text style={s.error}>Neravu operations has been alerted. If this is a medical emergency, call 108 or 112 now.</Text>}
      <ErrorText msg={err} />
    </View>
  );
}

// --------------------------------------------------------------------- home
function Home({ me, signOut }: { me: Me; signOut: () => void }) {
  const [hasProfile, setHasProfile] = useState(me.hasCustomerProfile);
  const [bookings, setBookings] = useState<CustomerBooking[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const load = useCallback(async () => { try { setBookings((await api.customer.listBookings()).results); setErr(null); } catch (e) { setErr(errMsg(e)); } }, []);
  useEffect(() => { void load(); const t = setInterval(load, 15000); return () => clearInterval(t); }, [load]);

  return (
    <SafeAreaView style={s.screen}>
      <View style={s.header}><Text style={s.headerTitle}>Neravu · Hello {me.firstName}</Text></View>
      <ScrollView contentContainerStyle={s.pad}>
        <EmergencyNotice />
        <ErrorText msg={err} />
        {!hasProfile ? <ProfileForm onSaved={() => setHasProfile(true)} /> : <NewBooking onCreated={load} />}
        <Text style={s.h2}>Your journeys</Text>
        {bookings.map((b) => <BookingCard key={b.id} b={b} reload={load} />)}
        {bookings.length === 0 && <Text style={s.muted}>No journeys yet.</Text>}
        <Btn label="Sign out" kind="alt" onPress={signOut} />
      </ScrollView>
    </SafeAreaView>
  );
}

export default function App() {
  return <AuthGate role="CUSTOMER" title="Neravu — Sign in">{(me, out) => <Home me={me} signOut={out} />}</AuthGate>;
}
