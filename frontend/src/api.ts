const API_BASE = '/v1'

export type AuthMode = 'none' | 'api-key' | 'demo'

const API_KEY_STORAGE_KEY = 'settleiq_api_key'
const DEMO_TOKEN_STORAGE_KEY = 'settleiq_demo_token'

function getAuthMode(): AuthMode {
  const demoToken = sessionStorage.getItem(DEMO_TOKEN_STORAGE_KEY)
  const apiKey = sessionStorage.getItem(API_KEY_STORAGE_KEY)
  if (demoToken) return 'demo'
  if (apiKey) return 'api-key'
  return 'none'
}

function clearAuth(): void {
  sessionStorage.removeItem(API_KEY_STORAGE_KEY)
  sessionStorage.removeItem(DEMO_TOKEN_STORAGE_KEY)
}

function getAuthHeaders(): Record<string, string> {
  const mode = getAuthMode()
  if (mode === 'demo') {
    const token = sessionStorage.getItem(DEMO_TOKEN_STORAGE_KEY)
    return token ? { 'X-Demo-Token': token } : {}
  }
  const apiKey = sessionStorage.getItem(API_KEY_STORAGE_KEY)
  return apiKey ? { 'X-API-Key': apiKey } : {}
}

function demoPath(path: string): string {
  return path.startsWith('/demo/') ? path : `/demo/${path.replace(/^\//, '')}`
}

interface ApiErrorBody {
  detail?: string | { error?: string; detail?: string }
  error?: string
}

function errorMessage(body: ApiErrorBody, status: number, statusText: string): string {
  const detail = body?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (detail && typeof detail === 'object') {
    if (typeof detail.detail === 'string' && detail.detail.trim()) return detail.detail
    if (typeof detail.error === 'string' && detail.error.trim()) return detail.error
  }
  if (typeof body?.error === 'string' && body.error.trim()) return body.error
  return `HTTP ${status}${statusText ? ` ${statusText}` : ''}`
}

async function parseError(res: Response): Promise<string> {
  let body: ApiErrorBody = {}
  try {
    body = (await res.json()) as ApiErrorBody
  } catch {
    // Non-JSON response (e.g. a gateway HTML page) - surface status info.
    body = {}
  }
  return errorMessage(body, res.status, res.statusText)
}

async function fetchApi<T>(path: string, options: RequestInit = {}): Promise<T> {
  const mode = getAuthMode()
  const targetPath = mode === 'demo' ? demoPath(path) : path
  const headers = new Headers({
    'Content-Type': 'application/json',
    ...options.headers,
  })
  if (mode === 'demo') {
    const token = sessionStorage.getItem(DEMO_TOKEN_STORAGE_KEY)
    if (token) headers.set('X-Demo-Token', token)
  } else {
    const apiKey = sessionStorage.getItem(API_KEY_STORAGE_KEY)
    if (apiKey) headers.set('X-API-Key', apiKey)
  }
  const res = await fetch(`${API_BASE}${targetPath}`, {
    headers,
    ...options,
  })
  if (!res.ok) {
    const message = await parseError(res)
    if (res.status === 401 || res.status === 403) {
      clearAuth()
      const reason = mode === 'demo' ? 'demo-expired' : 'unauthorized'
      // Redirect to auth screen - the App component will handle this.
      window.location.href = `/auth?reason=${reason}`
    }
    throw new Error(message)
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
      fetch(`${API_BASE}/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(payload),
      }).then(async r => {
        if (!r.ok) throw new Error(await parseError(r))
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
      fetchApi<{
        run_id: string
        count: number
        entries: Array<{
          sequence: number
          run_id: string
          event: string
          timestamp: string
          actor: string
          detail: string
          discrepancy_id?: string
        }>
      }>(`/runs/${id}/history`),
  },

  discrepancies: {
    list: (params?: { run_id?: string; type?: string; severity?: string }) => {
      const search = new URLSearchParams()
      if (params?.run_id) search.set('run_id', params.run_id)
      if (params?.type) search.set('type', params.type)
      if (params?.severity) search.set('severity', params.severity)
      return fetchApi<{ count: number; discrepancies: any[] }>(`/discrepancies?${search.toString()}`)
    },
    get: (id: string) => fetchApi<any>(`/discrepancies/${id}`),
    resolve: (id: string, reason: string, selectedCandidate?: string) =>
      fetch(`${API_BASE}/discrepancies/${id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ reason, selected_candidate: selectedCandidate }),
      }).then(async r => {
        if (!r.ok) throw new Error(await parseError(r))
        return r.json()
      }),
  },

  investigation: {
    get: (id: string) => fetchApi<InvestigationReport>(`/discrepancies/${id}/investigate`),
    trace: (runId: string, constituentId: string) =>
      fetchApi<TransactionTrace>(`/runs/${runId}/trace/${constituentId}`),
  },

  demo: {
    session: () =>
      fetch(`${API_BASE}/demo/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }).then(async r => {
        if (!r.ok) throw new Error(await parseError(r))
        return r.json()
      }),
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

  // Auth helpers
  auth: {
    setKey: (key: string) => sessionStorage.setItem(API_KEY_STORAGE_KEY, key),
    clearKey: clearAuth,
    hasKey: () => !!sessionStorage.getItem(API_KEY_STORAGE_KEY),
    getMode: getAuthMode,
    isDemo: () => getAuthMode() === 'demo',
    setDemoToken: (token: string) =>
      sessionStorage.setItem(DEMO_TOKEN_STORAGE_KEY, token),
    clearDemoToken: () => sessionStorage.removeItem(DEMO_TOKEN_STORAGE_KEY),
    getDemoToken: () => sessionStorage.getItem(DEMO_TOKEN_STORAGE_KEY),
  },
}