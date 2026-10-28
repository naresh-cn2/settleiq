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
* **Payload Size Limit**: Request bodies exceeding 10MB are rejected with HTTP 413.
* **Security Headers**: All HTTP responses include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict Content Security Policy.

