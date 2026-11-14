import {
  Routes,
  Route,
  Navigate,
  useLocation,
} from 'react-router-dom'
import { OverviewPage } from './pages/OverviewPage'
import { RunsPage } from './pages/RunsPage'
import { ImportPage } from './pages/ImportPage'
import { DiscrepanciesPage } from './pages/DiscrepanciesPage'
import { InvestigationPage } from './pages/InvestigationPage'
import { MetricsPage } from './pages/MetricsPage'
import { HistoryPage } from './pages/HistoryPage'
import { HomePage } from './pages/HomePage'
import { FeaturesPage } from './pages/FeaturesPage'
import { PricingPage } from './pages/PricingPage'
import { LoginPage } from './pages/LoginPage'
import { SignupPage } from './pages/SignupPage'
import { OnboardingPage } from './pages/OnboardingPage'
import { AuthScreen } from './components/AuthScreen'
import { Navbar, Footer } from './components/Navbar'
import { api } from './api'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const mode = api.auth.getMode()
  if (mode === 'none') {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function App() {
  const location = useLocation()
  void location.pathname

  return (
    <div className="app">
      <Navbar />
      <main className="main">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          {/* Auth route (demo + API key entry) */}
          <Route path="/auth" element={<AuthScreen />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <OverviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/runs"
            element={
              <ProtectedRoute>
                <RunsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/import"
            element={
              <ProtectedRoute>
                <ImportPage />
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
          <Route
            path="/onboarding"
            element={
              <ProtectedRoute>
                <OnboardingPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

export default App
