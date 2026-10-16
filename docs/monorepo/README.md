# Neravu Monorepo Workspace Guide

This monorepo houses all core software assets for the Neravu assisted medical mobility and companion platform.

## Directory Layout

```
neravu/
├── apps/
│   ├── website/             # Public Marketing & Information Web Portal (React + Vite)
│   ├── admin-dashboard/     # Operations, Verification & Dispatch Console (React + Vite)
│   ├── customer-mobile/     # Patient & Family Helper Mobile App (React Native + Expo)
│   └── care-partner-mobile/ # Care Partner Field Mobile App (React Native + Expo)
├── backend/                 # Authoritative Python / Django REST Framework service
│   ├── config/              # Split settings (base, local, test, production), URLs, WSGI/ASGI
│   ├── apps/                # Modular domain apps (core, users, companions, pricing, bookings, etc.)
│   └── requirements/        # Dependency specifications (base, dev, prod)
├── packages/
│   └── shared-types/        # Canonical TypeScript types, enums, and API envelopes
├── environments/            # Sanitized environment configuration templates
└── docs/                    # Architecture blueprints and system guides
```

## Technology Invariants
- **Sole Authoritative DB**: PostgreSQL (No Firestore, no Express live mock).
- **Sole Authoritative Backend**: Django REST Framework.
- **Client Web**: React, TypeScript, Vite.
- **Client Mobile**: React Native, Expo, TypeScript.
- **Design Palette**: `#1769AA` (Primary), `#62B6E8` (Secondary), `#EAF5FF` (Background), `#172B4D` (Navy).
- **Currency & Timezone**: INR (₹) / Asia/Kolkata (IST).
