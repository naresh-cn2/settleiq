# SettleIQ — Deployment and Operations Manual

This document details the configuration, deployment, migration, backup, and operational procedures for SettleIQ.

---

## 1. Architecture Overview

SettleIQ is packaged as a dual-service containerized application:

1. **`settleiq-api`**: FastAPI application serving both the REST API (`/v1/*`) and the compiled React web dashboard (`/`). Runs as non-root user `settleiq` on port `8000`.
2. **`settleiq-postgres`**: PostgreSQL 16 relational database maintaining exact-decimal persistence and hash-chained journal entries, with automatic schema initialization via mounted migrations.

---

## 2. Quickstart with Docker Compose

### Prerequisites
* Docker 24.0+ and Docker Compose v2.20+
* 2 GB available RAM

### Deployment Steps

1. **Configure Environment Variables**:
   Create a `.env` file or export variables:
   ```bash
   POSTGRES_USER=settleiq
   POSTGRES_PASSWORD=your_strong_password_here
   POSTGRES_DB=settleiq_db
   SETTLEIQ_API_KEY=your_secure_api_key_here
   # Optional: enables the read-only "Explore Public Demo" experience.
   # Must be at least 32 characters of high-entropy random data.
   SETTLEIQ_DEMO_SECRET=your_64_character_random_demo_signing_secret
   ```

   `SETTLEIQ_DEMO_SECRET` signs stateless demo tokens with HMAC-SHA256. It is
   optional: when it is absent (or shorter than 32 characters) the public demo
   fails closed with HTTP 503, while API-key authentication keeps working.
   Never reuse `SETTLEIQ_API_KEY` as the demo secret, and never commit either
   value. Generate the demo secret with:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

2. **Launch Services**:
   ```bash
   docker compose up -d --build
   ```

3. **Verify Service Health**:
   ```bash
   docker compose ps
   curl -i http://localhost:8000/health
   ```

4. **Access the Application**:
   * **Dashboard**: `http://localhost:8000/`
   * **API Docs**: `http://localhost:8000/docs`
   * **Health**: `http://localhost:8000/health`

5. **Stop Services**:
   ```bash
   docker compose down
   # Or to destroy persistent data volumes:
   docker compose down -v
   ```

---

## 3. Database Migrations

PostgreSQL migrations are version-controlled in `src/settleiq/persistence/migrations/`:

* `001_initial_schema.sql`: Tables for `reconciliation_run`, `discrepancy`, `discrepancy_resolution`, `journal_entry`, and `supersession`, with strict check constraints and relational foreign keys.

### Executing Migrations Manually
When running outside Docker, apply migrations using:
```bash
python -c "from settleiq.persistence import open_store; open_store('postgresql://settleiq:pass@localhost:5432/settleiq_db')"
```

---

## 4. Backup and Disaster Recovery

### Creating a Database Backup
```bash
docker exec -t settleiq-postgres pg_dump -U settleiq -d settleiq_db -F c -b -v -f /var/lib/postgresql/data/settleiq_backup.dump
docker cp settleiq-postgres:/var/lib/postgresql/data/settleiq_backup.dump ./settleiq_backup.dump
```

### Restoring from Backup
```bash
docker cp ./settleiq_backup.dump settleiq-postgres:/tmp/settleiq_backup.dump
docker exec -t settleiq-postgres pg_restore -U settleiq -d settleiq_db --clean --if-exists /tmp/settleiq_backup.dump
```

---

## 5. Security and Operational Hardening

* **Non-Root Execution**: Container runs under UID 1000 (`settleiq`).
* **Mutating API Protection**: When `SETTLEIQ_API_KEY` is set, all mutating requests (`POST /v1/*`) require header `X-API-Key`.
* **Public Demo Isolation**: Demo tokens are HMAC-SHA256 signed, expire after `SETTLEIQ_DEMO_TOKEN_TTL_SECS` (default 1800 seconds), and are only accepted by `/v1/demo/*` routes. Demo sessions never read or write production reconciliation data.
* **Demo Fail-Closed Behavior**: If `SETTLEIQ_DEMO_SECRET` is missing or shorter than 32 characters, `POST /v1/demo/session` returns HTTP 503 instead of issuing a weak token.
* **Payload Size Limit**: Request bodies exceeding 10MB are rejected with HTTP 413.
* **Security Headers**: All HTTP responses include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict Content Security Policy.
* **No Caching of API Responses**: `/v1/*` and `/health` responses are sent with `Cache-Control: no-store` so session tokens and mutable audit data are never cached.

---

## 6. Vercel Deployment (Public Demo)

The public deployment at `https://settleiq-zeta.vercel.app` is defined by
[`vercel.json`](../vercel.json), which deploys a single Vercel service:

* `app`: FastAPI (`src/settleiq/api/app.py`) handling `/health`, `/v1/*`, and
  the compiled React dashboard from `src/settleiq/static` (including SPA
  fallback for deep links such as `/auth` and `/runs/:runId`).

The frontend bundle must be rebuilt and copied into `src/settleiq/static`
before deploying (`npm --prefix frontend run build`, then copy `frontend/dist`
over `src/settleiq/static`). The Docker image performs this step automatically.

### Required Environment Variables

Configure these in **Vercel → Project → Settings → Environment Variables** for
both **Production** and **Preview**:

| Variable | Required | Purpose |
|:---|:---|:---|
| `SETTLEIQ_API_KEY` | Yes | Protects production `POST /v1/*` endpoints. |
| `SETTLEIQ_DEMO_SECRET` | For demo | HMAC key for stateless demo tokens. Minimum 32 characters. |
| `SETTLEIQ_CORS_ORIGIN` | Recommended | Exact browser origin allowed to call the API. |
| `SETTLEIQ_DB_PATH` | Recommended | Persistence path or PostgreSQL URL for production runs. |

Environment variable changes do **not** apply to existing deployments. After
adding or rotating `SETTLEIQ_DEMO_SECRET`, create a new production deployment
(for example `vercel --prod` or redeploy the latest commit). Rotating the secret
immediately invalidates every previously issued demo token, which is the
intended revocation mechanism.

### Verifying the Deployed Public Demo

The production-equivalent browser verifier drives real headless Chrome through
the public auth page and demo workflow:

```bash
node frontend/scripts/verify_public_demo_e2e.mjs \
  --mode production \
  --app-url https://settleiq-zeta.vercel.app \
  --api-key "$SETTLEIQ_API_KEY"
```

If you prefer not to put the key on the command line, pass
`--api-key-file ./local_api_key.txt` and keep that file out of version control.

Expected evidence is written to `proof/e2e/public_demo_production_latest.json`.
A healthy deployment reports `POST /v1/demo/session` as HTTP 201, loads the
dashboard, discrepancies, investigation trace, metrics, and history, and rejects
demo tokens on production `/v1/runs` routes.

### Common Failure: Demo Returns HTTP 503

```
{"error":"unavailable","detail":"Public demo is temporarily unavailable: the server demo secret is not configured."}
```

This means the running deployment cannot see `SETTLEIQ_DEMO_SECRET`, or the
value is shorter than 32 characters. Confirm the variable exists in the target
environment, then trigger a fresh deployment. The backend logs a warning at
startup when the secret is missing and an error when it is too short.

