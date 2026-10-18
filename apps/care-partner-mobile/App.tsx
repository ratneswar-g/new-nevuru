import React, { useCallback, useEffect, useState } from 'react';
import { Alert, SafeAreaView, ScrollView, Text, TextInput, View } from 'react-native';
import type { KycDocumentType, MobilityRequirement, Me, PartnerJob, PartnerSelf, VehicleType } from '@neravu/shared-types';
import { api } from './src/api';
import { AuthGate } from './src/AuthGate';
import { C, s } from './src/theme';
import { Btn, EmergencyNotice, errMsg, ErrorText } from './src/ui';

const DOCS: KycDocumentType[] = ['DRIVING_LICENSE', 'AADHAAR', 'POLICE_VERIFICATION', 'VEHICLE_RC'];
const MOBILITY: MobilityRequirement[] = ['INDEPENDENT', 'WALKER_ASSISTANCE', 'FOLDING_WHEELCHAIR', 'COMPANION_ONLY'];
const VEHICLES: VehicleType[] = ['SEDAN', 'HATCHBACK', 'SUV', 'WHEELCHAIR_ACCESSIBLE'];

// ------------------------------------------------------------- onboarding
function Onboarding({ p, reload }: { p: PartnerSelf; reload: () => void }) {
  const [doc, setDoc] = useState<KycDocumentType>('DRIVING_LICENSE');
  const [docId, setDocId] = useState('');
  const [v, setV] = useState({ reg: '', make: '', model: '', color: '' });
  const [vt, setVt] = useState<VehicleType>('SEDAN');
  const [sup, setSup] = useState<MobilityRequirement[]>(['INDEPENDENT']);
  const [err, setErr] = useState<string | null>(null);
  const act = async (fn: () => Promise<unknown>) => { setErr(null); try { await fn(); reload(); } catch (e) { setErr(errMsg(e)); } };

  return (
    <View style={{ gap: 12 }}>
      <View style={s.card}>
        <Text style={s.h2}>Verification: {p.status.replaceAll('_', ' ')}</Text>
        <Text style={s.muted}>Submitted documents: {p.documentTypes.join(', ') || 'none yet'}. Neravu reviews documents and your vehicle before you can take journeys.</Text>
        <View style={s.row}>{DOCS.map((d) => <Text key={d} onPress={() => setDoc(d)} style={[s.chip, doc === d && s.chipOn, { color: doc === d ? '#fff' : C.primary }]}>{d.replaceAll('_', ' ')}</Text>)}</View>
        <TextInput style={s.input} placeholder="Document number" value={docId} onChangeText={setDocId} autoCapitalize="characters" />
        <Btn label="Submit document" disabled={!docId.trim()} onPress={() => act(async () => { await api.partner.submitKyc(doc, docId.trim()); setDocId(''); })} />
        <Text style={s.muted}>Photo upload is not built yet; only the document number is recorded.</Text>
      </View>
      <View style={s.card}>
        <Text style={s.h2}>Vehicles</Text>
        {p.vehicles.map((x) => <Text key={x.id} style={s.text}>{x.registrationNumber} · {x.make} {x.model} · {x.isVerified ? 'verified' : 'awaiting inspection'}</Text>)}
        <TextInput style={s.input} placeholder="Registration no. e.g. KA01AB1234" autoCapitalize="characters" value={v.reg} onChangeText={(t) => setV({ ...v, reg: t })} />
        <TextInput style={s.input} placeholder="Make" value={v.make} onChangeText={(t) => setV({ ...v, make: t })} />
        <TextInput style={s.input} placeholder="Model" value={v.model} onChangeText={(t) => setV({ ...v, model: t })} />
        <TextInput style={s.input} placeholder="Colour" value={v.color} onChangeText={(t) => setV({ ...v, color: t })} />
        <View style={s.row}>{VEHICLES.map((t) => <Text key={t} onPress={() => setVt(t)} style={[s.chip, vt === t && s.chipOn, { color: vt === t ? '#fff' : C.primary }]}>{t.replaceAll('_', ' ')}</Text>)}</View>
        <Text style={s.muted}>Mobility needs this vehicle can safely support:</Text>
        <View style={s.row}>{MOBILITY.map((m) => { const on = sup.includes(m); return <Text key={m} onPress={() => setSup(on ? sup.filter((x) => x !== m) : [...sup, m])} style={[s.chip, on && s.chipOn, { color: on ? '#fff' : C.primary }]}>{m.replaceAll('_', ' ')}</Text>; })}</View>
        <Btn label="Add vehicle" disabled={!v.reg || !v.make || !v.model || sup.length === 0} onPress={() => act(async () => {
          await api.partner.addVehicle({ registrationNumber: v.reg.trim(), make: v.make.trim(), model: v.model.trim(), color: v.color.trim(), vehicleType: vt, supportedMobility: sup }); setV({ reg: '', make: '', model: '', color: '' });
        })} />
      </View>
      <ErrorText msg={err} />
    </View>
  );
}

// --------------------------------------------------------------- job card
function JobCard({ j, reload }: { j: PartnerJob; reload: () => void }) {
  const [code, setCode] = useState('');
  const [notes, setNotes] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const act = async (fn: () => Promise<unknown>) => { setErr(null); try { await fn(); setCode(''); reload(); } catch (e) { setErr(errMsg(e)); } };
  const needsDropoff = j.status === 'RETURN_TRANSIT' || (j.status === 'ACCOMPANIMENT' && !j.isRoundTrip);

  return (
    <View style={s.card}>
      <Text style={s.h2}>{j.customer.firstName} → {j.hospitalName}</Text>
      <Text style={s.text}>Status: {j.status.replaceAll('_', ' ')}</Text>
      <Text style={s.muted}>Pickup: {j.pickupAddress}{j.pickupLandmark ? ` (${j.pickupLandmark})` : ''}</Text>
      <Text style={s.muted}>Hospital: {j.hospitalAddress}</Text>
      <Text style={s.muted}>{new Date(j.scheduledPickupTime).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} · {j.mobilityRequirement.replaceAll('_', ' ')} · {j.isRoundTrip ? 'round trip' : 'one way'}</Text>
      {j.customer.accessibilityNotes ? <Text style={s.muted}>Assistance notes: {j.customer.accessibilityNotes}</Text> : null}
      <Text style={s.muted}>Customer phone: {j.customer.phoneNumber}</Text>

      {j.status === 'ASSIGNED' && <Btn label="I have arrived at pickup" onPress={() => act(() => api.partner.arrive(j.id))} />}
      {j.status === 'ARRIVED' && (<>
        <Text style={s.muted}>Ask the customer to open their app, generate the pickup code, and read it to you.</Text>
        <TextInput style={s.input} placeholder="4-digit pickup code" keyboardType="number-pad" maxLength={4} value={code} onChangeText={setCode} />
        <Btn label="Verify & start journey" disabled={code.length !== 4} onPress={() => act(() => api.partner.verifyPickup(j.id, code))} />
      </>)}
      {j.status === 'IN_TRANSIT_HOSPITAL' && <Btn label="Arrived at hospital" onPress={() => act(() => api.partner.arriveHospital(j.id))} />}
      {j.status === 'ACCOMPANIMENT' && j.isRoundTrip && (<>
        <TextInput style={s.input} placeholder="Non-clinical notes (optional)" value={notes} onChangeText={setNotes} />
        <Btn label="Start return journey" onPress={() => act(() => api.partner.startReturn(j.id, notes || undefined))} />
      </>)}
      {needsDropoff && (<>
        <Text style={s.muted}>At drop-off, ask the customer to generate the drop-off code.</Text>
        <TextInput style={s.input} placeholder="4-digit drop-off code" keyboardType="number-pad" maxLength={4} value={code} onChangeText={setCode} />
        <Btn label="Verify & complete journey" disabled={code.length !== 4} onPress={() => act(() => api.partner.complete(j.id, code, notes || undefined))} />
      </>)}
      {['ASSIGNED', 'ARRIVED', 'IN_TRANSIT_HOSPITAL', 'ACCOMPANIMENT', 'RETURN_TRANSIT'].includes(j.status) && (
        <Btn label="SOS / Emergency" kind="danger" onPress={() => Alert.alert('Emergency', 'This alerts Neravu operations and pauses the journey. Call 108/112 yourself for any medical emergency.', [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Send alert', style: 'destructive', onPress: () => act(async () => { const r = await api.partner.emergency(j.id); Alert.alert('Alert sent', r.guidance); }) },
        ])} />)}
      {j.status === 'INCIDENT_FLAGGED' && <Text style={s.error}>Journey paused by an incident. Wait for Neravu operations. Call 108/112 for medical emergencies.</Text>}
      <ErrorText msg={err} />
    </View>
  );
}

// -------------------------------------------------------------------- home
function Home({ me, signOut }: { me: Me; signOut: () => void }) {
  const [p, setP] = useState<PartnerSelf | null>(null);
  const [jobs, setJobs] = useState<PartnerJob[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const self = await api.partner.me(); setP(self);
      if (self.status === 'APPROVED') setJobs((await api.partner.listJobs()).results);
      setErr(null);
    } catch (e) { setErr(errMsg(e)); }
  }, []);
  useEffect(() => { void load(); const t = setInterval(load, 15000); return () => clearInterval(t); }, [load]);

  const toggle = async () => { if (!p) return; try { await api.partner.setDuty(!p.isOnline); await load(); } catch (e) { setErr(errMsg(e)); } };

  return (
    <SafeAreaView style={s.screen}>
      <View style={s.header}><Text style={s.headerTitle}>Neravu Partner · {me.firstName}</Text></View>
      <ScrollView contentContainerStyle={s.pad}>
        <EmergencyNotice />
        <ErrorText msg={err} />
        {p && p.status !== 'APPROVED' && <Onboarding p={p} reload={load} />}
        {p && p.status === 'REJECTED' && <Text style={s.error}>Your application was not approved. Contact Neravu support.</Text>}
        {p && p.status === 'APPROVED' && (<>
          <View style={s.card}>
            <Text style={s.h2}>Duty: {p.isOnline ? 'ONLINE' : 'OFFLINE'}</Text>
            <Btn label={p.isOnline ? 'Go offline' : 'Go online'} kind={p.isOnline ? 'alt' : 'primary'} onPress={toggle} />
          </View>
          <Text style={s.h2}>Your journeys</Text>
          {jobs.map((j) => <JobCard key={j.id} j={j} reload={load} />)}
          {jobs.length === 0 && <Text style={s.muted}>No journeys assigned yet. Neravu operations assigns journeys to you.</Text>}
        </>)}
        <Btn label="Sign out" kind="alt" onPress={signOut} />
      </ScrollView>
    </SafeAreaView>
  );
}

export default function App() {
  return <AuthGate role="CARE_PARTNER" title="Neravu Partner — Sign in">{(me, out) => <Home me={me} signOut={out} />}</AuthGate>;
}
