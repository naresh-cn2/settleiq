import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <div className="page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-container">
          <div className="hero-content">
            <div className="hero-badge">
              <span className="badge-dot"></span>
              <span>Public demo available — no API key required</span>
            </div>
            <h1 className="hero-title">
              Reconcile payments with <span className="text-accent">mathematical certainty</span>
            </h1>
            <p className="hero-subtitle">
              SettleIQ compares payment transactions, processor payouts, and bank
              deposits to identify matched records, missing payments, incorrect
              amounts, unexpected fees, timing differences, and unexplained
              discrepancies — all with exact decimal arithmetic and a
              hash-chained audit trail.
            </p>
            <div className="hero-actions">
              <Link to="/signup" className="btn btn-primary btn-lg">
                Start for free
              </Link>
              <Link to="/" className="btn btn-outline btn-lg">
                Explore public demo
              </Link>
            </div>
          </div>
          <div className="hero-visual">
            <div className="hero-stat-card">
              <div className="stat-value">76%</div>
              <div className="stat-label">Auto-match rate</div>
            </div>
            <div className="hero-stat-card">
              <div className="stat-value">7</div>
              <div className="stat-label">Discrepancy types</div>
            </div>
            <div className="hero-stat-card">
              <div className="stat-value">0</div>
              <div className="stat-label">Float rounding errors</div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="how-it-works">
        <div className="section-container">
          <div className="section-header">
            <h2>How SettleIQ works</h2>
            <p className="section-subtitle">
              From raw transaction data to resolved discrepancies in four steps.
            </p>
          </div>
          <div className="steps-grid">
            <div className="step-card">
              <div className="step-number">1</div>
              <h3>Import your data</h3>
              <p>
                Upload CSV or JSON files containing charges, fees, refunds,
                payouts, and bank deposits. SettleIQ validates every record
                and quarantines any that fail.
              </p>
            </div>
            <div className="step-card">
              <div className="step-number">2</div>
              <h3>Automatic reconciliation</h3>
              <p>
                The engine decomposes each payout into its constituents and
                matches them using declared rules. No black-box heuristics —
                every match cites the rule and fields it used.
              </p>
            </div>
            <div className="step-card">
              <div className="step-number">3</div>
              <h3>Investigate discrepancies</h3>
              <p>
                Review typed discrepancies with visual transaction traces,
                ranked hypotheses, and supporting evidence. Resolve with a
                documented reason that's immutably journaled.
              </p>
            </div>
            <div className="step-card">
              <div className="step-number">4</div>
              <h3>Export and report</h3>
              <p>
                Export reconciliation results as JSON or CSV. Every run, every
                discrepancy, and every resolution is recorded in a tamper-
                evident audit journal.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Preview */}
      <section className="features-preview">
        <div className="section-container">
          <div className="section-header">
            <h2>Built for financial operations</h2>
            <p className="section-subtitle">
              Everything you need to close the books with confidence.
            </p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>Exact decimal arithmetic</h3>
              <p>
                No binary floating-point on financial paths. Every monetary
                operation uses exact decimal arithmetic with currency-aware
                precision validation.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔗</div>
              <h3>Hash-chained audit journal</h3>
              <p>
                Every run, discrepancy, and resolution is sealed in a SHA-256
                hash chain. Tampering is detectable — not just possible.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔍</div>
              <h3>Evidence-backed investigation</h3>
              <p>
                Visual transaction traces show the complete money journey.
                Ranked hypotheses explain root causes with supporting and
                contradicting evidence.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Transparent methodology</h3>
              <p>
                Match rate numerator and denominator are defined in code, not
                prose. Know exactly how your reconciliation rate is calculated.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta">
        <div className="cta-container">
          <h2>Ready to reconcile with confidence?</h2>
          <p>Start with the public demo or create a free account.</p>
          <div className="cta-actions">
            <Link to="/signup" className="btn btn-primary btn-lg">
              Create account
            </Link>
            <Link to="/" className="btn btn-outline btn-lg">
              Try the demo
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
