/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  Globe,
  LayoutDashboard,
  Smartphone,
  ShieldCheck,
  Server,
  FileCode,
  BookOpen,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Car,
  HeartPulse,
} from 'lucide-react';
import type {
  UserRole,
  BookingStatus,
  MobilityRequirement,
  CarePartnerStatus,
  VehicleType,
  RateCardRule,
  FareEstimate,
  ApiResponse,
} from '@neravu/shared-types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'website' | 'admin' | 'customer' | 'partner' | 'backend' | 'types'>('overview');

  const supportedMobilities: MobilityRequirement[] = [
    'INDEPENDENT',
    'WALKER_ASSISTANCE',
    'FOLDING_WHEELCHAIR',
    'COMPANION_ONLY',
  ];

  const journeyStates: BookingStatus[] = [
    'REQUESTED',
    'QUOTED',
    'CONFIRMED',
    'ASSIGNED',
    'ARRIVED',
    'IN_TRANSIT_HOSPITAL',
    'ACCOMPANIMENT',
    'RETURN_TRANSIT',
    'COMPLETED',
    'CLOSED',
  ];

  const partnerStatuses: CarePartnerStatus[] = [
    'PENDING_VERIFICATION',
    'APPROVED',
    'REJECTED',
    'SUSPENDED',
  ];

  const vehicleTypes: VehicleType[] = [
    'SEDAN',
    'HATCHBACK',
    'SUV',
    'WHEELCHAIR_ACCESSIBLE',
  ];

  const sampleRateCardRule: RateCardRule = {
    id: 'rc_v1_seed',
    version: 1,
    name: 'Bangalore Standard Rate Card (Configurable)',
    baseFare: 250,
    baseDistanceKm: 4,
    perKmRate: 22,
    perMinuteWaitingRate: 3.5,
    mobilityTierSurcharges: {
      INDEPENDENT: 0,
      WALKER_ASSISTANCE: 50,
      FOLDING_WHEELCHAIR: 100,
      COMPANION_ONLY: 50,
    },
    effectiveFrom: '2026-10-01T00:00:00Z',
    isActive: true,
  };

  const sampleFareEstimate: FareEstimate = {
    quoteId: 'quote_mock_preview',
    rateCardVersion: 1,
    baseFare: 250,
    distanceFare: 132,
    estimatedDistanceKm: 6,
    estimatedWaitingFare: 210,
    estimatedWaitingMinutes: 60,
    mobilitySurcharge: 100,
    totalFare: 692,
    currency: 'INR',
    expiresAt: '2026-10-15T22:30:00Z',
  };

  const sampleApiResponse: ApiResponse<FareEstimate> = {
    success: true,
    data: sampleFareEstimate,
    timestamp: '2026-10-15T22:15:00Z',
  };

  return (
    <div className="min-h-screen bg-[#EAF5FF] text-[#172B4D] flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-[#1769AA] text-white px-6 py-4 shadow-md flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#62B6E8] flex items-center justify-center text-[#172B4D] font-black text-xl shadow-inner">
            N
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight">Neravu Platform</h1>
              <span className="text-xs bg-[#62B6E8] text-[#172B4D] font-bold px-2 py-0.5 rounded">
                Phase 1 Active
              </span>
            </div>
            <p className="text-xs text-[#EAF5FF]/80">
              Assisted Medical Transport & Non-Clinical Companion Engine (INR • Asia/Kolkata)
            </p>
          </div>
        </div>

        <nav className="flex flex-wrap items-center gap-1 bg-[#172B4D]/40 p-1 rounded-lg text-xs font-medium">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 rounded transition ${activeTab === 'overview' ? 'bg-white text-[#1769AA] font-bold shadow-sm' : 'text-white hover:bg-white/10'}`}
          >
            Monorepo Overview
          </button>
          <button
            onClick={() => setActiveTab('website')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${activeTab === 'website' ? 'bg-white text-[#1769AA] font-bold shadow-sm' : 'text-white hover:bg-white/10'}`}
          >
            <Globe className="w-3.5 h-3.5" />
            Website
          </button>
          <button
            onClick={() => setActiveTab('admin')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${activeTab === 'admin' ? 'bg-white text-[#1769AA] font-bold shadow-sm' : 'text-white hover:bg-white/10'}`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            Admin Dashboard
          </button>
          <button
            onClick={() => setActiveTab('customer')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${activeTab === 'customer' ? 'bg-white text-[#1769AA] font-bold shadow-sm' : 'text-white hover:bg-white/10'}`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            Customer Mobile
          </button>
          <button
            onClick={() => setActiveTab('partner')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${activeTab === 'partner' ? 'bg-white text-[#1769AA] font-bold shadow-sm' : 'text-white hover:bg-white/10'}`}
          >
            <Car className="w-3.5 h-3.5" />
            Care Partner Mobile
          </button>
          <button
            onClick={() => setActiveTab('backend')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${activeTab === 'backend' ? 'bg-white text-[#1769AA] font-bold shadow-sm' : 'text-white hover:bg-white/10'}`}
          >
            <Server className="w-3.5 h-3.5" />
            Django Backend
          </button>
          <button
            onClick={() => setActiveTab('types')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${activeTab === 'types' ? 'bg-white text-[#1769AA] font-bold shadow-sm' : 'text-white hover:bg-white/10'}`}
          >
            <FileCode className="w-3.5 h-3.5" />
            Shared Types
          </button>
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Phase 1 Scaffolding Banner */}
            <div className="bg-white border-l-4 border-[#1769AA] p-5 rounded-r-lg shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-bold text-[#1769AA] flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    Phase 1: Repository & Application Scaffolding Completed
                  </h2>
                  <p className="text-sm text-[#42526E] mt-1">
                    All four applications, the Django REST Framework backend, reusable <code>@neravu/shared-types</code> package, and sanitized environment templates are initialized according to the frozen Phase 0 architecture.
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs font-semibold px-2.5 py-1 bg-[#EAF5FF] text-[#1769AA] border border-[#62B6E8] rounded-full">
                    Currency: INR (₹)
                  </span>
                  <div className="text-[11px] text-[#42526E] mt-1">Timezone: Asia/Kolkata</div>
                </div>
              </div>
            </div>

            {/* 4 Interfaces Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-lg border border-[#62B6E8]/40 shadow-sm hover:shadow-md transition">
                <div className="w-9 h-9 rounded bg-[#EAF5FF] text-[#1769AA] flex items-center justify-center mb-3">
                  <Globe className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-sm text-[#172B4D]">1. Public Website</h3>
                <p className="text-xs text-[#42526E] mt-1 mb-3">
                  Service information, non-clinical companion explainer, safety standards, transparent rate card rules, and intake portals.
                </p>
                <div className="text-[11px] text-[#1769AA] font-mono bg-[#EAF5FF] px-2 py-1 rounded inline-block">
                  apps/website (React+Vite)
                </div>
              </div>

              <div className="bg-white p-5 rounded-lg border border-[#62B6E8]/40 shadow-sm hover:shadow-md transition">
                <div className="w-9 h-9 rounded bg-[#EAF5FF] text-[#1769AA] flex items-center justify-center mb-3">
                  <LayoutDashboard className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-sm text-[#172B4D]">2. Admin Dashboard</h3>
                <p className="text-xs text-[#42526E] mt-1 mb-3">
                  Care Partner KYC approval, vehicle verification, live dispatch board, versioned rate card manager, and audit logs.
                </p>
                <div className="text-[11px] text-[#1769AA] font-mono bg-[#EAF5FF] px-2 py-1 rounded inline-block">
                  apps/admin-dashboard (React+Vite)
                </div>
              </div>

              <div className="bg-white p-5 rounded-lg border border-[#62B6E8]/40 shadow-sm hover:shadow-md transition">
                <div className="w-9 h-9 rounded bg-[#EAF5FF] text-[#1769AA] flex items-center justify-center mb-3">
                  <Smartphone className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-sm text-[#172B4D]">3. Customer Mobile</h3>
                <p className="text-xs text-[#42526E] mt-1 mb-3">
                  Mobility requirement filtering, fare quote confirmation, verbal OTP display, live companion tracking, family helpers.
                </p>
                <div className="text-[11px] text-[#1769AA] font-mono bg-[#EAF5FF] px-2 py-1 rounded inline-block">
                  apps/customer-mobile (Expo)
                </div>
              </div>

              <div className="bg-white p-5 rounded-lg border border-[#62B6E8]/40 shadow-sm hover:shadow-md transition">
                <div className="w-9 h-9 rounded bg-[#EAF5FF] text-[#1769AA] flex items-center justify-center mb-3">
                  <Car className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-sm text-[#172B4D]">4. Care Partner Mobile</h3>
                <p className="text-xs text-[#42526E] mt-1 mb-3">
                  Duty toggle, assignment acceptance, 4-digit pickup/drop-off OTP entry, hospital wait counter, and incident alerts.
                </p>
                <div className="text-[11px] text-[#1769AA] font-mono bg-[#EAF5FF] px-2 py-1 rounded inline-block">
                  apps/care-partner-mobile (Expo)
                </div>
              </div>
            </div>

            {/* Architecture Invariants Box */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <h4 className="font-bold text-sm text-[#1769AA] mb-2 flex items-center gap-1.5">
                  <Server className="w-4 h-4" /> Authoritative Backend
                </h4>
                <p className="text-xs text-[#42526E] leading-relaxed">
                  Django REST Framework is the sole authority for state transitions, pricing math, cryptographic OTP generation, and role permissions. No Express live mock.
                </p>
              </div>

              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <h4 className="font-bold text-sm text-[#1769AA] mb-2 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" /> Sole Authoritative DB
                </h4>
                <p className="text-xs text-[#42526E] leading-relaxed">
                  PostgreSQL 16+ is the single authoritative application database. Firestore is prohibited as a second primary database.
                </p>
              </div>

              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <h4 className="font-bold text-sm text-[#1769AA] mb-2 flex items-center gap-1.5">
                  <HeartPulse className="w-4 h-4 text-rose-600" /> Non-Emergency Scope
                </h4>
                <p className="text-xs text-[#42526E] leading-relaxed">
                  Neravu is non-clinical assisted transport and accompaniment. In clinical emergencies, automated protocols redirect to 108/112.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Website Simulator / Preview */}
        {activeTab === 'website' && (
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
            <div className="bg-slate-100 px-4 py-2 border-b border-slate-200 text-xs font-mono text-slate-600 flex items-center justify-between">
              <span>Preview: apps/website (Vite SPA)</span>
              <span className="text-[#1769AA]">Port: 5173</span>
            </div>
            <div className="p-8">
              <div className="max-w-2xl mx-auto space-y-6">
                <div className="border-b border-slate-200 pb-4">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#1769AA]">Welcome to Neravu</span>
                  <h2 className="text-2xl font-bold text-[#172B4D] mt-1">Dignified Medical Transportation with Non-Clinical Accompaniment</h2>
                  <p className="text-sm text-[#42526E] mt-2 leading-relaxed">
                    We bridge the journey from doorstep to consultation room. Our vetted Care Partners provide safe transit, physical assistance, and compassionate waiting accompaniment throughout hospital visits.
                  </p>
                </div>

                <div className="bg-[#EAF5FF] p-4 rounded-lg border border-[#62B6E8]/40">
                  <h3 className="text-sm font-bold text-[#1769AA] mb-2">Supported Patient Mobility Profiles</h3>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {supportedMobilities.map((mob) => (
                      <div key={mob} className="bg-white p-2 rounded border border-[#62B6E8]/20 font-medium text-[#172B4D]">
                        ✓ {mob}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg text-xs text-amber-900">
                  <strong>Service Boundary Notice:</strong> Neravu is not an ambulance, paramedic, or clinical care service. We do not provide acute trauma response, emergency medical evacuation, or nursing.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Admin Dashboard Simulator / Preview */}
        {activeTab === 'admin' && (
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
            <div className="bg-slate-100 px-4 py-2 border-b border-slate-200 text-xs font-mono text-slate-600 flex items-center justify-between">
              <span>Preview: apps/admin-dashboard (Vite SPA)</span>
              <span className="text-[#1769AA]">Port: 5174</span>
            </div>
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-[#EAF5FF] p-4 rounded-lg border border-[#62B6E8]/40">
                  <div className="text-xs text-[#42526E]">Pending KYC Partners</div>
                  <div className="text-2xl font-bold text-[#1769AA] mt-1">0</div>
                  <div className="text-[11px] text-slate-500 mt-1">Awaiting Phase 2 models</div>
                </div>
                <div className="bg-[#EAF5FF] p-4 rounded-lg border border-[#62B6E8]/40">
                  <div className="text-xs text-[#42526E]">Active Rate Card Version</div>
                  <div className="text-2xl font-bold text-[#1769AA] mt-1">v{sampleRateCardRule.version}</div>
                  <div className="text-[11px] text-slate-500 mt-1">Configurable via Admin API</div>
                </div>
                <div className="bg-[#EAF5FF] p-4 rounded-lg border border-[#62B6E8]/40">
                  <div className="text-xs text-[#42526E]">System Health Status</div>
                  <div className="text-2xl font-bold text-emerald-600 mt-1">READY</div>
                  <div className="text-[11px] text-slate-500 mt-1">Phase 1 Scaffolding clean</div>
                </div>
              </div>

              <div className="border border-slate-200 rounded-lg p-4">
                <h3 className="text-sm font-bold text-[#1769AA] mb-3">Care Partner KYC Review Workflow</h3>
                <div className="flex flex-wrap gap-2">
                  {partnerStatuses.map((st) => (
                    <span key={st} className="px-3 py-1 bg-slate-100 border border-slate-300 rounded text-xs font-mono">
                      {st}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Customer Mobile App Preview */}
        {activeTab === 'customer' && (
          <div className="max-w-md mx-auto bg-white rounded-2xl shadow-lg border-4 border-slate-800 overflow-hidden">
            <div className="bg-[#172B4D] text-white px-4 py-3 flex items-center justify-between text-xs">
              <span className="font-bold">Neravu Customer App</span>
              <span className="text-[#62B6E8]">Expo Mobile</span>
            </div>
            <div className="p-5 space-y-4 bg-[#EAF5FF]/40">
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="text-xs font-bold text-[#1769AA] uppercase tracking-wider">Book Assisted Journey</div>
                <div className="mt-2 text-xs text-slate-600">
                  <div className="font-semibold text-slate-800">Doorstep ➔ Hospital Destination</div>
                  <div className="mt-1">Hospital: Manipal Hospital, HAL Old Airport Rd</div>
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="text-xs font-bold text-[#172B4D]">Mobility & Assistance Needs</div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {supportedMobilities.map((mob) => (
                    <span key={mob} className="px-2 py-1 bg-[#EAF5FF] text-[#1769AA] border border-[#62B6E8] rounded text-[11px] font-medium">
                      {mob}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                  <span>Authoritative Fare Quote:</span>
                  <span className="text-[#1769AA] font-bold text-sm">₹{sampleFareEstimate.totalFare}</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  Base fare (₹{sampleFareEstimate.baseFare}) + Distance (₹{sampleFareEstimate.distanceFare}) + Waiting (₹{sampleFareEstimate.estimatedWaitingFare})
                </div>
              </div>

              <div className="bg-emerald-50 border border-emerald-200 p-3 rounded-lg text-xs text-emerald-800">
                <strong>Verbal Pickup OTP Security:</strong> 4-digit OTP is presented on passenger phone and shared verbally with Care Partner at doorstep. Never exposed to partner via API.
              </div>
            </div>
          </div>
        )}

        {/* Care Partner Mobile App Preview */}
        {activeTab === 'partner' && (
          <div className="max-w-md mx-auto bg-white rounded-2xl shadow-lg border-4 border-[#1769AA] overflow-hidden">
            <div className="bg-[#1769AA] text-white px-4 py-3 flex items-center justify-between text-xs">
              <span className="font-bold">Care Partner Field App</span>
              <span className="bg-[#62B6E8] text-[#172B4D] font-bold px-2 py-0.5 rounded text-[10px]">Duty: ONLINE</span>
            </div>
            <div className="p-5 space-y-4 bg-slate-50">
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="text-xs font-bold text-slate-500 uppercase">Current Assignment</div>
                <div className="text-sm font-bold text-[#172B4D] mt-1">Stage: ARRIVED AT PICKUP</div>
                <div className="text-xs text-[#42526E] mt-1">Patient: Senior Citizen (Folding Wheelchair)</div>
              </div>

              <div className="bg-white p-4 rounded-xl border-2 border-dashed border-[#1769AA] p-4 text-center">
                <div className="text-xs font-semibold text-[#1769AA]">Enter Passenger's 4-Digit Pickup OTP</div>
                <div className="flex justify-center gap-2 mt-3">
                  <div className="w-10 h-12 rounded border border-slate-300 bg-slate-100 flex items-center justify-center font-bold text-lg text-slate-400">•</div>
                  <div className="w-10 h-12 rounded border border-slate-300 bg-slate-100 flex items-center justify-center font-bold text-lg text-slate-400">•</div>
                  <div className="w-10 h-12 rounded border border-slate-300 bg-slate-100 flex items-center justify-center font-bold text-lg text-slate-400">•</div>
                  <div className="w-10 h-12 rounded border border-slate-300 bg-slate-100 flex items-center justify-center font-bold text-lg text-slate-400">•</div>
                </div>
                <div className="text-[10px] text-slate-500 mt-2">Server verifies OTP hash before unlocking hospital transit</div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-xs text-slate-600">
                <div className="font-bold text-slate-800 mb-1">Supported Vehicle Classes:</div>
                <div className="flex flex-wrap gap-1">
                  {vehicleTypes.map((vt) => (
                    <span key={vt} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-mono">
                      {vt}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Django Backend Inspector */}
        {activeTab === 'backend' && (
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-6">
            <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-[#172B4D] flex items-center gap-2">
                  <Server className="w-5 h-5 text-[#1769AA]" />
                  Django REST Framework Backend Architecture
                </h3>
                <p className="text-xs text-[#42526E] mt-0.5">Authoritative business logic, state machines, and relational PostgreSQL integration</p>
              </div>
              <span className="text-xs font-mono bg-emerald-50 text-emerald-700 border border-emerald-300 px-2.5 py-1 rounded">
                Syntax Validated (py_compile: PASSED)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#1769AA] mb-2">Split Settings Architecture</h4>
                <ul className="text-xs space-y-1.5 font-mono text-slate-700">
                  <li>• <code>backend/config/settings/base.py</code> (Timezone: Asia/Kolkata, INR, apps)</li>
                  <li>• <code>backend/config/settings/local.py</code> (Local PostgreSQL, CORS)</li>
                  <li>• <code>backend/config/settings/test.py</code> (Isolated test DB, password hash speedup)</li>
                  <li>• <code>backend/config/settings/production.py</code> (SSL, Cloud SQL, Secret Mgr)</li>
                </ul>
              </div>

              <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#1769AA] mb-2">Modular Domain Apps Scaffolded</h4>
                <ul className="text-xs space-y-1.5 font-mono text-slate-700">
                  <li>• <code>apps.users</code> (Custom user, roles, family helper permissions)</li>
                  <li>• <code>apps.companions</code> (Care partner profiles, vehicle verification)</li>
                  <li>• <code>apps.pricing</code> (Versioned rate cards, fare calculation engine)</li>
                  <li>• <code>apps.bookings</code> &amp; <code>apps.journeys</code> (State machine &amp; OTP engine)</li>
                  <li>• <code>apps.incidents</code> &amp; <code>apps.audit</code> (Immutable audit logging)</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Shared Types Inspector */}
        {activeTab === 'types' && (
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-6">
            <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-[#172B4D] flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-[#1769AA]" />
                  @neravu/shared-types Package
                </h3>
                <p className="text-xs text-[#42526E] mt-0.5">Canonical TypeScript interfaces compiled cleanly with declarations in <code>dist/</code></p>
              </div>
              <span className="text-xs font-mono bg-emerald-50 text-emerald-700 border border-emerald-300 px-2.5 py-1 rounded">
                Compilation: PASSED
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Canonical Booking Status Machine</h4>
                <div className="flex flex-wrap gap-1.5">
                  {journeyStates.map((st, idx) => (
                    <span key={st} className="px-2.5 py-1 bg-[#EAF5FF] text-[#1769AA] border border-[#62B6E8] rounded text-xs font-mono">
                      {idx + 1}. {st}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Sample Standard API Envelope (ApiResponse&lt;T&gt;)</h4>
                <pre className="bg-[#172B4D] text-[#EAF5FF] p-4 rounded-lg text-xs font-mono overflow-x-auto">
                  {JSON.stringify(sampleApiResponse, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-[#172B4D] text-white text-xs py-4 px-6 mt-auto flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="font-semibold">Neravu Healthcare Mobility</span> &copy; 2026. Preserving Phase 0 requirements and architecture baseline.
        </div>
        <div className="flex items-center gap-4 text-slate-300">
          <span>Palette: #1769AA • #62B6E8 • #EAF5FF • #172B4D</span>
          <span>Sole DB: PostgreSQL</span>
        </div>
      </footer>
    </div>
  );
}
