import { Link, useNavigate, useLocation } from 'react-router-dom'
import { api } from '../api'

export function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const mode = api.auth.getMode()
  const userSession = api.auth.getUserSession()

  const handleLogout = () => {
    api.auth.clearKey()
    api.auth.clearDemoToken()
    api.auth.clearUserSession()
    api.auth.clearUserId()
    navigate('/login', { replace: true })
  }

  const isDemo = mode === 'demo'
  const isUser = mode === 'user'
  const isPublicPage = location.pathname === '/' || location.pathname === '/features' || location.pathname === '/pricing'

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Link to="/" className="navbar-logo">
            <span className="logo-icon">S</span>
            <span className="logo-text">SettleIQ</span>
          </Link>
        </div>

        <div className="navbar-menu">
          {!isPublicPage && (
            <>
              <Link to="/" className="nav-link">Dashboard</Link>
              <Link to="/runs" className="nav-link">Runs</Link>
              <Link to="/discrepancies" className="nav-link">Discrepancies</Link>
              <Link to="/metrics" className="nav-link">Metrics</Link>
              <Link to="/history" className="nav-link">History</Link>
            </>
          )}
          {isPublicPage && (
            <>
              <Link to="/features" className="nav-link">Features</Link>
              <Link to="/pricing" className="nav-link">Pricing</Link>
            </>
          )}
        </div>

        <div className="navbar-actions">
          {isPublicPage ? (
            <>
              <Link to="/login" className="nav-btn nav-btn-outline">
                Log in
              </Link>
              <Link to="/signup" className="nav-btn nav-btn-primary">
                Get started
              </Link>
            </>
          ) : (
            <>
              {mode === 'none' && (
                <Link to="/login" className="nav-btn nav-btn-outline">
                  Log in
                </Link>
              )}
              {isDemo && (
                <>
                  <span className="nav-badge nav-badge-demo">Demo mode</span>
                  <button
                    className="nav-btn nav-btn-danger"
                    onClick={handleLogout}
                  >
                    Exit demo
                  </button>
                </>
              )}
              {isUser && (
                <>
                  <span className="nav-badge nav-badge-user">
                    {userSession?.email}
                  </span>
                  <button
                    className="nav-btn nav-btn-danger"
                    onClick={handleLogout}
                  >
                    Log out
                  </button>
                </>
              )}
              {mode === 'api-key' && (
                <>
                  <span className="nav-badge nav-badge-key">API key</span>
                  <button
                    className="nav-btn nav-btn-danger"
                    onClick={handleLogout}
                  >
                    Log out
                  </button>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-brand">
          <span className="logo-icon">S</span>
          <span className="logo-text">SettleIQ</span>
          <p className="footer-tagline">
            Financial reconciliation for modern finance teams.
          </p>
        </div>
        <div className="footer-links">
          <div className="footer-link-group">
            <h3>Product</h3>
            <Link to="/features">Features</Link>
            <Link to="/pricing">Pricing</Link>
            <Link to="/">Dashboard</Link>
          </div>
          <div className="footer-link-group">
            <h3>Company</h3>
            <a href="#">About</a>
            <a href="#">Contact</a>
            <a href="#">Status</a>
          </div>
          <div className="footer-link-group">
            <h3>Resources</h3>
            <a href="#">Documentation</a>
            <a href="#">API Reference</a>
            <a href="#">Security</a>
          </div>
        </div>
        <div className="footer-legal">
          <p>© {new Date().getFullYear()} SettleIQ. All rights reserved.</p>
          <p className="footer-legal-text">
            Synthetic demonstration data only. No real customer data is used
            in the public demo.
          </p>
        </div>
      </div>
    </footer>
  )
}
