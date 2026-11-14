import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

export function OnboardingPage() {
  const [step, setStep] = useState(1)
  const navigate = useNavigate()

  const steps = [
    { title: 'Welcome', description: 'Tell us about your organization' },
    { title: 'Connect data', description: 'Import or connect your financial data' },
    { title: 'Configure', description: 'Set reconciliation preferences' },
    { title: 'Complete', description: "You're ready to reconcile" },
  ]

  const handleNext = () => {
    if (step < steps.length) {
      setStep(step + 1)
    } else {
      navigate('/dashboard')
    }
  }

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1)
    }
  }

  return (
    <div className="onboarding-page">
      <div className="onboarding-container">
        <div className="onboarding-header">
          <div className="onboarding-brand">
            <span className="logo-icon">S</span>
            <span className="logo-text">SettleIQ</span>
          </div>
          <div className="onboarding-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${((step - 1) / (steps.length - 1)) * 100}%` }}
              />
            </div>
            <div className="progress-text">
              Step {step} of {steps.length}
            </div>
          </div>
        </div>

        <div className="onboarding-content">
          <div className="steps-indicator">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`step-indicator ${i + 1 === step ? 'active' : i + 1 < step ? 'completed' : ''}`}
              >
                {i + 1 < step ? '✓' : i + 1}
              </div>
            ))}
          </div>

          <div className="step-content">
            <h2>{steps[step - 1].title}</h2>
            <p className="step-description">{steps[step - 1].description}</p>

            {step === 1 && (
              <div className="welcome-card">
                <h3>Welcome to SettleIQ</h3>
                <p>
                  SettleIQ helps finance teams reconcile payment transactions,
                  processor payouts, and bank deposits with mathematical
                  certainty.
                </p>
                <div className="feature-list">
                  <div className="feature-item">
                    <span className="feature-check">✓</span>
                    Exact decimal arithmetic — no float errors
                  </div>
                  <div className="feature-item">
                    <span className="feature-check">✓</span>
                    Constituent-level payout decomposition
                  </div>
                  <div className="feature-item">
                    <span className="feature-check">✓</span>
                    Hash-chained audit journal
                  </div>
                  <div className="feature-item">
                    <span className="feature-check">✓</span>
                    Evidence-backed discrepancy investigation
                  </div>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="connect-card">
                <h3>How would you like to start?</h3>
                <div className="connect-options">
                  <button className="btn btn-outline btn-full" onClick={() => navigate('/import')}>
                    <span>📁</span>
                    <span>Import CSV or JSON file</span>
                  </button>
                  <button className="btn btn-outline btn-full" onClick={() => navigate('/connections')}>
                    <span>🔗</span>
                    <span>Connect payment provider</span>
                  </button>
                  <button className="btn btn-secondary btn-full" onClick={() => setStep(4)}>
                    <span>⏭️</span>
                    <span>Skip — explore the demo first</span>
                  </button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="configure-card">
                <h3>Reconciliation preferences</h3>
                <div className="pref-group">
                  <label className="pref-label">Default settlement window (days)</label>
                  <select className="pref-select" defaultValue="3">
                    <option value="1">1 day</option>
                    <option value="3">3 days</option>
                    <option value="7">7 days</option>
                    <option value="14">14 days</option>
                    <option value="30">30 days</option>
                  </select>
                </div>
                <div className="pref-group">
                  <label className="pref-label">Auto-match rules</label>
                  <div className="rule-list">
                    <div className="rule-item">
                      <input type="checkbox" defaultChecked disabled />
                      <label>R-EXACT-REFERENCE — Match by settlement reference</label>
                    </div>
                    <div className="rule-item">
                      <input type="checkbox" defaultChecked disabled />
                      <label>R-EXACT-AMOUNT — Match by amount and currency</label>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="complete-card">
                <h3>You're all set!</h3>
                <p>
                  Your SettleIQ workspace is ready. You can now import financial
                  data, run reconciliation, and investigate discrepancies.
                </p>
                <div className="complete-actions">
                  <Link to="/import" className="btn btn-primary">
                    Import data &raquo;
                  </Link>
                  <Link to="/" className="btn btn-outline">
                    Go to dashboard
                  </Link>
                </div>
              </div>
            )}
          </div>

          <div className="onboarding-footer">
            {step > 1 && (
              <button className="btn btn-outline" onClick={handleBack}>
                Back
              </button>
            )}
            <button
              className="btn btn-primary"
              onClick={handleNext}
              disabled={step === steps.length}
            >
              {step === steps.length ? 'Finish setup' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
