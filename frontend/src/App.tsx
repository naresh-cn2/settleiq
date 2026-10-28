import { Routes, Route, Link, Outlet, useNavigate } from 'react-router-dom'
import { RunsPage } from './pages/RunsPage'
import { DiscrepanciesPage } from './pages/DiscrepanciesPage'
import { InvestigationPage } from './pages/InvestigationPage'
import { MetricsPage } from './pages/MetricsPage'
import { HistoryPage } from './pages/HistoryPage'

const API_BASE = '/v1'

export default function App() {
  const navigate = useNavigate()

  const handleApiError = (error: unknown) => {
    console.error('API error:', error)
    // Could add toast/notification here
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <Link to="/" className="brand-link">SettleIQ</Link>
        </div>
        <nav className="header-nav">
          <NavLink to="/">Runs</NavLink>
          <NavLink to="/discrepancies">Discrepancies</NavLink>
          <NavLink to="/metrics">Metrics</NavLink>
          <NavLink to="/history">History</NavLink>
        </nav>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <footer className="footer">
        <span>SettleIQ - Financial Reconciliation Engine</span>
      </footer>
    </div>
  )
}

function NavLink({ children, to }: { children: React.ReactNode; to: string }) {
  const navigate = useNavigate()
  return (
    <button
      className="nav-link"
      onClick={() => navigate(to)}
      title={to}
    >
      {children}
    </button>
  )
}

function Routes() {
  return (
    <Routes>
      <Route path="/" element={<RunsPage />} />
      <Route path="/discrepancies" element={<DiscrepanciesPage />} />
      <Route path="/discrepancies/:id" element={<InvestigationPage />} />
      <Route path="/metrics" element={<MetricsPage />} />
      <Route path="/history" element={<HistoryPage />} />
    </Routes>
  )
}

const API_BASE = '/v1'

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
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

// --- Types ---
interface Run {
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

interface Discrepancy {
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

interface RunListResponse {
  count: number
  runs: Run[]
}

interface DiscrepancyListResponse {
  count: number
  discrepancies: Discrepancy[]
}

interface MetricsResponse {
  run_id: string
  numerator: number
  denominator: number
  rate: number
  methodology_version: string
  rule_version: string
}

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

interface Decomposition {
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

interface Constituent {
  kind: string
  source_id: string
  amount: string
  contribution: string
}