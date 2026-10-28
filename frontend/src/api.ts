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