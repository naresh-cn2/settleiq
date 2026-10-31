import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export function AuthScreen() {
  const [apiKey, setApiKey] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!apiKey.trim()) {
      setError('Please enter your API key')
      return
    }
    setLoading(true)
    try {
      // Test the API key by making a simple authenticated request with the provided key
      const testKey = apiKey.trim()
      const res = await fetch('/v1/runs', {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': testKey,
        },
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(detail.detail || `HTTP ${res.status}`)
      }
      // If successful, store the key and redirect to home
      api.auth.setKey(testKey)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-header">
          <h1>SettleIQ</h1>
          <p className="subtitle">Financial Reconciliation Engine</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="apiKey">API Key</label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
              autoComplete="off"
              disabled={loading}
              aria-describedby="apiKeyHelp"
            />
            <small id="apiKeyHelp" className="form-help">
              Enter your SettleIQ API key to access the dashboard
            </small>
          </div>

          {error && <div className="auth-error" role="alert">{error}</div>}

          <button
            type="submit"
            className="auth-submit"
            disabled={loading || !apiKey.trim()}
          >
            {loading ? 'Verifying...' : 'Access Dashboard'}
          </button>
        </form>

        <div className="auth-footer">
          <p>Your API key is stored in session storage for this browser tab only.</p>
          <p>It is never sent to any third party or persisted beyond this session.</p>
        </div>
      </div>
    </div>
  )
}

export function HeaderAuth({ onLogout }: { onLogout: () => void }) {
  return (
    <button className="header-logout" onClick={onLogout} title="Logout">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
        <polyline points="16 17 21 12 16 7" />
        <line x1="21" y1="12" x2="9" y2="12" />
      </svg>
      <span>Logout</span>
    </button>
  )
}