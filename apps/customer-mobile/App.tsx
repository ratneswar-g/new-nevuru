import React from 'react';
import { StyleSheet, Text, View, SafeAreaView } from 'react-native';
import type { BookingStatus, MobilityRequirement } from '@neravu/shared-types';

export default function App() {
  const currentStatus: BookingStatus = 'REQUESTED';
  const mobilityChoice: MobilityRequirement = 'FOLDING_WHEELCHAIR';

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Neravu</Text>
        <Text style={styles.headerSubtitle}>Patient & Family Companion</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Assisted Medical Journey</Text>
        <Text style={styles.statusBadge}>Status: {currentStatus}</Text>
        <Text style={styles.detailText}>Selected Mobility: {mobilityChoice}</Text>
        <Text style={styles.infoText}>
          Door-to-door assisted transit with verified non-clinical hospital accompaniment.
        </Text>
      </View>

      <View style={styles.noticeBox}>
        <Text style={styles.noticeText}>
          Non-emergency service. In clinical emergency, dial 108 or 112 immediately.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#EAF5FF',
    padding: 16,
  },
  header: {
    backgroundColor: '#1769AA',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  headerTitle: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '700',
  },
  headerSubtitle: {
    color: '#62B6E8',
    fontSize: 14,
    marginTop: 4,
  },
  card: {
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#62B6E8',
    marginBottom: 16,
  },
  cardTitle: {
    color: '#172B4D',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  statusBadge: {
    color: '#1769AA',
    fontWeight: '600',
    marginBottom: 4,
  },
  detailText: {
    color: '#172B4D',
    fontSize: 14,
    marginBottom: 8,
  },
  infoText: {
    color: '#42526E',
    fontSize: 13,
    lineHeight: 18,
  },
  noticeBox: {
    backgroundColor: '#FFF0B3',
    padding: 12,
    borderRadius: 6,
    borderLeftWidth: 4,
    borderLeftColor: '#FFAB00',
  },
  noticeText: {
    color: '#172B4D',
    fontSize: 12,
  },
});
