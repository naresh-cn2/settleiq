# SettleIQ — Product UX Audit

**Document ID:** SETTLEIQ-UX-001  
**Status:** COMPLETE  
**Audit Date:** 2026-11-14  
**Audited Against:** Production deployment `https://settleiq-zeta.vercel.app` (commit `e34716a`)

---

## 1. Every Page and Route

| Route | Page | Purpose | Auth Required | Status |
|-------|------|---------|---------------|--------|
| `/auth` | AuthScreen | Login + Explore Public Demo entry | No | Working |
| `/` (Overview) | OverviewPage | Aggregate metrics across runs | Yes (demo or API key) | Working |
| `/runs` | RunsPage | Run history, create custom run, demo seed | Yes | Working |
| `/import` | ImportPage | CSV/JSON upload, validation preview | Yes | Working |
| `/discrepancies` | DiscrepanciesPage | Discrepancy list with filters | Yes | Working |
| `/discrepancies/:id` | InvestigationPage | Discrepancy detail, trace, hypotheses, resolution | Yes | Working |
| `/metrics` | MetricsPage | Auto-match rate, methodology, per-run metrics | Yes | Working |
| `/history` | HistoryPage | Audit timeline, run comparison | Yes | Working |

**Missing pages:** Public website (Home, Features, Pricing, Docs), Login/Signup, Organization settings, Team management, Billing, Developer portal, Connections.

---

## 2. Every Available Action

### Public Demo Mode
| Action | Endpoint | Works |
|--------|----------|-------|
| Create demo session | `POST /v1/demo/session` | Yes |
| List demo runs | `GET /v1/demo/runs` | Yes |
| Get demo run | `GET /v1/demo/runs/{id}` | Yes |
| List demo discrepancies | `GET /v1/demo/discrepancies` | Yes |
| Get demo discrepancy | `GET /v1/demo/discrepancies/{id}` | Yes |
| Demo discrepancy investigate | `GET /v1/demo/discrepancies/{id}/investigate` | Yes |
| Demo trace | `GET /v1/demo/runs/{id}/trace/{constituent}` | Yes |
| Demo metrics | `GET /v1/demo/runs/{id}/metrics` | Yes |
| Demo history | `GET /v1/demo/runs/{id}/history` | Yes |
| Demo export | `GET /v1/demo/runs/{id}/export?format=json\|csv` | Yes |
| Demo seed | `POST /v1/demo/seed` | Yes |
| Demo journal verify | `POST /v1/demo/journal/verify` | Yes |
| Demo decomposition | `GET /v1/demo/runs/{id}/decomposition` | Yes |
| Exit demo | Clear sessionStorage | Yes |

### API-Key Mode
| Action | Endpoint | Works |
|--------|----------|-------|
| Create run | `POST /v1/runs` | Yes |
| List runs | `GET /v1/runs` | Yes |
| Get run | `GET /v1/runs/{id}` | Yes |
| Run history | `GET /v1/runs/{id}/history` | Yes |
| Run metrics | `GET /v1/runs/{id}/metrics` | Yes |
| Run discrepancies | `GET /v1/runs/{id}/discrepancies` | Yes |
| Run export | `GET /v1/runs/{id}/export?format=json\|csv` | Yes |
| Run decomposition | `GET /v1/runs/{id}/decomposition` | **Returns 404** (not implemented) |
| Import validate | `POST /v1/import/validate` | Yes |
| List discrepancies | `GET /v1/discrepancies` | Yes |
| Get discrepancy | `GET /v1/discrepancies/{id}` | Yes |
| Investigate discrepancy | `GET /v1/discrepancies/{id}/investigate` | Yes |
| Resolve discrepancy | `POST /v1/discrepancies/{id}/resolve` | Yes |
| Trace constituent | `GET /v1/runs/{id}/trace/{constituent}` | Yes |
| Health | `GET /health`, `GET /v1/health` | Yes |

### Missing Actions (Not Implemented)
- User signup / login
- Organization creation
- Team management
- Billing / subscription
- Payment provider connections
- API key management UI
- Developer portal
- Production run decomposition

---

## 3. Every Backend Endpoint Used by Frontend

| Frontend Page | Endpoints Used |
|---------------|----------------|
| AuthScreen | `POST /v1/demo/session`, `GET /v1/runs` (API key test) |
| OverviewPage | `GET /v1/runs`, `GET /v1/discrepancies?run_id={id}` |
| RunsPage | `GET /v1/runs`, `POST /v1/runs`, `POST /v1/demo/seed` |
| ImportPage | `POST /v1/import/validate`, `POST /v1/runs` |
| DiscrepanciesPage | `GET /v1/discrepancies?run_id={id}&type={t}&severity={s}` |
| InvestigationPage | `GET /v1/discrepancies/{id}`, `GET /v1/discrepancies/{id}/investigate`, `GET /v1/runs/{run_id}/trace/{constituent}`, `POST /v1/discrepancies/{id}/resolve` |
| MetricsPage | `GET /v1/runs`, `GET /v1/runs/{id}/metrics` |
| HistoryPage | `GET /v1/runs`, `GET /v1/runs/{id}/history`, `GET /v1/runs/{id}/export` |

---

## 4. Complete Import-to-Reconciliation Workflow

```
1. User clicks "Import" in navigation
2. User uploads CSV or JSON file
3. Frontend parses records, groups by kind
4. Frontend calls POST /v1/import/validate
5. Backend returns accepted_count, quarantined_count, duplicate_count
6. User reviews validation results
7. User clicks "Create Reconciliation Run"
8. Frontend calls POST /v1/runs with validated records
9. Backend validates, reconciles, persists, journals
10. Backend returns run_id, numerator, denominator, rate, discrepancy_count
11. User navigates to discrepancies page filtered by run_id
12. User investigates individual discrepancies
13. User reviews transaction trace and hypotheses
14. User exports results (CSV or JSON)
```

**Gaps:** No file download templates, no data format guide, no step-by-step guidance for first-time users.

---

## 5. Authentication and Authorization Boundaries

| Aspect | Implementation | Status |
|--------|---------------|--------|
| Demo tokens | Stateless HMAC-SHA256, `SETTLEIQ_DEMO_SECRET` | Working |
| API key auth | `X-API-Key` header, constant-time comparison | Working |
| Demo isolation | Demo tokens rejected on `/v1/runs` production routes | Working |
| Fail-closed | Missing `SETTLEIQ_API_KEY` rejects all `/v1/*` | Working |
| User accounts | **Not implemented** | Missing |
| Organizations | **Not implemented** | Missing |
| Sessions | sessionStorage only (demo token, API key) | Working but ephemeral |
| MFA | **Not implemented** | Missing |
| RBAC | **Not implemented** | Missing |

---

## 6. Features: Public Demo vs API-Key Mode

| Feature | Public Demo | API-Key Mode |
|---------|-------------|--------------|
| View demo data | Yes | Yes (own runs) |
| Create custom runs | No | Yes |
| Import data | Yes (validation only) | Yes (full import + run) |
| Export results | Yes (demo) | Yes (own runs) |
| Resolve discrepancies | No (read-only) | Yes |
| Persistent runs | No | Yes (PostgreSQL/SQLite) |
| Decomposition view | Yes | No (404) |

---

## 7. Missing Functionality and Confusing UX

### Critical Gaps
1. **No public website** — Visitors cannot learn what SettleIQ does without logging in
2. **No user accounts** — Cannot create account, login, or persist data across sessions
3. **No organizations** — Cannot separate business data by tenant
4. **No billing** — Cannot subscribe or pay for the service
5. **No payment provider connections** — Cannot connect Stripe/Razorpay/etc.
6. **No data import templates** — Users must guess the required CSV/JSON format
7. **No guided onboarding** — First-time users don't know what to do
8. **Production decomposition returns 404** — Cannot inspect payout decomposition for real runs
9. **No empty state guidance** — Empty screens don't explain next steps
10. **No contextual help** — No tooltips or explanations of metrics

### Confusing Experiences
- `/auth` is the only entry point; no marketing/public pages
- Demo mode is read-only but this isn't clearly explained until investigation page
- Import validation requires API key (production), demo users can't test import
- Empty states show "No reconciliation runs yet" without guidance on how to create one

---

## 8. Capability Matrix

| Area | Feature | Status |
|------|---------|--------|
| Backend API | Reconciliation engine | Fully implemented |
| Backend API | Demo tokens (stateless HMAC) | Fully implemented |
| Backend API | API key authentication | Fully implemented |
| Backend API | Import validation | Fully implemented |
| Backend API | CSV/JSON export | Fully implemented |
| Backend API | Discrepancy investigation | Fully implemented |
| Backend API | Payout decomposition (demo) | Fully implemented |
| Backend API | Payout decomposition (production) | Missing (404) |
| Backend API | User accounts | Missing |
| Backend API | Organizations | Missing |
| Backend API | Billing/subscriptions | Missing |
| Backend API | Payment provider connections | Missing |
| Frontend | Dashboard pages (7) | Fully implemented |
| Frontend | Public website | Missing |
| Frontend | Auth pages (login/signup) | Partial (login only, no signup) |
| Frontend | Import page | Fully implemented |
| Frontend | Investigation page | Fully implemented |
| Frontend | Onboarding wizard | Missing |
| Frontend | Team management | Missing |
| Frontend | Billing portal | Missing |
| Frontend | Developer portal | Missing |
| Infrastructure | Vercel deployment | Working |
| Infrastructure | PostgreSQL persistence | Available (untested at scale) |
| Infrastructure | Multi-tenancy | Missing |

---

## 9. Root Causes of Usability Gap

1. **Product built for engineers, not operators** — All pages assume the user already understands reconciliation concepts
2. **No entry point for non-technical users** — `/auth` requires either an API key or knowledge of "Explore Public Demo"
3. **No data guidance** — Users must already know the CSV/JSON schema
4. **No progressive disclosure** — All features are equally visible regardless of user experience level
5. **No business context** — No organization, team, or billing context

---

## 10. Recommended Fix Priority

1. **P0:** Public website (Home, Features, Pricing) — explains what SettleIQ does
2. **P0:** User authentication (signup, login) — enables account creation
3. **P0:** Organization model — enables multi-tenancy
4. **P1:** Onboarding wizard — guides first-time users
5. **P1:** Import templates and data format guide — removes guesswork
6. **P1:** Production decomposition endpoint — completes the feature set
7. **P2:** Team management, billing, developer portal
8. **P2:** Payment provider connections
