const API_BASE = '/v1'

async function api<T>(path: string, options: RequestInit = {}): Promise<any> {
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

export const api = {
  runs: {
    list: () => api<{ count: number; runs: any[] }>('/runs'),
    create: (payload: any) =>
      fetch('/v1/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).then(r => {
        if (!r.ok) return r.json().then(d => { throw new Error(d.detail) })
        return r.json()
      }),
    get: (id: string) => api<{ run: any; discrepancy_count: number }>(`/runs/${id}`),
    discrepancies: (id: string, params?: { type?: string; severity?: string }) =>
      api<{ count: number; discrepancies: any[] }>(`/runs/${id}/discrepancies`, {
        method: 'GET',
        // query params handled by URLSearchParams
      }),
    metrics: (id: string) =>
      api<{
        run_id: string
        numerator: number
        denominator: number
        rate: number
        methodology_version: string
        rule_version: string
      }>(`/runs/${id}/metrics`),
    export: (id: string) => api<any>(`/runs/${id}/export`),
    history: (id: string) =>
      api<any>(`/runs/${id}/history`),
  },

  discrepancies: {
    list: (params?: { type?: string; severity?: string }) =>
      api<{ count: number; discrepancies: any[] }>(
        `/discrepancies?${new URLSearchParams(params as any).toString()}`
      ),
    get: (id: string) => api<any>(`/discrepancies/${id}`),
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

  journal: {
    verify: () =>
      api<{
        intact: boolean
        findings: [number, string, string][]
        entries_verified: number
        head_digest: string
      }>('/journal/verify', { method: 'POST' }),
  },

  runs: {
    list: () => api<{ count: number; runs: any[] }>('/runs'),
    create: (payload: any) =>
      fetch('/v1/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).then(r => {
        if (!r.ok) return r.json().then(d => { throw new Error(d.detail) })
        return r.json()
      }),
    get: (id: string) =>
      api<{ run: any; discrepancy_count: number }>(`/runs/${id}`),
    discrepancies: (id: string, params?: { type?: string; severity?: string }) =>
      api<{ count: number; discrepancies: any[] }>(
        `/runs/${id}/discrepancies${new URLSearchParams(params as any).toString()}`
      ),
    metrics: (id: string) =>
      api<{
        run_id: string
        numerator: number
        denominator: number
        rate: number
        methodology_version: string
        rule_version: string
      }>(`/runs/${id}/metrics`),
    export: (id: string) => api<any>(`/runs/${id}/export`),
    history: (id: string) =>
      api<any>(`/runs/${id}/history`),
  },

  discrepancies: {
    list: (params?: { type?: string; severity?: string }) =>
      api<{ count: number; discrepancies: any[] }>(
        `/discrepancies?${new URLSearchParams(params as any).toString()}`
      ),
    get: (id: string) => api<any>(`/discrepancies/${id}`),
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

  journal: {
    verify: () =>
      api<{
        intact: boolean
        findings: [number, string, string][]
        entries_verified: number
        head_digest: string
      }>('/journal/verify', { method: 'POST' }),
  },
}