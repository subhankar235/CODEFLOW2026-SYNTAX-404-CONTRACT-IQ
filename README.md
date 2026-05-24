<div align="center">

# ⚖️ LegalTech AI

**fine-tunned:AI-powered contract analysis at enterprise depth.**
## 🎥 Demo Video

## 🎥 Demo Video

[Watch the Full Demo](https://screenrec.com/share/NLyxgfrzIj)
Upload a contract. In minutes, know exactly what you're signing.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A.svg)](https://docs.celeryq.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL+pgvector-16-336791.svg)](https://www.postgresql.org/)
[![Polygon](https://img.shields.io/badge/Polygon-PoS-8247E5.svg)](https://polygon.technology/)

</div>

-

## Overview

Most people sign legal contracts without truly understanding them. Even those who read every word often lack the legal expertise to spot unfair clauses, power imbalances, or provisions that courts consistently refuse to enforce.

**LegalTech AI** solves this by combining a multi-stage AI analysis pipeline with:

- **RAG over a curated legal precedent corpus** for evidence-backed risk assessment
- **On-chain contract registration** on Polygon PoS for tamper-evident audit trails
- **Multilingual support** (EN, ES, FR, DE, PT, HI) via DeepL
- **Interactive counter-offer generation** with ready-to-send negotiation emails
- **AI Negotiation Simulator** to practice before the real conversation
- **Regional law adaptation** across India, US, EU, and more
- **Real-time streaming** of analysis results as each clause is processed

---

## Who It's For

| User | Use Case |
|---|---|
| **Individual contractors & freelancers** | Understand NDAs, employment agreements, and service contracts before signing |
| **Small businesses** | Review vendor agreements and SLAs without a dedicated legal team |
| **Legal teams** | Accelerate clause-level review with AI-assisted triage and precedent citations |
| **Compliance officers** | Audit high-volume contract ingestion with structured, auditable outputs |

---

## Features

### 🔍 18-Step Async Analysis Pipeline
Upload PDF or DOCX contracts via UploadThing. A Celery worker orchestrates an 18-step pipeline asynchronously, streaming results back in real-time via Server-Sent Events (SSE) over Redis pub/sub.

### 🧠 Two-Pass Clause Risk Classification
- **Pass 1 — Rule Engine:** 40+ compiled regex patterns triage every clause into `GREEN / YELLOW / RED`. Green clauses get instant `SAFE/LOW` results — no LLM cost.
- **Pass 2 — LLM Analysis:** Yellow and Red clauses are batched (≤20 per call) and sent to the primary LLM. Each clause receives: `risk_severity`, `safety_rating`, `risk_categories`, `explanation`, `recommendation`, `confidence_score`, and `problematic_language`.

### ⚠️ Consequence Generation
For every HIGH and MEDIUM risk clause, a dedicated pipeline produces:
- Worst-case financial exposure estimate
- Plain-English headline explaining the real-world risk
- Probability of the worst case occurring

### 📊 Power Asymmetry Analysis
Detects which party holds the structural advantage across the full contract. Outputs a 0–100 power score with a human-readable label (e.g., *"Strongly Employer-Favored"*).

### ⚖️ Legal Precedent Retrieval (RAG)
For every HIGH-risk clause: embeds the clause → queries pgvector for the top-3 most similar pre-indexed legal precedent summaries → synthesises an AI analysis. Outputs:
- `precedent_summary`
- `enforcement_likelihood` (one of 4 calibrated values)
- `confidence_score` (blended: retrieval similarity × LLM self-rating)
- 1–3 `cited_cases`

### 🤝 Counter-Offer Generator
On-demand, for any flagged clause: generates 3 distinct redline versions (aggressive / balanced / conservative) using RAG over a "favorable clause" corpus, plus a ready-to-send negotiation email.

### 📄 Summary & Pros/Cons Card
- Executive one-liner and overall risk score (0–100)
- Top 3 red flags and top 2 leverage points
- Recommendation: **Sign**, **Sign with Changes**, or **Do Not Sign**

### 💬 RAG Q&A Chat
After analysis, ask free-form questions about your contract. Clause text is embedded and stored in pgvector for semantic retrieval.

### 🌐 Multilingual Support
Auto-detects contract language. Translates non-English contracts (ES, FR, DE, PT, HI) to English for analysis via DeepL, then translates results back.

### ⛓️ Blockchain Registration (Polygon PoS)
Register contracts on-chain: `keccak256` hash + IPFS CID written to a custom `ContractRegistry` Solidity contract. Every audit trail event is anchored on-chain. Celery Beat polls pending transactions for confirmation.

### 📑 Shareable PDF Reports
Full-detail PDF reports generated with WeasyPrint + Jinja2. Shareable via a signed UUID URL — no authentication required.

### 🔐 Authentication & Security
Clerk JWT auth verified server-side on every protected route. Per-user data isolation enforced at the repository layer. Strict 403 on unauthorized resource access.

---

## Advanced Features

### 🔏 Immutable Blockchain Audit Trail

Every critical contract event is cryptographically anchored on-chain using Polygon PoS. Stored records include:

- Digital signatures
- Timestamped contract versions
- Edit history
- Audit events (upload, analysis, sharing, updates)

Each contract receives a tamper-evident `keccak256` hash, ensuring document integrity and verifiable authenticity.

**Why It Matters:**
- Prevents silent contract manipulation
- Creates forensic-grade verification history
- Provides immutable proof of document state
- Enables transparent compliance auditing

> Immutable audit trails are a powerful trust signal for enterprises, compliance teams, and legal review workflows.

---

### 🥊 AI Negotiation Simulator

Practice negotiations before speaking with the real party. The AI simulates the opposing side across common contract scenarios:

| Simulated Party | Common Scenarios |
|---|---|
| **Employers** | Non-competes, IP assignment, at-will termination |
| **Clients** | SLA penalties, scope creep, payment terms |
| **Landlords** | Rent escalation, security deposits, early exit |
| **Investors** | Equity dilution, vesting cliffs, liquidation preference |
| **Vendors** | Liability caps, exclusivity, auto-renewal |

**Example Workflow:**

1. AI detects a risky clause
2. User opens Negotiation Simulator
3. AI roleplays the opposing side
4. User practices responses in real time
5. AI provides negotiation coaching and counter-strategy suggestions

Users learn what to say, how to handle pushback, which clauses have room to move, where they hold leverage, and which demands are dangerous to accept. This transforms LegalTech AI from a passive analysis tool into an interactive legal negotiation assistant.

---

### 🌍 Regional Law Adaptation

Contracts are analyzed according to jurisdiction-specific legal frameworks rather than generic global standards.

**Supported Legal Contexts:**

| Jurisdiction | Coverage |
|---|---|
| 🇮🇳 India | Labor law, non-compete enforceability, IT Act |
| 🇺🇸 United States | Federal baseline + state-specific variations |
| 🇪🇺 European Union | GDPR, Working Time Directive, consumer protection |
| State-level (planned) | California, New York, Texas employment law |

**Example Jurisdiction-Aware Insights:**
- *"This non-compete clause may be unenforceable under Indian labor law."*
- *"Potential GDPR compliance concerns detected for EU data subjects."*
- *"This arbitration clause may conflict with California employment protections."*

**Capabilities:**
- Jurisdiction-aware clause analysis
- Regional enforceability checks
- Local compliance warnings
- Country-specific legal precedent retrieval
- State-specific labor and contract law adaptation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser (Next.js 16 + React 19)                                    │
│  Clerk Auth  ·  UploadThing  ·  Zustand  ·  Framer Motion / GSAP   │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  API Service  (FastAPI 0.115 / Uvicorn)  :8000                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ /upload  │  │ /scan    │  │ /report  │  │ /blockchain      │    │
│  │ /summary │  │ /chat    │  │ /counter │  │ /dashboard       │    │
│  │ /power   │  │/precedent│  │/translate│  │ /webhooks/clerk  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘    │
│  Clerk JWT Auth  ·  SQLAlchemy async  ·  Redis pub/sub SSE bridge   │
└────────────────┬──────────────────┬────────────────────────────────┘
                 │                  │ pub/sub
          async  │              ┌───▼──────────┐
          tasks  │              │  Redis / SSE  │
                 ▼              │  :6379        │
┌────────────────────────────┐  └───────────────┘
│  Celery Worker             │
│  18-step scan pipeline     │◄──── Celery Beat (scheduled tasks)
│  ┌──────────────────────┐  │       · confirm_blockchain_records (5m)
│  │ 1. ScanJob: queued   │  │       · blockchain_health_monitor  (10m)
│  │ 2. Download file     │  │       · cleanup_expired_reports    (1h)
│  │ 3. Parse PDF/DOCX    │  │
│  │ 4. Language detect   │  │
│  │ 5. Segment clauses   │  │
│  │ 6. Rule triage       │  │
│  │ 7. Type detection    │──┼──► AI Service :8001
│  │ 8. Risk classif.     │──┼──► AI Service :8001
│  │ 9. Consequence gen.  │──┼──► AI Service :8001
│  │10. Power asymmetry   │──┼──► AI Service :8001
│  │11. Precedent RAG     │──┼──► AI Service :8001
│  │12. Summary card      │──┼──► AI Service :8001
│  │13. Pros/cons         │  │
│  │14. Store in Postgres │──┼──► PostgreSQL :5432
│  │15. Embed for Q&A     │──┼──► pgvector
│  │16. Translate back    │──┼──► DeepL API
│  │17. ScanJob: complete │  │
│  │18. Publish to Redis  │──┼──► SSE → Browser
│  └──────────────────────┘  │
└────────────────────────────┘
         │
         ▼
┌───────────────────────────┐
│  AI Service (FastAPI)     │
│  :8001                    │
│  OpenRouter → Llama 3.3 70B (PRIMARY)
│            └→ Gemini 2.0 Flash (FAST)
│  sentence-transformers    │ all-MiniLM-L6-v2 (local, 384-dim)
│  pgvector similarity      │
└───────────────────────────┘
         │
         ▼
┌───────────────────────────┐
│  Blockchain Layer         │
│  Polygon PoS (Hardhat)    │
│  ContractRegistry.sol     │ keccak256 hash + IPFS CID
│  AuditTrail.sol           │ per-event on-chain anchoring
└───────────────────────────┘
```

### Request Flow: Upload → Real-Time Streaming

1. User uploads a PDF/DOCX via UploadThing. A signed URL is returned from the CDN.
2. Frontend calls `POST /api/v1/upload` with the file URL and metadata.
3. API creates `Contract` and `ScanJob` records, enqueues the Celery task, and returns `job_id` immediately — no blocking.
4. Frontend opens an `EventSource` to `GET /api/v1/scan/{jobId}/stream?token=<jwt>`.
5. FastAPI subscribes to the Redis channel `scan:{jobId}` and proxies events as SSE.
6. The Celery worker executes all 18 steps, publishing `progress`, `clause`, `complete`, and `error` events at each step.
7. The frontend renders clause cards in real time as events arrive.

---

## Tech Stack

### Frontend

| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router) + React 19 |
| Language | TypeScript 5 |
| Styling | Tailwind CSS 4 |
| UI Components | Radix UI + shadcn/ui |
| Animation | Framer Motion 12 + GSAP 3 + Three.js |
| Auth | Clerk (`@clerk/nextjs`) |
| File Upload | UploadThing 7 |
| State | Zustand 5 |
| PDF Viewer | react-pdf 10 |
| Icons | Lucide React |

### Backend API

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 + Uvicorn 0.32 |
| Language | Python 3.13 |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2 (async) |
| Migrations | Alembic 1.14 |
| Auth | Clerk JWT (python-jose) + Svix webhook verification |
| HTTP Client | httpx 0.28 |
| PDF Generation | WeasyPrint 62 + Jinja2 3.1 |
| Encryption | PyCryptodome 3.21 |

### AI & NLP

| Component | Technology |
|---|---|
| LLM Gateway | OpenRouter API |
| Primary Model | `meta-llama/llama-3.3-70b-instruct:free` |
| Fast Model | `google/gemini-2.0-flash-exp:free` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim, runs locally) |
| Document Parsing | PyMuPDF + python-docx + pdfminer.six |
| Language Detection | langdetect |
| Translation | DeepL API (free tier) |
| RAG Vector Search | pgvector (cosine distance) |
| NLP | spaCy 3 |

### Database & Infrastructure

| Component | Technology |
|---|---|
| Database | PostgreSQL 16 (Neon serverless) |
| Vector Index | pgvector 0.8 (384-dim, cosine ops) |
| Task Queue | Celery 5.4 |
| Message Broker | Upstash Redis (TLS, `rediss://`) |
| Task Scheduling | Celery Beat |
| File Storage | UploadThing CDN |
| Container | Docker + Docker Compose |
| Blockchain | Polygon PoS (Hardhat) + Web3.py 7 |

---

## AI Pipeline

### Rule Engine Triage (Pass 1)

`risk_mapper.py` applies 40+ compiled regex patterns to every clause before any LLM call:

| Signal | Classification | Action |
|---|---|---|
| No risk signals | `GREEN` | Immediate SAFE/LOW result. Zero LLM cost. |
| Moderate signals | `YELLOW` | Queued for LLM analysis |
| Critical signals (IP assignment, unlimited indemnity, non-compete, unilateral termination) | `RED` | Queued with high priority |

### LLM Analysis (Pass 2 — Batched)

Only YELLOW and RED clauses proceed to the LLM, batched at ≤20 per call. Results are validated by Pydantic v2. On failure, the pipeline retries once with a corrective prompt; on second failure it emits a safe fallback with `confidence_score = 0.0` and `requires_attorney_review = true`.

### RAG — Legal Precedent Retrieval

```
HIGH-risk clause
   │
   ├─► SentenceTransformer.encode()         (384-dim vector)
   ├─► pgvector cosine similarity search    (top-3, filtered by risk_category)
   ├─► LLM synthesis prompt                 (clause + 3 retrieved cases)
   └─► PrecedentMatch
           precedent_summary
           enforcement_likelihood  ∈ {Very Likely, Likely, Unlikely, Rarely Enforced}
           confidence_score        = avg(pgvector similarities) × LLM self-rating
           cited_cases             [1–3 objects with name, year, jurisdiction, outcome]
```

### RAG — Counter-Offer Generation

```
Flagged clause
   │
   ├─► embed clause → pgvector search       (embedding_type='favorable_clause')
   ├─► retrieve most similar favorable variant from corpus
   ├─► prompt PRIMARY_MODEL
   └─► CounterOfferResult
           aggressive   { clause, explanation }
           balanced     { clause, explanation }
           conservative { clause, explanation }
           negotiation_email
```

### Model Routing

| Pipeline Step | Model | Reason |
|---|---|---|
| Contract type detection | Gemini 2.0 Flash | Requires only first 1000 tokens; latency-sensitive |
| Risk classification | Llama 3.3 70B | Deep legal reasoning required |
| Consequence generation | Llama 3.3 70B | Precise financial language required |
| Power asymmetry | Llama 3.3 70B | Full clause context required |
| Precedent synthesis | Llama 3.3 70B | Legal accuracy is critical |
| Summary card | Gemini 2.0 Flash | Aggregation task; latency matters |
| Counter-offer | Llama 3.3 70B | Must produce legally coherent redlines |
| Negotiation simulation | Llama 3.3 70B | Roleplay requires strong instruction-following |
| Jurisdiction analysis | Llama 3.3 70B | Region-specific legal reasoning required |

### Retry & Fallback

- Exponential backoff on HTTP 429/5xx (respects `Retry-After` header)
- 1 retry with corrective prompt on JSON parse or Pydantic validation failure
- Safe Pydantic defaults returned on second failure — never crash
- Celery task-level retry: up to 3 attempts with exponential backoff (`60 × 2^attempt` seconds)
- Circuit breaker via `pybreaker` on the blockchain service

---

## Project Structure

```
Legal-Tech/
├── apps/
│   ├── web/                     # Next.js 16 frontend
│   │   └── src/
│   │       ├── app/
│   │       │   ├── (app)/       # Authenticated routes: dashboard, upload, scan, chat, report, history, settings
│   │       │   ├── (auth)/      # Clerk sign-in / sign-up pages
│   │       │   ├── api/         # Next.js API routes (UploadThing handler)
│   │       │   └── share/       # Public report sharing
│   │       ├── components/      # Shared UI components
│   │       ├── features/        # Feature-scoped modules (analysis, chat, counter-offer, dashboard, negotiation, …)
│   │       ├── hooks/           # Custom React hooks
│   │       ├── lib/             # Shared utilities and API client
│   │       ├── store/           # Zustand global state
│   │       └── types/           # TypeScript type definitions
│   │
│   └── worker/                  # Celery worker application
│       ├── celery_app.py
│       ├── pipeline/            # Pipeline orchestration steps (step_01 … step_04)
│       └── tasks/               # Celery task definitions
│
├── services/
│   ├── api/                     # FastAPI REST API
│   │   └── app/
│   │       ├── api/v1/endpoints/
│   │       ├── core/            # Pydantic Settings
│   │       ├── db/              # Session + base
│   │       ├── models/          # SQLAlchemy ORM models
│   │       ├── repositories/    # Data access layer (query-only)
│   │       ├── schemas/         # Pydantic request/response schemas
│   │       ├── services/        # Business logic
│   │       ├── workers/         # SSE streaming worker
│   │       └── migrations/      # Alembic scripts
│   │
│   └── ai/                      # Standalone AI microservice (FastAPI :8001)
│       └── app/
│           ├── api/routes/      # chat, translate, analyze, counter_offer, precedent, negotiation
│           ├── models/          # openrouter_client.py, model_config.py
│           ├── pipelines/       # clause_extraction, risk_classification, consequence_generation, …
│           ├── prompts/         # Prompt templates (*.txt)
│           ├── rules/           # regex_rules.py + risk_mapper.py
│           ├── jurisdiction/    # regional_analyzer.py + jurisdiction_rules/
│           ├── multilingual/    # DeepL translator + language detector
│           ├── parser/          # PDF/DOCX parsing
│           ├── rag/             # RAG utilities
│           └── utils/           # confidence_scorer.py, prompt_loader.py
│
├── blockchain/                  # Smart contracts (Hardhat)
│   ├── contracts/
│   │   ├── ContractRegistry.sol
│   │   └── AuditTrail.sol
│   ├── ignition/                # Hardhat Ignition deployment modules
│   ├── abis/                    # Compiled ABI JSON
│   └── scripts/                 # Deployment scripts
│
├── docs/
├── scripts/                     # DB seeding, deployment helpers
├── tests/
├── docker-compose.yml
└── .env.example
```

---

## Local Development

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.13+ |
| Node.js | 20+ |
| Docker + Docker Compose | Latest stable |

### 1. Clone the Repository

```bash
git clone https://github.com/<org>/Legal-Tech.git
cd Legal-Tech
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Clerk, OpenRouter, UploadThing, and database credentials
```

### 3. Start Infrastructure

```bash
docker compose up db redis -d
```

### 4. Backend API

```bash
cd services/api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python run.py
# → http://localhost:8000
```

### 5. AI Service

```bash
cd services/ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
# → http://localhost:8001
```

### 6. Celery Worker

```bash
cd apps/worker
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
celery -A celery_app worker --loglevel=info

# Optional: start the Beat scheduler for periodic tasks
celery -A celery_app beat --loglevel=info
```

### 7. Frontend

```bash
cd apps/web
npm install
npm run dev
# → http://localhost:3000
```

### 8. Seed Legal Precedents (optional)

```bash
cd services/ai
python scripts/seed_precedents.py
```

### Run Everything with Docker Compose

```bash
docker compose up --build
```

| Service | Port |
|---|---|
| Next.js (run separately) | 3000 |
| FastAPI (API) | 8000 |
| FastAPI (AI) | 8001 |
| PostgreSQL | 5433 |
| Redis | 6379 |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values.

```bash
# ── Frontend ──────────────────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
UPLOADTHING_SECRET=sk_live_...
UPLOADTHING_APP_ID=your-app-id

# ── Backend API ───────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:password@host/legaltech
REDIS_URL=rediss://default:password@host.upstash.io:6379?ssl_cert_reqs=none
CLERK_WEBHOOK_SECRET=whsec_...
CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json

# ── AI Service ────────────────────────────────────────────────────────────
OPENROUTER_API_KEY=sk-or-...
PRIMARY_MODEL=meta-llama/llama-3.3-70b-instruct:free
FAST_MODEL=google/gemini-2.0-flash-exp:free
DEEPL_API_KEY=...
EMBEDDING_MODEL=all-MiniLM-L6-v2
DEFAULT_JURISDICTION=IN         # IN | US | EU

# ── Blockchain (optional) ─────────────────────────────────────────────────
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/...
POLYGON_PRIVATE_KEY=0x...
CONTRACT_REGISTRY_ADDRESS=0x...

# ── Shared ────────────────────────────────────────────────────────────────
AI_SERVICE_URL=http://localhost:8001
ENVIRONMENT=development
```

---

## API Reference

All protected endpoints require `Authorization: Bearer <clerk_jwt>`.

### Contracts & Upload

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/upload` | Create contract + enqueue scan job |
| `GET` | `/api/v1/contracts` | List user's contracts |
| `GET` | `/api/v1/contracts/{id}` | Get contract details |
| `DELETE` | `/api/v1/contracts/{id}` | Delete contract and all results |

### Analysis & Streaming

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/scan` | Trigger analysis on existing contract |
| `GET` | `/api/v1/scan/{jobId}/status` | Poll scan job status |
| `GET` | `/api/v1/scan/{jobId}/stream?token=` | SSE stream of clause results |
| `GET` | `/api/v1/scan/{jobId}/clauses` | Fetch all clause results |

### AI Features

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/counter-offer` | Generate 3 counter-offer versions for a clause |
| `GET` | `/api/v1/summary/{contractId}` | Get summary card |
| `GET` | `/api/v1/power/{contractId}` | Get power asymmetry analysis |
| `GET` | `/api/v1/precedent/{clauseId}` | Get legal precedent match |
| `POST` | `/api/v1/chat` | Q&A chat about a contract |
| `POST` | `/api/v1/translate` | Translate text (DeepL proxy) |
| `POST` | `/api/v1/negotiate` | Start / continue a negotiation simulation session |
| `GET` | `/api/v1/jurisdiction/{contractId}` | Get jurisdiction-specific enforceability analysis |

### Reports & Dashboard

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/report/{contractId}` | Generate PDF report |
| `GET` | `/api/v1/report/share/{uuid}` | Public report access (no auth) |
| `GET` | `/api/v1/dashboard` | Aggregated user stats |

### Blockchain

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/blockchain/register/{contractId}` | Register contract on Polygon |
| `GET` | `/api/v1/blockchain/status/{contractId}` | On-chain registration status |
| `GET` | `/api/v1/blockchain/health` | RPC connectivity health |

---

## Database Schema

All tables use UUID primary keys. All queries are scoped by `user_id`.

| Table | Purpose |
|---|---|
| `users` | Synced from Clerk via webhook |
| `contracts` | Contract metadata: `file_ref`, `contract_type`, `detected_language`, `party_roles`, `jurisdiction` |
| `scan_jobs` | Pipeline status: `{queued, processing, complete, failed}`, `progress_pct`, `error_message` |
| `clauses` | Per-clause analysis: `text`, `risk_level`, `risk_category`, `plain_english`, `worst_case_scenario`, `confidence`, `negotiable` |
| `analysis_results` | Contract-level aggregates: `power_score`, `power_label`, `overall_risk_score`, `should_sign`, `leverage_points`, `top_concerns` |
| `jurisdiction_results` | Regional enforceability: `jurisdiction`, `enforceability_flags`, `compliance_warnings` (JSONB) |
| `embeddings` | pgvector table (384-dim): `embedding_type ∈ {contract_qa, favorable_clause, precedent}` |
| `precedent_matches` | RAG output per HIGH-risk clause: `precedent_summary`, `enforcement_likelihood`, `cited_cases` (JSONB) |
| `counter_offers` | Three-version redlines: `aggressive_version`, `balanced_version`, `conservative_version`, `negotiation_email` |
| `negotiation_sessions` | Simulator state: `simulated_party`, `turn_history` (JSONB), `coaching_notes` |
| `reports` | PDF metadata: `share_uuid`, `expires_at`, `report_url` |
| `contract_blockchain_records` | On-chain registration: `contract_hash`, `polygon_tx_hash`, `block_number`, `registration_status`, `ipfs_cid` |
| `audit_trail_events` | Per-event audit log anchored on-chain: `event_type`, `polygon_tx_hash`, `on_chain_status` |

**pgvector index:**

```sql
CREATE INDEX embeddings_embedding_idx
ON embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## Security

| Concern | Implementation |
|---|---|
| **Authentication** | Clerk JWT verified on every protected route via `get_current_user_id` dependency. JWKS URL verified, not shared secret. |
| **Webhook Verification** | Clerk webhooks verified via Svix before processing. Invalid signatures → 400. |
| **Resource Isolation** | All DB queries filter by `user_id`. Unauthorized access returns 403 (404 on contracts to avoid existence leakage). |
| **File Security** | Files stored by UploadThing CDN; file bytes are never stored in the database. |
| **Secrets Handling** | All secrets loaded via Pydantic `BaseSettings`. Never logged or hardcoded. |
| **SSE Auth** | `EventSource` cannot send `Authorization` headers; the SSE endpoint accepts `?token=<jwt>` and validates it before subscribing. |
| **Rate Limiting** | Per-user rate limiting via Upstash Redis. |
| **Encryption** | PyCryptodome available for client-side encrypted document support. Decryption key never stored. |
| **On-Chain Integrity** | Contract hashes on Polygon are immutable — tamper-evident proof of document state at registration time. |

---

## Blockchain Layer

Two Solidity contracts are deployed on Polygon PoS:

**`ContractRegistry.sol`**
- Stores `keccak256(pdfBytes)` + `keccak256(metadata)` + IPFS CID for each contract
- Append-only — records cannot be modified or deleted
- Emits `ContractRegistered` event (indexed by `contractHash` and `uploader`)

**`AuditTrail.sol`**
- Records individual audit events (upload, view, analysis, share) on-chain
- Each event is linked to a contract hash and actor address

**Celery Beat maintenance:**
- Every 5 min: `confirm_blockchain_records` — polls Polygon for transaction receipts; updates `registration_status = 'confirmed'` and stores `block_number`
- Every 10 min: `blockchain_health_monitor` — checks RPC connectivity and publishes health status to Redis (90s TTL)

---

## Scalability Notes

**Async-first:** FastAPI and SQLAlchemy are fully async. Multiple Celery worker replicas can process different contracts in parallel.

**Queue-based decoupling:** `POST /upload` returns in <200ms. The 18-step pipeline runs entirely in the background.

**Vector search performance:** `all-MiniLM-L6-v2` produces compact 384-dim vectors. IVFFlat index keeps search latency <50ms even at scale.

**LLM cost optimization:** Rule engine eliminates LLM calls for GREEN clauses (typically 40–60% of all clauses). Batching reduces LLM round trips by ~20×. All OpenRouter models used are free-tier — zero per-token cost during development.

**Caching:** Blockchain health status cached in Redis with a 90-second TTL. Celery result backend is Redis for persistent task state.

---

## Production Deployment

```
Vercel (Next.js frontend)
    │
    ▼
Railway / Render (FastAPI API)  ←── Neon PostgreSQL (pgvector)
                                ←── Upstash Redis (TLS)
    │
    ▼
Railway / Render (FastAPI AI)
Railway / Render (Celery Worker)
Railway / Render (Celery Beat)
```

**Production checklist:**
- Set `ENVIRONMENT=production` on all services
- Use `rediss://` (TLS) for Redis URL (Upstash requires it)
- Use `postgresql+asyncpg://` for `DATABASE_URL`
- Deploy contracts to Polygon Mainnet or Amoy Testnet via Hardhat Ignition
- Configure Clerk's production instance and update all `CLERK_*` variables

**Run migrations in production:**

```bash
cd services/api
alembic upgrade head
```

---

## Roadmap

- [ ] Parallel clause processing with `asyncio.gather` for concurrent precedent retrieval
- [ ] Migrate pgvector index from IVFFlat to HNSW for better recall at high vector counts
- [ ] Token-level streaming for consequence and counter-offer generation
- [ ] Semantic clause comparison across a user's full contract history
- [ ] Model fallback chain (PRIMARY → FAST → tertiary) on quota exhaustion
- [ ] Fine-tune `all-MiniLM-L6-v2` on legal domain text for improved retrieval
- [ ] IPFS pinning via Pinata or web3.storage before on-chain registration
- [ ] Multi-party analysis (contracts with more than two parties)
- [ ] Attorney review workflow for clauses with `confidence < 0.7`
- [ ] CSV/JSON export of clause-level audit trail events
- [ ] State-specific legal rules for California, New York, and Texas
- [ ] Negotiation Simulator scoring and session replay
- [ ] Voice interface for negotiation practice sessions

---

## Contributing

### Getting Started

```bash
# 1. Fork the repository and clone your fork
git clone https://github.com/<your-username>/Legal-Tech.git

# 2. Create a feature branch
git checkout -b feat/your-feature

# 3. Complete the local development setup, make your changes, run tests
pytest tests/          # backend
npm run lint           # frontend
```

### Code Standards

**Python:** Python 3.13, fully typed, async functions use `async def`, structured logging (`key=value` format), all config via `settings` — never `os.environ` directly, repository layer is query-only with zero business logic.

**TypeScript:** Strict mode, single-responsibility components co-located with their feature module, state via Zustand, Radix UI primitives for accessible components.

### Commit Convention

```
feat(ai): add multilingual support for Hindi contracts
fix(worker): handle empty clause list in power analysis
docs(readme): update environment variable table
refactor(api): extract clause scoring into service layer
```

### Branch Naming

```
feat/<scope>/<description>
fix/<scope>/<description>
docs/<description>
refactor/<scope>/<description>
chore/<description>
```

---

## License

[MIT License](./LICENCE) — Copyright (c) 2026 subhankar nath
<div align="center">

Built with ⚖️ and 🤖 to make legal contracts accessible to everyone.

</div>
