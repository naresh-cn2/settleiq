import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { RunsPage } from './pages/RunsPage'
import { DiscrepanciesPage } from './pages/DiscrepanciesPage'
import { InvestigationPage } from './pages/InvestigationPage'
import { MetricsPage } from './pages/MetricsPage'
import { HistoryPage } from './pages/HistoryPage'

function App() {
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
        <Routes>
          <Route path="/" element={<RunsPage />} />
          <Route path="/discrepancies" element={<DiscrepanciesPage />} />
          <Route path="/discrepancies/:id" element={<InvestigationPage />} />
          <Route path="/metrics" element={<MetricsPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
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

export default App