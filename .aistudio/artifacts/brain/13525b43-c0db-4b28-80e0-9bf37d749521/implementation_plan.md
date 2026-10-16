# Neravu — Phase 0 Architecture & Engineering Blueprint

Neravu is a specialized medical transportation and non-clinical patient companion platform operating in India (Currency: INR, Timezone: Asia/Kolkata). It bridges patient accessibility by providing dependable door-to-hospital transport paired with non-clinical human accompaniment (hospital navigation, registration queue assistance, waiting, and return transit).

> [!IMPORTANT]
> **Clinical Boundary Disclaimer**: Neravu is explicitly **not** an ambulance, paramedic, nursing, or emergency clinical treatment service. It operates as an assisted mobility and supportive companion service. Emergency workflows route immediately to local emergency numbers (108/112).

---

## User Review & Critical Decisions

> [!IMPORTANT]
> **Authentication Decision Gate (Must be settled before Phase 3)**:
> We must decide between **Native Django REST Auth (Django Custom User + SimpleJWT / Knox tokens)** vs. **Firebase Authentication (FCM + Auth with DRF token verification middleware)**.
> 
> - **Option A (Recommended): Native Django REST Auth with Phone OTP (via SMS Gateway)**
>   - *Pros*: Completely unified user authority in PostgreSQL; zero external auth vendor lock-in; single source of truth for user models, roles, and session invalidation; adheres strictly to "no Firestore / no dual authority" principle.
>   - *Cons*: Requires direct integration with an Indian SMS gateway (e.g., MSG91/Twilio) for phone OTP.
> - **Option B: Firebase Authentication (Phone Auth) + DRF Custom Backend Validation**
>   - *Pros*: Streamlined phone OTP verification via Firebase Auth SDK on mobile.
>   - *Cons*: Introduces hybrid auth tokens; Firebase manages auth identities while DRF/Postgres manages roles, requiring bidirectional syncing and webhook/token verification on every API request.
> 
> *Recommended Path*: Option A for unified PostgreSQL-first transactional security, or Option B if Firebase Phone Auth is mandatory for SMS delivery convenience. Approval is required before Phase 3 implementation.

---

## 1. Overview & Core Concept

### Core Journey Flow
```
┌─────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ Customer Book   ├─────►│ Fare Calculation & Conf ├─────►│ Care Partner Match &    │
│ (Mobility/Needs)│      │ (Configurable Rate Card)│      │ Assignment Acceptance   │
└─────────────────┘      └─────────────────────────┘      └────────────┬────────────┘
                                                                       │
┌─────────────────────────┐      ┌─────────────────────────┐           │
│ Hospital Waiting &      │◄─────┤ Transport to Hospital   │◄──────────┘
│ Non-Clinical Companion  │      │ (4-digit Pickup OTP)    │
└────────────┬────────────┘      └─────────────────────────┘
             │
             ▼
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ Optional Return Journey ├─────►│ Drop-off Destination    ├─────►│ Completion, Payment Rec │
│ (Same Partner Priority) │      │ (4-digit Drop-off OTP)  │      │ & Audit Log Archive     │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

### Visual & Design Identity
- **Primary Brand Color**: `#1769AA` (Trust Medical Blue)
- **Secondary Accent**: `#62B6E8` (Sky Blue)
- **Background Atmosphere**: `#EAF5FF` (Soft Tint Blue / Clean Canvas)
- **Deep Slate / Navy**: `#172B4D` (High-contrast accessible text)
- **Typography**: Clean humanist sans-serif (Inter / Plus Jakarta Sans) optimized for legibility across elder patients and field partners.

---

## 2. Platform Architecture & Monorepo Structure

Neravu is organized as a unified monorepo to ensure strong type coherence and clear separation of concerns across the four client applications and the backend engine.

```
neravu/
├── backend/                  # Python 3.12+ & Django REST Framework (DRF)
│   ├── manage.py
│   ├── config/               # Settings (base, dev, test, prod), WSGI/ASGI, URLs
│   ├── apps/
│   │   ├── users/            # Custom User model, RBAC (Customer, Partner, Admin)
│   │   ├── companions/       # Care Partner profiles, vehicles, verification docs
│   │   ├── bookings/         # Booking lifecycle, OTP generation & state machine
│   │   ├── pricing/          # Configurable rate cards, fare engine (INR)
│   │   ├── incidents/        # Incident logs, escalation triggers, SOS records
│   │   └── audit/            # Tamper-evident operational audit logs
│   ├── tests/                # Unit and integration test suite
│   └── requirements/         # Base, dev, prod dependencies
│
├── apps/
│   ├── website/              # Public Marketing & Onboarding Web App (React + Vite + TS)
│   │   └── src/              # Services, how it works, pricing transparency, safety info
│   ├── admin-dashboard/      # Admin Web Portal (React + Vite + TS)
│   │   └── src/              # Partner approvals, dispatch oversight, rate card manager
│   ├── customer-mobile/      # Customer Mobile App (React Native + Expo + TS)
│   │   └── src/              # Booking, mobility options, OTP viewing, live status
│   └── care-partner-mobile/  # Care Partner Mobile App (React Native + Expo + TS)
│       └── src/              # Duty toggle, assignments, OTP entry, hospital wait timer
│
├── packages/
│   └── shared-types/         # Shared TypeScript interfaces, enums, & API contracts
│       ├── booking.ts        # BookingStatus, VehicleType, MobilityNeeds
│       ├── pricing.ts        # FareEstimate, RateCardConfig
│       └── user.ts           # UserRole, Profile
│
└── docs/                     # Architecture, state machines, API specs, deployment guides
```

---

## 3. Application and Backend Responsibilities

| Subsystem | Responsibilities | Disallowed Behaviors |
| :--- | :--- | :--- |
| **Backend (Django REST Framework)** | **Single Source of Truth**: All state transitions, fare math, cryptographic OTP generation, assignment rules, RBAC enforcement, audit logging. | Never delegate fare calculation, OTP validation, or state changes to client apps. |
| **Authoritative DB (PostgreSQL)** | Persistent storage for users, vehicles, rate cards, active bookings, journey logs, and incidents. | Never use Firestore as a secondary primary database. |
| **Public Website** | Brand awareness, transparent pricing explainer, service safety guidelines, customer/partner onboarding flows, SEO. | No booking dispatching or internal operational controls. |
| **Customer Mobile App** | Ride requests with mobility filters (wheelchair assistance, walker, companion-only), fare confirmation, OTP display, live partner tracking, emergency contact broadcast. | No client-side fare computation or direct partner-assignment logic. |
| **Care Partner Mobile App** | Duty toggle (online/offline), assignment review, 4-digit pickup OTP entry, hospital accompaniment log, return leg initiation, drop-off OTP entry, SOS/incident reporting. | Cannot bypass OTP verification or edit booking records. |
| **Admin Web Dashboard** | Care partner KYC/vehicle verification & approval, live dispatch supervision, configurable rate card manager, incident investigation, audit log export. | Cannot operate without strict role permissions; no unlogged sensitive updates. |

---

## 4. Database & Environment Strategy

### Authoritative Database (PostgreSQL)
- **Engine**: PostgreSQL 16+.
- **Data Integrity**: Foreign key constraints, unique constraints on active states, transactional consistency for booking transitions (`select_for_update`).
- **Auditability**: Timestamped audit trails (`created_at`, `updated_at`, `actor_id`, `state_change`).

### Environment Isolation Strategy
- **Development (`dev`)**: Isolated local/containerized PostgreSQL database; mock SMS gateway provider; debug logs enabled.
- **Testing (`test`)**: Ephemeral in-memory/test PostgreSQL instance for deterministic pytest/Django test runs; zero external API dependencies.
- **Production (`prod`)**: Cloud-managed PostgreSQL (with read-replicas, continuous backups, point-in-time recovery, SSL encryption in transit and AES-256 at rest); strict secrets management (environment variables via Cloud Secret Manager).
- **Rule**: Development and testing environments must never point to production databases or expose real customer PII.

---

## 5. Security Requirements

1. **Zero Secret Exposure**: No API keys, database credentials, or secret keys in frontend code, git repositories, or client bundles.
2. **Authoritative State Transitions**: The booking state machine is strictly enforced server-side:
   $$\text{REQUESTED} \rightarrow \text{QUOTED} \rightarrow \text{ASSIGNED} \rightarrow \text{ARRIVED} \rightarrow \text{IN\_TRANSIT\_TO\_HOSPITAL} \rightarrow \text{ACCOMPANIMENT} \rightarrow \text{RETURN\_TRANSIT} \rightarrow \text{COMPLETED}$$
3. **Cryptographic OTPs**: 4-digit pickup and drop-off OTPs are generated on the server with short validity windows and rate-limited attempt throttling (maximum 3 failed attempts before lockout).
4. **Role-Based Access Control (RBAC)**: Enforced via Django permissions (`IsCustomer`, `IsCarePartner`, `IsAdminOperator`).
5. **Data Protection & Privacy**: Patient mobility needs, medical appointment destinations, and emergency contact details are classified as sensitive personal data; access is restricted to assigned partners during active journeys.

---

## 6. Phased Implementation Roadmap & Acceptance Criteria

### Phase 0: Requirements and Architecture (Current)
- **Goal**: Establish scope, technical agreements, repository blueprint, and decision gates.
- **Acceptance Criteria**: Comprehensive architecture document approved; technical constraints locked (PostgreSQL authoritative, no mock backend, 4 applications defined).

### Phase 1: Repository & Application Scaffolding
- **Goal**: Clean directory structure, standard linting/formatting, shared TypeScript types package, and scaffolded app containers.
- **Acceptance Criteria**: Monorepo structure created; shared TypeScript types build cleanly; base configs for DRF, Vite, and Expo established.

### Phase 2: Database Foundation & Domain Models
- **Goal**: Custom User model, Companion/Vehicle models, Booking models, RateCard models, and migrations in PostgreSQL.
- **Acceptance Criteria**: Migrations execute without error; domain models enforce relational constraints; model-level unit tests pass with 100% core coverage.

### Phase 3: Authentication & Role-Based Permissions
- **Goal**: Implement agreed authentication system, session tokens, and permission classes.
- **Acceptance Criteria**: Registration and login endpoints functional for Customers, Care Partners, and Admins; unauthorized access blocked with HTTP 401/403; test suite verifies role boundaries.

### Phase 4: Core Engine — Pricing, Booking, Assignment & State Machine
- **Goal**: Implement rate card fare engine, booking creation, assignment logic, OTP generation/validation, and state transitions.
- **Acceptance Criteria**: Fares calculated accurately based on configurable rate cards; OTP verification transitions booking states; concurrent assignment races prevented via transactional locking; journey state machine tests pass.

### Phase 5: Client Application Integration
- **Goal**: Connect Public Website, Customer App, Care Partner App, and Admin Dashboard to the live DRF API.
- **Acceptance Criteria**: Customers can quote and book journeys; Care Partners receive assignments and verify OTPs; live status reflects in real time; website communicates brand and onboarding.

### Phase 6: Admin Operations, Safety, Notifications & Audit Logs
- **Goal**: Partner document verification, rate card editing, incident escalation, FCM notifications, and audit logging.
- **Acceptance Criteria**: Admins can approve/reject partner credentials and configure fares; incidents trigger alert records; operational actions generate immutable audit logs.

### Phase 7: Deployment, Security Review & End-to-End Testing
- **Goal**: Production configuration, automated CI testing, end-to-end journey tests, and security hardening.
- **Acceptance Criteria**: E2E test passes complete customer journey (booking $\rightarrow$ OTP $\rightarrow$ hospital companion $\rightarrow$ return $\rightarrow$ completion); zero critical security vulnerabilities.
