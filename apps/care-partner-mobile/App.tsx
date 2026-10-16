import React from 'react';
import { StyleSheet, Text, View, SafeAreaView } from 'react-native';
import type { CarePartnerStatus, BookingStatus } from '@neravu/shared-types';

export default function App() {
  const kycStatus: CarePartnerStatus = 'PENDING_VERIFICATION';
  const activeStatus: BookingStatus = 'ARRIVED';

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Neravu Care Partner</Text>
        <Text style={styles.headerSubtitle}>Field Driver & Companion Service</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>KYC Verification Status</Text>
        <Text style={styles.statusBadge}>{kycStatus}</Text>
        <Text style={styles.infoText}>
          Document inspection and vehicle equipment verification are required by admin before taking assignments.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Active Journey Workflow</Text>
        <Text style={styles.statusBadge}>Stage: {activeStatus}</Text>
        <Text style={styles.infoText}>
          Pickup OTP verification required from customer at doorstep before proceeding to hospital.
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
    backgroundColor: '#172B4D',
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
    fontWeight: '700',
    marginBottom: 8,
  },
  infoText: {
    color: '#42526E',
    fontSize: 13,
    lineHeight: 18,
  },
});
