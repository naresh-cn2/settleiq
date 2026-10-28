export interface Run {
  run_id: string
  input_digest: string
  rule_version: string
  schema_version: string
  numerator: number
  denominator: number
  rate: number
  discrepancy_count: number
  status: string
}

export interface RunListResponse {
  count: number
  runs: Run[]
}

export interface Discrepancy {
  discrepancy_id: string
  type: string
  severity: string
  constituent_kind: string
  constituent_id: string
  reason: string
  age_days: number
  status: string
  resolution_history: Array<{
    reason: string
    selected_candidate?: string
    timestamp: string
  }>
}

export interface DiscrepancyListResponse {
  count: number
  discrepancies: Discrepancy[]
}

export interface MetricsResponse {
  run_id: string
  numerator: number
  denominator: number
  rate: number
  methodology_version: string
  rule_version: string
}

export interface Decomposition {
  payout_id: string
  batch_reference: string
  gross: string
  fees: string
  refunds: string
  adjustments: string
  net_expected: string
  net_paid: string
  residual: string
  closes_exactly: boolean
  constituents: Constituent[]
}

export interface Constituent {
  kind: string
  source_id: string
  amount: string
  contribution: string
}

export interface DecompositionResponse {
  decompositions: Decomposition[]
}

export interface RunListResponse {
  count: number
  runs: Run[]
}

export interface DiscrepancyListResponse {
  count: number
  discrepancies: Discrepancy[]
}

export interface RunDetailResponse {
  run: {
    run_id: string
    input_digest: string
    rule_version: string
    schema_version: string
    numerator: number
    denominator: number
    rate: number
    discrepancy_count: number
    status: string
  }
  discrepancy_count: number
}