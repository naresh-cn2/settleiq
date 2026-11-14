import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'

export function SignupPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!email.trim()) {
      setError('Please enter your email')
      return
    }
    if (!password.trim()) {
      setError('Please enter a password')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    setLoading(true)
    try {
      const session = await api.authApi.register({
        email: email.trim(),
        password,
        full_name: fullName.trim() || undefined,
        organization_name: organizationName.trim() || undefined,
      })
      api.auth.setUserSession({
        ...session,
        token: '', // Token is stored in HTTP-only cookie by the backend
      })
      api.auth.setUserId(session.user_id)
      navigate('/onboarding')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed')
    } finally {
      setLoading(false)
    }
  }
  const navigate = useNavigate()

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-brand">
          <span className="logo-icon">S</span>
          <span className="logo-text">SettleIQ</span>
        </div>
        <div className="auth-card">
          <div className="auth-header">
            <h1>Create account</h1>
            <p>Start reconciling your financial data</p>
          </div>
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="fullName">Full name</label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                placeholder="Jane Smith"
                autoComplete="name"
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@company.com"
                autoComplete="email"
                required
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
                minLength={8}
                required
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label htmlFor="organizationName">Organization name (optional)</label>
              <input
                id="organizationName"
                type="text"
                value={organizationName}
                onChange={e => setOrganizationName(e.target.value)}
                placeholder="Acme Corp"
                autoComplete="organization"
                disabled={loading}
              />
              <p className="form-help">
                Your organization is used to separate data between teams.
                You can add more later.
              </p>
            </div>
            {error && (
              <div className="auth-error" role="alert">
                {error}
              </div>
            )}
            <button
              type="submit"
              className="btn btn-primary btn-full"
              disabled={loading}
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>
          <div className="auth-footer">
            <p>
              Already have an account?{' '}
              <Link to="/login">Log in</Link>
            </p>
            <p>
              Want to try without an account?{' '}
              <Link to="/">Explore the public demo</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
