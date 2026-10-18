# Neravu — AI Handoff

**Repository:** `ratneswar-g/new-nevuru` · **Branch:** `dev/mvp-implementation` (never commit to `main`)
**Last updated:** 2026-10-18 · See `git log` for the exact latest commit.

## 1. Status at a glance

| Area | State | Verified how |
|---|---|---|
| Backend API (DRF) | Implemented | `pytest`: **68 passed** (local Postgres, isolated test DB) |
| Shared types + API client | Implemented | `tsc --noEmit` OK; client key-casing tests 3/3 |
| Admin dashboard | Implemented | `tsc` OK, `vite build` OK. **Not run against a live Firebase/backend** |
| Public website | Implemented (live public pricing) | `tsc` OK, `vite build` OK. **Not run against a live backend** |
| Customer mobile app | Implemented | `tsc --noEmit` OK only. **Never bundled or run on a device/emulator** |
| Care Partner mobile app | Implemented | `tsc --noEmit` OK only. **Never bundled or run on a device/emulator** |

"Implemented" means the code exists and compiles/tests as stated above. **No end-to-end test with real Firebase
phone auth has been performed**, and the mobile apps have never been executed.

## 2. Architecture (unchanged, approved)
React+Vite website and admin · Expo/React Native customer and Care Partner apps · Django REST Framework ·
PostgreSQL · `packages/shared-types` (types only) · `packages/api-client` (fetch client, snake↔camel).
Auth = Firebase phone auth on clients; backend verifies ID token (`check_revoked=True`) and resolves users
**only by `firebase_uid`**. Roles are never taken from client input or token claims.

## 3. Backend (what exists)
API root `/api/v1/`. Error shape everywhere: `{"error": {"code","message","details"}}`.

- **Identity** `auth/register/` (phone + UID from verified token only; `ADMIN` rejected), `me/`, `me/customer-profile/`, `me/family-helpers/`.
- **Pricing** `public/pricing/`, `admin/rate-cards/` (+`/activate/`). Fare = base + max(0, distance − included)·per_km + mobility surcharge + wait_minutes·per_min; round trip doubles distance. **No default amounts exist anywhere**: with no active rate card, quoting/booking returns 503 `RATE_CARD_UNAVAILABLE`. Bookings keep the rate card they were quoted on.
- **Bookings (customer)** `bookings/quote|/`, `bookings/<id>/{confirm,cancel,otp/<pickup|dropoff>,emergency,incidents}`. Family helpers act via `can_book` / `can_view_live_status` / `can_view_history`.
- **Journey (Care Partner)** `partner/bookings/<id>/{arrive,verify-pickup,arrive-hospital,start-return,complete,emergency,incidents}`; `partner/{me,kyc,vehicles,duty}`.
- **Admin** bookings list/assign/unassign/cancel/close, partners approve/reject/suspend, `vehicles/<id>/verify`, incidents list/resolve, `dashboard`, `audit-logs`.
- **State machine** `apps/bookings/state_machine.py`; the only status mutator is `services.transition()` under a row lock. `INCIDENT_FLAGGED` freezes the journey; only admin resolution may resume (to the exact held state) or cancel.
- **OTP** 4 digits, stored as HMAC-SHA256 (keyed with `SECRET_KEY`), TTL `OTP_TTL_MINUTES` (30), `OTP_MAX_ATTEMPTS` (3). Plaintext is returned once, only to the customer side, `Cache-Control: no-store`. Partner serializers contain no OTP fields (tested). Failed-attempt decrements are committed before the error is raised. Audit never records codes.
- **Audit** append-only (`save`/`delete`/queryset `update`/`delete` raise). API does not expose IP.
- **Assignment** requires APPROVED partner, active user, a verified+active vehicle supporting the booking's mobility need, and no other active journey.
- **Ops command** `python manage.py provision_admin --phone +91… --firebase-uid <UID>` (the only way to create an admin).

## 4. Commands that were actually run (this environment)
```bash
# one-time local DB (isolated test DB the test settings require)
pg_ctlcluster 16 main start
su postgres -c "psql -c \"CREATE ROLE test_user LOGIN PASSWORD 'test_password' CREATEDB;\" -c \"CREATE DATABASE neravu_test_isolated OWNER test_user;\""
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements/dev.txt
cd backend && DJANGO_SETTINGS_MODULE=config.settings.test ../.venv/bin/python -m pytest tests -q    # 68 passed
python manage.py makemigrations --check --dry-run --settings=config.settings.test                  # No changes detected
bun install                                                                                        # workspace deps
cd packages/api-client && node --experimental-strip-types --test src/case.test.ts                  # 3 pass
for d in packages/shared-types packages/api-client apps/admin-dashboard apps/website apps/customer-mobile apps/care-partner-mobile; do (cd $d && ../../node_modules/.bin/tsc --noEmit); done   # all exit 0
(cd apps/admin-dashboard && bun run build); (cd apps/website && bun run build)                     # both OK
```
Test DB safety: `config/settings/test.py` asserts the DB name is `neravu_test_isolated` and refuses prod/dev names.
Tests never touch Firebase (token verification is mocked) or any remote database. Nothing was run against Neon/production.

## 5. How to run locally
```bash
# backend (dev DB must be a LOCAL/dev database, never production)
cp environments/.env.example.backend backend/.env   # fill values; do not commit
cd backend && python manage.py migrate --settings=config.settings.local
python manage.py provision_admin --phone +91XXXXXXXXXX --firebase-uid <UID from Firebase console>
python manage.py runserver 0.0.0.0:8000 --settings=config.settings.local
# web
cp environments/.env.example.admin apps/admin-dashboard/.env.local   # add VITE_FIREBASE_*
bun run --cwd apps/admin-dashboard dev     # :5174
bun run --cwd apps/website dev             # :5173
# mobile: needs a DEV BUILD (react-native-firebase is not available in Expo Go)
#   place google-services.json / GoogleService-Info.plist in each app dir (git-ignored), then `npx expo prebuild && npx expo run:android`
```
Set `FIREBASE_CREDENTIALS_PATH` (service-account JSON kept outside the repo) for the backend.

## 6. Known gaps / blockers (honest list)
1. **No Firebase project configured** → real sign-in end-to-end is untested. Needs: Firebase project with Phone auth, web config values, `google-services.json`/plist, service account for backend.
2. **Mobile apps never executed.** Metro monorepo config (`metro.config.js`) and `@react-native-firebase` Expo plugins are unverified; Expo 52 + RN Firebase 21 needs `expo prebuild`/dev client. Possible React 18 (mobile) vs 19 (web) hoisting conflicts under bun workspaces.
3. **Rate card amounts not provided** — intentionally none seeded. An admin must create and activate one before anyone can book.
4. **Distance is straight-line (haversine)**, labelled `STRAIGHT_LINE_ESTIMATE`. Needs a routing provider (Maps API key) for road distance, plus address search/geocoding in the apps (currently manual lat/lng entry).
5. **OTP is delivered in-app only** (customer generates it). No SMS gateway integration; `SMS_BACKEND` in test settings references `apps.core.sms.MockTestSMSBackend` which does not exist (unused today).
6. **KYC document file upload not implemented** (only document identifiers). Storage/encryption design needed.
7. **No push notifications / realtime** — mobile apps poll every 15 s. No live Care Partner location tracking (model has no location fields).
8. **No admin UI for creating a booking on a customer's behalf, helper management UI in the customer app, booking history filters, or incident-photo/attachment support.**
9. Legacy AI-Studio artefacts remain: root `src/`, root `vite.config.ts`, root deps (`express`, `@google/genai`, `firebase-admin`). Root `src/App.tsx` is an architecture explainer, not product code. Candidate for cleanup.
10. No CI, no linting config for TS, no frontend unit/e2e tests beyond the client casing tests, no concurrency/load tests of the row-locking paths, no production deploy config verified. Django admin site exists but ModelAdmin registrations were not written.
11. Payment/settlement is out of scope so far: `final_fare` is computed on completion; nothing collects money.
12. TypeScript versions differ (root `typescript@7`, apps declare `^5`); builds passed with the installed 7.0.2.

## 7. Suggested next steps (in order)
1. Create Firebase project; configure all env templates; run the admin dashboard against a local backend with a real phone login; fix whatever breaks.
2. Admin creates the first rate card (business owner supplies amounts) → smoke-test the full journey from both apps with two test phone numbers.
3. Get the mobile apps building (`expo prebuild`, dev client); fix Metro/hoisting issues.
4. Add routing/geocoding provider and replace manual lat/lng entry.
5. SMS gateway + push notifications; KYC document upload; helper-management UI.
6. Add CI (backend pytest + `tsc` + builds), register Django admin models, clean up legacy root files.

## 8. Key files
Backend: `backend/apps/bookings/{services,state_machine,views,admin_views}.py`, `apps/pricing/services.py`, `apps/companions/views.py`, `apps/incidents/`, `apps/audit/`, `apps/core/{permissions,exceptions}.py`, `backend/tests/test_api_flow.py`.
Frontend: `packages/api-client/src/index.ts`, `packages/shared-types/src/contracts.ts`, `apps/admin-dashboard/src/**`, `apps/website/src/App.tsx`, `apps/{customer,care-partner}-mobile/{App.tsx,src/*}`.
