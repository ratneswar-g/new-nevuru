import React from 'react';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';
import { ApiError } from '@neravu/api-client';
import { s } from './theme';

export const errMsg = (e: unknown): string =>
  e instanceof ApiError ? e.message : e instanceof Error ? e.message : 'Something went wrong.';

export const inr = (v?: string | null) => (v == null ? '—' : `₹${Number(v).toFixed(2)}`);

export function Btn(p: { label: string; onPress: () => void; kind?: 'primary' | 'alt' | 'danger'; disabled?: boolean; busy?: boolean }) {
  const style = p.kind === 'alt' ? s.btnAlt : p.kind === 'danger' ? s.btnDanger : s.btn;
  const off = p.disabled || p.busy;
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={p.label} disabled={off} onPress={p.onPress} style={[style, off && s.disabled]}>
      {p.busy ? <ActivityIndicator color={p.kind === 'alt' ? '#1769AA' : '#fff'} /> :
        <Text style={p.kind === 'alt' ? s.btnAltText : s.btnText}>{p.label}</Text>}
    </Pressable>
  );
}

export const ErrorText = ({ msg }: { msg: string | null }) => (msg ? <Text accessibilityRole="alert" style={s.error}>{msg}</Text> : null);

export const EmergencyNotice = () => (
  <View style={s.notice}><Text style={s.noticeText}>
    Neravu is not an ambulance service. In a medical emergency call 108 or 112 immediately.
  </Text></View>
);
