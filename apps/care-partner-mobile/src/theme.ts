import { StyleSheet } from 'react-native';

export const C = { primary: '#1769AA', secondary: '#62B6E8', bg: '#EAF5FF', navy: '#172B4D', bad: '#b3261e', line: '#d5e3f0', muted: '#5b6b85' };

export const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  pad: { padding: 16, gap: 12 },
  header: { backgroundColor: C.primary, padding: 16 },
  headerTitle: { color: '#fff', fontSize: 20, fontWeight: '700' },
  card: { backgroundColor: '#fff', borderRadius: 10, padding: 14, gap: 6 },
  h2: { color: C.navy, fontSize: 17, fontWeight: '700' },
  text: { color: C.navy, fontSize: 15 },
  muted: { color: C.muted, fontSize: 13 },
  error: { color: C.bad, fontSize: 14 },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: C.line, borderRadius: 8, padding: 10, fontSize: 16, color: C.navy },
  btn: { backgroundColor: C.primary, borderRadius: 8, padding: 12, alignItems: 'center' },
  btnAlt: { backgroundColor: '#fff', borderWidth: 1, borderColor: C.primary, borderRadius: 8, padding: 12, alignItems: 'center' },
  btnDanger: { backgroundColor: C.bad, borderRadius: 8, padding: 14, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  btnAltText: { color: C.primary, fontWeight: '700', fontSize: 15 },
  disabled: { opacity: 0.5 },
  notice: { backgroundColor: '#fff3cd', padding: 10, borderRadius: 8 },
  noticeText: { color: '#856404', fontSize: 13 },
  row: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  chip: { paddingVertical: 6, paddingHorizontal: 10, borderRadius: 999, borderWidth: 1, borderColor: C.primary },
  chipOn: { backgroundColor: C.primary },
  otp: { fontSize: 40, fontWeight: '800', letterSpacing: 10, color: C.primary, textAlign: 'center' },
});
