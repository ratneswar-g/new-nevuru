import assert from 'node:assert/strict';
import { test } from 'node:test';
import { camelizeKeys, snakeizeKeys } from './case.ts';

test('camelizes snake keys but not UPPERCASE enum keys', () => {
  const out = camelizeKeys<any>({
    base_fare: '1', mobility_tier_surcharges: { WALKER_ASSISTANCE: '50' },
    results: [{ care_partner_id: 'x' }], bookings_by_status: { IN_TRANSIT_HOSPITAL: 2 },
  });
  assert.deepEqual(out, {
    baseFare: '1', mobilityTierSurcharges: { WALKER_ASSISTANCE: '50' },
    results: [{ carePartnerId: 'x' }], bookingsByStatus: { IN_TRANSIT_HOSPITAL: 2 },
  });
});

test('snakeizes camel keys and preserves enum keys / values', () => {
  const out: any = snakeizeKeys({
    pickupAddress: 'a', isRoundTrip: true, mobilityTierSurcharges: { FOLDING_WHEELCHAIR: '150' },
  });
  assert.deepEqual(out, {
    pickup_address: 'a', is_round_trip: true, mobility_tier_surcharges: { FOLDING_WHEELCHAIR: '150' },
  });
});

test('leaves primitives, null and single words alone', () => {
  assert.equal(camelizeKeys<any>(null), null);
  assert.deepEqual(camelizeKeys<any>({ role: 'ADMIN', id: 1 }), { role: 'ADMIN', id: 1 });
});
