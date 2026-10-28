# SettleIQ — Security Architecture and Threat Model Review

This document provides the formal security review of SettleIQ across all 17 security dimensions required for financial systems.

---

## 1. Security Baseline & Threat Model

### Trust Boundaries
1. **Financial Ingest Boundary**: External JSON payloads from payment processors (e.g., Stripe) and internal ledger files. Input must be validated fail-closed.
2. **REST API Boundary**: FastAPI application exposing management and investigation endpoints. Protected by IP rate limiting, request size limits, and constant-time API key verification.
3. **Storage Boundary**: Persistence stores (PostgreSQL and SQLite) holding runs, discrepancies, resolutions, and audit journal entries.
4. **Audit Journal Boundary**: Immutable append-only cryptographic hash chain.

---

## 2. Assessment of the 17 Security Dimensions

### 1. Authentication and Authorization
* **Design**: Deployable with dual posture:
  * **Local Demonstration Mode**: Loopback requests (`localhost`, `127.0.0.1`) execute with local developer permissions.
  * **Enforced Network Mode**: When `SETTLEIQ_API_KEY` is configured, all mutating endpoints (`POST /v1/*`) mandate the `X-API-Key` header.
* **Limitation**: An API key is a service-to-service authentication mechanism. A multi-tenant enterprise deployment requires downstream OAuth2 / OIDC and fine-grained Role-Based Access Control (RBAC).

### 2. Timing Attack Defense (Constant-Time Verification)
* **Design**: API key validation uses `hmac.compare_digest` in `security_and_limits_middleware`. This eliminates side-channel timing leaks during key comparison.

### 3. Rate Limiting and DoS Protection
* **Design**: Sliding-window rate limiter tracks request frequency per client IP address. Configurable via `SETTLEIQ_RATE_LIMIT` (default: 120 req/min). Burst traffic beyond the threshold receives HTTP 429 (`rate_limit_exceeded`) with a `Retry-After: 60` header.

### 4. Resource & Payload Size Limits
* **Design**: Request body size is inspected prior to parsing. Payloads exceeding 10MB are rejected with HTTP 413 (`payload_too_large`), preventing buffer exhaustion.

### 5. Input Validation & Fail-Closed Ingest
* **Design**: String-based monetary inputs enforce exact decimal arithmetic. Any JSON number parsed into a binary float raises `SourceAdapterError`. Missing required fields or duplicate records within a batch trigger typed quarantine reasons (`MISSING_FIELD`, `DUPLICATE`, `UNSUPPORTED_CURRENCY`).

### 6. SQL Injection Prevention
* **Design**:
  * PostgreSQL persistence (`PostgresPersistence`) utilizes DB-API `%s` parameterized queries exclusively.
  * SQLite persistence (`Persistence`) uses `?` parameterized queries.
  * Table digest lookups enforce a strict frozen allowlist (`ALLOWED_TABLES`), preventing arbitrary table injection.

### 7. Cross-Site Scripting (XSS) & Frontend Security
* **Design**: React JSX escapes rendered template variables. HTTP responses include:
  * `Content-Security-Policy`: Restricts scripts and connections to `'self'`.
  * `X-Content-Type-Options: nosniff`.
  * `X-Frame-Options: DENY`: Prevents clickjacking.
  * `X-XSS-Protection: 1; mode=block`.

### 8. CORS Configuration
* **Design**: FastAPI `CORSMiddleware` restricts permitted origins strictly to local development addresses (`localhost:5173`, `127.0.0.1:5173`, `localhost:8000`). Wildcard `*` origins are prohibited.

### 9. Error Message Leakage & Information Disclosure
* **Design**: Reconciliation errors and database failures log stack traces internally to application logs while returning sanitized error descriptors (`"reconciliation_failed"`) to external clients.

### 10. Audit Journal Integrity and Threat Model
* **Guarantees**:
  * SHA-256 hash chaining over `prev_digest` and canonical JSON payload.
  * Detects payload modification (`PAYLOAD_MODIFIED`).
  * Detects digest tampering (`DIGEST_MODIFIED`).
  * Detects entry deletion from the middle (`ENTRY_DELETED`).
  * Detects reordering and duplicate injection (`ENTRY_REORDERED`, `ENTRY_DUPLICATED`).
* **Honest Limitations**:
  * **Tail Truncation**: Deleting entries from the end leaves the remaining chain valid. Detecting tail truncation requires external head digest anchoring on an external schedule.
  * **Genesis Rewrite**: An attacker with direct database root access could rewrite the entire table from genesis. Anchoring the latest head digest to an external ledger or immutable storage mitigates this risk.

### 11. Transactional Atomicity & Data Consistency
* **Design**: Discrepancy resolutions and run records write to relational tables and the audit journal within the same transaction (`BEGIN IMMEDIATE` / `COMMIT`). If either write fails, the entire transaction rolls back.

### 12. Sensitive Data & PII Exposure
* **Design**: Monetary records and customer data are synthetic (`DataProvenance.SYNTHETIC`). Real data requires explicit environment authorization (`is_real_data_authorized()`). Bank accounts are masked to the last 3 digits (`bank_account_last3`).

### 13. Dependency Vulnerabilities
* **Design**: Core dependencies (`fastapi`, `pydantic`, `uvicorn`, `psycopg`) are maintained at current patch releases.

### 14. Non-Root Execution
* **Design**: The production Dockerfile creates and runs under user `settleiq` (UID 1000). Root execution inside containers is blocked.

### 15. Backup and Disaster Recovery
* **Design**: Documented procedures in `docs/DEPLOYMENT.md` for PostgreSQL binary dumps (`pg_dump -F c`) and atomic restore (`pg_restore --clean`).

### 16. Data Retention and Archival
* **Design**: Run identity is deterministic (`input_digest` + parameters). Identical inputs produce identical run identities, avoiding runaway duplicate data accumulation.

### 17. Operational Health Monitoring
* **Design**: Liveness check at `/health` returns `{ "status": "ok", "api_version": "1" }`. Container healthchecks probe this endpoint every 30 seconds.

