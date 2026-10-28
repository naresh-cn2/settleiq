-- Migration 001: Initial PostgreSQL Schema for SettleIQ
-- Strict typing, relational integrity, non-negative checks, and exact audit tracking.

CREATE TABLE IF NOT EXISTS schema_migration (
    version INTEGER PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reconciliation_run (
    run_id VARCHAR(64) PRIMARY KEY,
    input_digest VARCHAR(64) NOT NULL,
    rule_version VARCHAR(32) NOT NULL,
    schema_version VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    declared_window VARCHAR(128) NOT NULL,
    numerator INTEGER NOT NULL CHECK (numerator >= 0),
    denominator INTEGER NOT NULL CHECK (denominator >= 0),
    methodology_version VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discrepancy (
    discrepancy_id VARCHAR(128) PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES reconciliation_run(run_id) ON DELETE RESTRICT,
    type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    constituent_kind VARCHAR(32) NOT NULL,
    constituent_id VARCHAR(128) NOT NULL,
    reason TEXT NOT NULL,
    age_days INTEGER NOT NULL CHECK (age_days >= 0),
    status VARCHAR(32) NOT NULL CHECK (status IN ('OPEN', 'ASSIGNED', 'INVESTIGATING', 'RESOLVED', 'DISMISSED'))
);

CREATE TABLE IF NOT EXISTS discrepancy_resolution (
    resolution_id VARCHAR(128) PRIMARY KEY,
    discrepancy_id VARCHAR(128) NOT NULL REFERENCES discrepancy(discrepancy_id) ON DELETE RESTRICT,
    run_id VARCHAR(64) NOT NULL REFERENCES reconciliation_run(run_id) ON DELETE RESTRICT,
    status VARCHAR(32) NOT NULL,
    reason TEXT NOT NULL,
    selected_candidate VARCHAR(256),
    resolved_by VARCHAR(128) NOT NULL,
    resolved_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS supersession (
    superseded_id VARCHAR(128) PRIMARY KEY,
    superseding_id VARCHAR(128) NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journal_entry (
    sequence BIGSERIAL PRIMARY KEY,
    prev_digest VARCHAR(64) NOT NULL,
    entry_digest VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance & foreign key lookups
CREATE INDEX IF NOT EXISTS ix_discrepancy_run ON discrepancy(run_id);
CREATE INDEX IF NOT EXISTS ix_discrepancy_type ON discrepancy(type);
CREATE INDEX IF NOT EXISTS ix_discrepancy_severity ON discrepancy(severity);
CREATE INDEX IF NOT EXISTS ix_resolution_discrepancy ON discrepancy_resolution(discrepancy_id);
CREATE INDEX IF NOT EXISTS ix_journal_sequence ON journal_entry(sequence);

INSERT INTO schema_migration (version, name)
VALUES (1, '001_initial_schema')
ON CONFLICT (version) DO NOTHING;
