# SettleIQ — Commercial Product Comparison Matrix (25 Dimensions)

**Document ID:** SETTLEIQ-RES-002  
**Status:** ACTIVE  

| # | Dimension | BlackLine | Modern Treasury | Numeric | HighRadius | SettleIQ (Ours) |
|:---|:---|:---|:---|:---|:---|:---|
| **1** | **Core Arithmetic** | Floating point / DB decimal | String/Integer Minor Units | String/Decimal | DB Decimal | **`decimal.Decimal` (AST Zero-Float Enforced)** |
| **2** | **Monetary Precision** | Standard DB scale (2-4) | Integer cents | Currency dependent | Standard scale | **ISO 4217 Currency Exponents Enforced** |
| **3** | **Payout Decomposition** | Monolithic compare | Ledger accounts | Batch total | Invoice total | **Algebraic Constituent Decomposition** |
| **4** | **Residual Handling** | Rounding GL absorption | Rebalance entry | Silent variance | Unapplied cash | **Explicit First-Class `RESIDUAL` Entity** |
| **5** | **Matching Engine** | Rules engine | Double-entry | AI / Rule hybrid | ML / Probabilistic | **Deterministic Total-Order Rules** |
| **6** | **Ambiguity Resolution**| First-match / manual | N/A | Heuristic score | Probability rank | **Whole Candidate Set Preserved; Zero Guessing** |
| **7** | **Audit Trail** | Database audit logs | Event stream | Activity log | Activity log | **Cryptographic SHA-256 Hash Chained** |
| **8** | **Tamper Detection** | DBA / DB logs | System logs | None published | None published | **Automated Chain Verification on Read** |
| **9** | **Deterministic Reruns**| No (ambient time) | Event replay | No (live sync) | No (dynamic ML) | **100% Byte-Identical Preimages** |
| **10**| **Quarantine Isolation**| Error CSV export | Webhook error | Ingestion alert | Exception tab | **Typed Ingestion Quarantine Stream** |
| **11**| **AI Integration** | Limited / Roadmap | None | Suggestion AI | Cash matching ML| **Evidence-Backed AI Root-Cause Investigator** |
| **12**| **AI Uncertainty** | N/A | N/A | Rarely stated | Confidence score| **Explicit `INSUFFICIENT_EVIDENCE` Exit** |
| **13**| **Human-in-the-Loop** | Yes (Approval matrix)| Yes (Admin API) | Yes (User click) | Yes (User click)| **Mandatory Transactional Human Signoff** |
| **14**| **API Availability** | SOAP / OData / Legacy| Modern REST | Internal sync | Proprietary API | **Open REST API (FastAPI / OpenAPI 3.1)** |
| **15**| **API Idempotency** | Partial | Header key | None | Partial | **Deterministic Identity & Header Replay** |
| **16**| **Database Support** | Proprietary Cloud | Proprietary Cloud | Hosted SaaS | Proprietary Cloud| **Dual SQLite & PostgreSQL 16 Migrations** |
| **17**| **Deployment Options** | Multi-tenant SaaS | Multi-tenant SaaS | Multi-tenant SaaS | Multi-tenant SaaS| **Docker, Docker Compose, Single Binary** |
| **18**| **Local Development** | Not possible | Sandbox API | Not possible | Not possible | **Single-Command Local (`docker compose up`)** |
| **19**| **Source Normalization**| Custom ETL scripts | Native APIs | Accounting sync | Bank scrapers | **Frozen `SourceAdapter` Protocol + Stripe** |
| **20**| **Performance (100k)**| Batch job (minutes) | Streaming | Not published | Batch job | **<38 seconds (3,752 rec/s throughput)** |
| **21**| **Peak Memory (100k)** | Enterprise server | Distributed | Cloud memory | Enterprise server| **191.29 MB RAM (Linear $O(N)$)** |
| **22**| **Frontend Tech** | Enterprise Web | React Dashboard | Modern React | Enterprise Web | **React 18, TypeScript, Tailwind SPA** |
| **23**| **Security Headers** | Standard | Strict | Standard | Standard | **Strict CSP, `nosniff`, `DENY`, Rate Limits** |
| **24**| **Open Source** | Proprietary | Proprietary | Proprietary | Proprietary | **Full Open-Source Architecture (MIT)** |
| **25**| **Published Proof** | Marketing whitepapers| API Docs | Blog posts | Marketing claims| **149 Passing Tests, Code Gate, Artifacts** |

