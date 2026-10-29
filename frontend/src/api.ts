const API_BASE = '/v1'

async function fetchApi<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(detail.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export interface TraceNode {
  node_id: string
  kind: string
  amount: string
  currency: string
  reference: string
  date: string
  status: string
  metadata: Record<string, any>
}

export interface TransactionTrace {
  nodes: TraceNode[]
  gross_amount: string
  fee_amount: string
  refund_amount: string
  net_expected: string
  net_paid: string
  bank_deposited: string
  residual: string
  is_closed: boolean
}

export interface Hypothesis {
  rank: number
  title: string
  description: string
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT'
  supporting_evidence: string[]
  contradicting_evidence: string[]
  recommended_action: string
}

export interface InvestigationReport {
  discrepancy_id: string
  type: string
  severity: string
  constituent_id: string
  status: string
  reason: string
  trace: TransactionTrace
  hypotheses: Hypothesis[]
  recommended_action: string
  draft_resolution: {
    action: string
    reason: string
    resolved_by: string
  }
}

export const api = {
  runs: {
    list: () => fetchApi<{ count: number; runs: any[] }>('/runs'),
    create: (payload: any) =>
      fetch('/v1/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).then(r => {
        if (!r.ok) return r.json().then(d => { throw new Error(d.detail) })
        return r.json()
      }),
    get: (id: string) => fetchApi<{ run: any; discrepancy_count: number }>(`/runs/${id}`),
    discrepancies: (id: string, params?: { type?: string; severity?: string }) => {
      const search = new URLSearchParams()
      if (params?.type) search.set('type', params.type)
      if (params?.severity) search.set('severity', params.severity)
      return fetchApi<{ count: number; discrepancies: any[] }>(`/runs/${id}/discrepancies?${search.toString()}`)
    },
    metrics: (id: string) =>
      fetchApi<{
        run_id: string
        numerator: number
        denominator: number
        rate: number
        methodology_version: string
        rule_version: string
      }>(`/runs/${id}/metrics`),
    export: (id: string) => fetchApi<any>(`/runs/${id}/export`),
    history: (id: string) =>
      fetchApi<any>(`/runs/${id}/history`),
  },

  discrepancies: {
    list: (params?: { type?: string; severity?: string }) => {
      const search = new URLSearchParams()
      if (params?.type) search.set('type', params.type)
      if (params?.severity) search.set('severity', params.severity)
      return fetchApi<{ count: number; discrepancies: any[] }>(`/discrepancies?${search.toString()}`)
    },
    get: (id: string) => fetchApi<any>(`/discrepancies/${id}`),
    resolve: (id: string, reason: string, selectedCandidate?: string) =>
      fetch(`/v1/discrepancies/${id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason, selected_candidate: selectedCandidate }),
      }).then(r => {
        if (!r.ok) return r.json().then(d => { throw new Error(d.detail) })
        return r.json()
      }),
  },

  investigation: {
    get: (id: string) => fetchApi<InvestigationReport>(`/discrepancies/${id}/investigate`),
    trace: (runId: string, constituentId: string) =>
      fetchApi<TransactionTrace>(`/runs/${runId}/trace/${constituentId}`),
  },

  demo: {
    seed: () =>
      fetchApi<{
        status: string
        run_id: string
        discrepancy_count: number
        numerator: number
        denominator: number
        rate: number
      }>('/demo/seed', { method: 'POST' }),
  },

  journal: {
    verify: () =>
      fetchApi<{
        intact: boolean
        findings: [number, string, string][]
        entries_verified: number
        head_digest: string
      }>('/journal/verify', { method: 'POST' }),
  },
}
