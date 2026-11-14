export function PricingPage() {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: '/month',
      description: 'For individuals and small teams getting started',
      features: [
        'Up to 1,000 records per month',
        'Public demo access',
        'CSV and JSON import',
        'Basic discrepancy investigation',
        'JSON and CSV export',
      ],
      buttonText: 'Get started free',
      buttonVariant: 'outline',
      popular: false,
    },
    {
      name: 'Starter',
      price: '$49',
      period: '/month',
      description: 'For freelancers and small businesses',
      features: [
        'Up to 10,000 records per month',
        'Unlimited reconciliation runs',
        'API key access',
        'Email support',
        '30-day data retention',
      ],
      buttonText: 'Choose Starter',
      buttonVariant: 'primary',
      popular: false,
    },
    {
      name: 'Growth',
      price: '$149',
      period: '/month',
      description: 'For growing finance teams',
      features: [
        'Up to 100,000 records per month',
        'Everything in Starter, plus:',
        'API rate limit: 1,000 req/hour',
        'Team members (up to 5)',
        'Priority email support',
        '90-day data retention',
        'Custom reconciliation rules',
      ],
      buttonText: 'Choose Growth',
      buttonVariant: 'primary',
      popular: true,
    },
    {
      name: 'Business',
      price: '$499',
      period: '/month',
      description: 'For larger finance teams',
      features: [
        'Up to 1,000,000 records per month',
        'Everything in Growth, plus:',
        'API rate limit: 5,000 req/hour',
        'Team members (up to 25)',
        'Phone and email support',
        '1-year data retention',
        'SSO and RBAC',
        'Custom integrations',
      ],
      buttonText: 'Contact sales',
      buttonVariant: 'outline',
      popular: false,
    },
  ]

  return (
    <div className="page">
      <section className="hero">
        <div className="hero-container">
          <div className="hero-content">
            <span className="hero-badge">Simple, transparent pricing</span>
            <h1>Pricing that scales with you</h1>
            <p>
              Choose the plan that fits your reconciliation volume. All paid
              plans include API access, audit journaling, and priority support.
            </p>
          </div>
        </div>
      </section>

      <section className="section-container">
        <div className="pricing-grid">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`pricing-card ${plan.popular ? 'pricing-card-popular' : ''}`}
            >
              {plan.popular && (
                <div className="popular-badge">Most popular</div>
              )}
              <div className="plan-header">
                <h3>{plan.name}</h3>
                <p className="plan-description">{plan.description}</p>
              </div>
              <div className="plan-price">
                <span className="price-currency">{plan.price.split('$')[0]}</span>
                <span className="price-value">{plan.price.split('$')[1]}</span>
                <span className="price-period">{plan.period}</span>
              </div>
              <ul className="plan-features">
                {plan.features.map((f, i) => (
                  <li key={i} className="feature-item">
                    <span className="feature-check">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              <button className={`btn ${plan.buttonVariant === 'primary' ? 'btn-primary' : 'btn-outline'} btn-full`}>
                {plan.buttonText}
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="section-container">
        <div className="faq-section">
          <h2>Frequently asked questions</h2>
          <div className="faq-grid">
            <div className="faq-item">
              <h3>Can I try before I buy?</h3>
              <p>Yes. The public demo is free and uses synthetic data. Create a free account to import your own data.</p>
            </div>
            <div className="faq-item">
              <h3>What happens when I exceed my record limit?</h3>
              <p>You'll be notified when you reach 80% of your monthly limit. You can upgrade or wait for the next billing cycle.</p>
            </div>
            <div className="faq-item">
              <h3>Can I change plans later?</h3>
              <p>Yes. You can upgrade or downgrade at any time. Changes take effect immediately.</p>
            </div>
            <div className="faq-item">
              <h3>Is my data secure?</h3>
              <p>Yes. All data is encrypted in transit and at rest. We use tenant isolation and never mix customer data.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
