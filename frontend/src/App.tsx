import { Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom'
import { RunsPage } from './pages/RunsPage'
import { DiscrepanciesPage } from './pages/DiscrepanciesPage'
import { InvestigationPage } from './pages/InvestigationPage'
import { MetricsPage } from './pages/MetricsPage'
import { HistoryPage } from './pages/HistoryPage'
import { AuthScreen, HeaderAuth } from './components/AuthScreen'
import { api } from './api'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!api.auth.hasKey()) {
    return <Navigate to="/auth" replace />
  }
  return <>{children}</>
}

function App() {
  const navigate = useNavigate()

  const handleLogout = () => {
    api.auth.clearKey()
    navigate('/auth', { replace: true })
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
          <HeaderAuth onLogout={handleLogout} />
        </nav>
      </header>
      <main className="main">
        <Routes>
          <Route path="/auth" element={<AuthScreen />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <RunsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/discrepancies"
            element={
              <ProtectedRoute>
                <DiscrepanciesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/discrepancies/:id"
            element={
              <ProtectedRoute>
                <InvestigationPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/metrics"
            element={
              <ProtectedRoute>
                <MetricsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            }
          />
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