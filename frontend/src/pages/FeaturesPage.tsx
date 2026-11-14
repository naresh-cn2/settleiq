import { Link } from 'react-router-dom'

export function FeaturesPage() {
  return (
    <div className="page">
      <section className="hero">
        <div className="hero-container">
          <div className="hero-content">
            <span className="hero-badge">Product features</span>
            <h1>Everything you need to reconcile payments</h1>
            <p>
              SettleIQ combines exact decimal arithmetic, constituent-level
              settlement decomposition, and a cryptographically verifiable
              audit journal into a single reconciliation platform.
            </p>
          </div>
        </div>
      </section>

      <section className="section-container">
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">💯</div>
            <h3>Exact decimal arithmetic</h3>
            <p>
              No binary floating-point on financial paths. Every monetary
              operation uses exact decimal arithmetic with currency-aware
              precision validation.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🧩</div>
            <h3>Payout decomposition</h3>
            <p>
              Each payout is decomposed into charges, fees, refunds, and
              adjustments. The composition must close exactly — any residual
              is surfaced as a typed discrepancy.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Transaction traces</h3>
            <p>
              Visual transaction traces show the complete money journey from
              charge to bank deposit. Every node carries amounts, references,
              and dates.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>Evidence-backed hypotheses</h3>
            <p>
              Discrepancies come with ranked hypotheses, supporting and
              contradicting evidence, and recommended actions. No guessing.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔒</div>
            <h3>Hash-chained audit journal</h3>
            <p>
              Every run, discrepancy, and resolution is sealed in a SHA-256
              hash chain. Tampering is detectable — not just possible.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📤</div>
            <h3>JSON and CSV export</h3>
            <p>
              Export reconciliation results as JSON or CSV. Every export
              carries run identity and rule version for traceability.
            </p>
          </div>
        </div>
      </section>

      <section className="section-container">
        <div className="discrepancy-types">
          <h2>Discrepancy types SettleIQ detects</h2>
          <div className="types-grid">
            <div className="type-card">
              <span className="type-badge type-net-gross">NET_GROSS_BREAK</span>
              <h3>Net/gross break</h3>
              <p>Batch composition doesn't close — payout paid doesn't match net expected.</p>
            </div>
            <div className="type-card">
              <span className="type-badge type-amount">AMOUNT_BREAK</span>
              <h3>Amount break</h3>
              <p>Payout amount differs from bank settlement deposit.</p>
            </div>
            <div className="type-card">
              <span className="type-badge type-timing">TIMING_BREAK</span>
              <h3>Timing break</h3>
              <p>Settlement posted outside the declared window.</p>
            </div>
            <div className="type-card">
              <span className="type-badge type-phantom-proc">PHANTOM_PROCESSOR</span>
              <h3>Phantom processor</h3>
              <p>Processor-side record with no corresponding payout.</p>
            </div>
            <div className="type-card">
              <span className="type-badge type-phantom-bank">PHANTOM_BANK</span>
              <h3>Phantom bank</h3>
              <p>Bank deposit with no matching payout reference.</p>
            </div>
            <div className="type-card">
              <span className="type-badge type-ambiguous">AMBIGUOUS_MATCH</span>
              <h3>Ambiguous match</h3>
              <p>Multiple equally valid candidates — engine doesn't choose.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="cta">
        <div className="cta-container">
          <h2>Start reconciling today</h2>
          <p>Try the public demo or create a free account.</p>
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
