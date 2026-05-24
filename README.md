# 🏛️ LegalTech Contract Scanner

> **"A legal guardian angel for freelancers and small business owners."**  
> Scan any contract, understand every risk, negotiate with confidence — no lawyer required.

---

## 🚀 Features

### Core Scanning
- **Multi-format support** — Upload PDF, DOCX, TXT files; handles password-protected and scanned PDFs
- **Clause extraction** — Intelligent segmentation using NLP with position tracking
- **9 risk categories** — IP ownership, liability, confidentiality, payment, termination, jurisdiction, indemnification, non-compete, arbitration
- **Color-coded risk levels** — 🟢 Green (safe), 🟡 Yellow (caution), 🔴 Red (danger)
- **Consequence explanation** — Plain-English explanations of what each risky clause means for you

### AI-Powered Analysis
- **Contract type detection** — Automatically identifies SOW, NDA, MSA, employment, lease, SaaS agreements
- **Power asymmetry scoring** — Quantifies contract imbalance with leverage points and negotiation insights
- **Legal precedent retrieval** — Matches clauses to 500+ court cases and favorable precedents
- **Counter-offer generation** — Suggests fair alternative language for red-flagged clauses

### Smart Chat & Search
- **RAG-powered Q&A** — Ask questions about your contract in plain English; get answers sourced from the document
- **Vector embeddings** — Semantic search across your contract history with pgvector
- **Streaming responses** — Real-time SSE streaming for all analysis results

### Multilingual & Accessibility
- **6 languages** — Works with English, Spanish, French, German, Portuguese, Hindi contracts
- **Auto-detection** — Detects source language and translates results back
- **Legal glossary** — Domain-specific terminology preserved across translations
- **PDF report export** — Beautiful shareable reports in multiple languages

### Developer Experience
- **REST API** — FastAPI backend with JWT authentication (Clerk)
- **Async workers** — Celery + Redis for background processing
- **Docker-ready** — One-command deployment with docker-compose
- **Streaming endpoints** — Server-Sent Events for real-time progress

---

## 📈 Target Users

- **Freelancers** — Sign client SOWs and project contracts with confidence
- **Small business owners** — Review vendor, lease, or SaaS agreements
- **Startups** — Navigate employment and partnership contracts
- **Legal professionals** — Use as a first-pass review tool

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                   │
└────────────┬──────────────────────────────────┬────────────┘
             │ JWT Auth (Clerk)                  │ File Upload (Uploadthing)
             ▼                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Contracts│ │  Chat    │ │ Reports  │ │   Webhooks   │  │
│  └─────┬────┘ └─────┬────┘ └────┬────┘ └──────┬───────┘  │
└────────┼─────────────┼───────────┼─────────────┼──────────┘
         │             │           │             │
    PostgreSQL      Redis       Celery         AI Service
    + pgvector     (Queue)    Workers         (port 8001)
                                              ┌───────────┐
                                              │  Pipeline │ ──► OpenRouter
                                              │  (LLM)    │     (Free Models)
                                              └───────────┘
```

---

## 🛠️ Tech Stack

|
 Layer 
|
 Technology 
|
|
-------
|
------------
|
|
**
API
**
|
 FastAPI, SQLAlchemy (async), Pydantic v2 
|
|
**
AI
**
|
 spaCy, LangChain, pgvector, sentence-transformers 
|
|
**
LLM
**
|
 OpenRouter (LLaMA 3.3, Gemini 2.0 Flash) 
|
|
**
Workers
**
|
 Celery 5, Redis 
|
|
**
Database
**
|
 PostgreSQL 16, pgvector 
|
|
**
Auth
**
|
 Clerk (JWT verification via JWKS) 
|
|
**
Translation
**
|
 DeepL API 
|
|
**
Reports
**
|
 WeasyPrint (HTML→PDF) 
|
|
**
Container
**
|
 Docker, Docker Compose 
|

---

## 📁 Project Structure

```
LegalTech/
├── services/
│   ├── api/               # FastAPI backend (port 8000)
│   │   ├── app/
│   │   │   ├── api/v1/    # REST endpoints
│   │   │   ├── core/      # Security, config, rate limiting
│   │   │   ├── db/        # Session, base, models
│   │   │   ├── models/    # ORM models (9 tables)
│   │   │   ├── schemas/   # Pydantic schemas
│   │   │   ├── services/  # Business logic
│   │   │   └── utils/     # File handling, PDF generation
│   │   ├── migrations/    # Alembic DB migrations
│   │   └── templates/     # Report HTML templates
│   │
│   └── ai/                # AI service (port 8001)
│       ├── app/
│       │   ├── parser/    # PDF, DOCX, fallback parsers
│       │   ├── pipelines/ # Type detection, risk, power, chat
│       │   ├── prompts/  # LLM prompt templates
│       │   ├── rules/     # Regex risk rules
│       │   ├── rag/       # Embedding, vector store
│       │   ├── multilingual/ # Translation, language detection
│       │   ├── data/      # Precedents, favorable clauses
│       │   └── scripts/   # Seeding scripts
│       └── models/        # OpenRouter client
│
├── apps/
│   └── worker/            # Celery worker
│       ├── tasks/         # Async tasks (scan, embed, translate, report)
│       └── pipeline/      # Step-by-step contract processing
│
├── agents/                # Agent prompts & context
├── docs/                  # PRD, tech stack, setup steps
├── scripts/               # Utility scripts
└── tests/                 # Test suite
```

---

## 🔌 API Endpoints

### Public
|
 Method 
|
 Endpoint 
|
 Description 
|
|
--------
|
-----------
|
-------------
|
|
 GET 
|
`/health`
|
 Health check 
|
|
 POST 
|
`/api/v1/webhooks/clerk`
|
 Clerk webhook handler 
|

### Protected (JWT Required)
|
 Method 
|
 Endpoint 
|
 Description 
|
|
--------
|
-----------
|
-------------
|
|
 POST 
|
`/api/v1/upload`
|
 Upload contract & start scan 
|
|
 GET 
|
`/api/v1/scan/{jobId}`
|
 Get scan status 
|
|
 GET 
|
`/api/v1/scan/{jobId}/stream`
|
 SSE progress stream 
|
|
 GET 
|
`/api/v1/contracts`
|
 List user's contracts 
|
|
 GET 
|
`/api/v1/contracts/{id}`
|
 Get contract details 
|
|
 DELETE 
|
`/api/v1/contracts/{id}`
|
 Delete contract 
|
|
 GET 
|
`/api/v1/summary/{contractId}`
|
 Get summary card 
|
|
 GET 
|
`/api/v1/power/{contractId}`
|
 Get power analysis 
|
|
 GET 
|
`/api/v1/precedent/{clauseId}`
|
 Get legal precedent 
|
|
 POST 
|
`/api/v1/counter-offer/{clauseId}`
|
 Generate counter-offer 
|
|
 POST 
|
`/api/v1/chat/{contractId}`
|
 RAG Q&A chat (streaming) 
|
|
 POST 
|
`/api/v1/translate/{contractId}`
|
 Translate results 
|
|
 POST 
|
`/api/v1/report/generate/{contractId}`
|
 Generate PDF report 
|
|
 GET 
|
`/api/v1/report/{reportId}`
|
 Get report 
|
|
 GET 
|
`/api/v1/report/share/{shareUuid}`
|
 Public share link 
|

---

## 💡 Vision

> Track power asymmetry across every contract you've ever signed.  
> *"Your last 5 contracts averaged -42. You're consistently undervalued."*  
> That's not a hackathon project — that's a product.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16 + pgvector
- Redis 7
- Docker (optional)

### Setup

```bash
# 1. Clone & enter directory
cd LegalTech

# 2. Copy environment template
cp .env.example .env
# Edit .env with your API keys

# 3. Start database & redis (Docker)
docker-compose up -d db redis

# 4. Run migrations
cd services/api
alembic upgrade head

# 5. Start services (3 terminals)
# Terminal 1: API
cd services/api && uvicorn app.main:app --reload --port 8000

# Terminal 2: AI Service
cd services/ai && uvicorn app.main:app --reload --port 8001

# Terminal 3: Celery Worker
cd apps/worker && celery -A celery_app worker --loglevel=info
```

Or use Docker Compose for everything:
```bash
docker-compose up --build
```

---

## ⚙️ Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname

# Redis
REDIS_URL=rediss://default:pass@host:6379

# Auth (Clerk)
CLERK_JWKS_URL=https://your-org.clerk.com/.well-known/jwks.json

# AI Models (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-...
PRIMARY_MODEL=meta-llama/llama-3.3-70b-instruct:free
FAST_MODEL=google/gemini-2.0-flash-exp:free

# Translation (DeepL)
DEEPL_API_KEY=your_key_here

# Shared
AI_SERVICE_URL=http://localhost:8001
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_risk_classification.py -v

# Verify end-to-end
./test-analyze.ps1
```

---

## 📊 Database Schema (9 Tables)

|
 Table 
|
 Purpose 
|
|
-------
|
---------
|
|
`users`
|
 Clerk-authenticated users 
|
|
`contracts`
|
 Uploaded contracts with metadata 
|
|
`clauses`
|
 Extracted clauses with risk scores 
|
|
`scan_jobs`
|
 Async processing jobs 
|
|
`analysis_results`
|
 Risk classification results 
|
|
`counter_offers`
|
 AI-generated counter proposals 
|
|
`precedent_matches`
|
 Court case references 
|
|
`reports`
|
 Generated PDF reports 
|
|
`embeddings`
|
 Vector embeddings for RAG 
|

---

## 🔒 Security Features

- **JWT verification** via Clerk JWKS
- **Ownership checks** on all contract endpoints
- **Rate limiting** on upload endpoints
- **Webhook signature verification** (Clerk)
- **AES-256-GCM** decryption for sensitive files

---

## 🌍 Multilingual Support

|
 Language 
|
 Code 
|
 Status 
|
|
----------
|
------
|
--------
|
|
 English 
|
`en`
|
 ✅ Primary 
|
|
 Spanish 
|
`es`
|
 ✅ 
|
|
 French 
|
`fr`
|
 ✅ 
|
|
 German 
|
`de`
|
 ✅ 
|
|
 Portuguese 
|
`pt`
|
 ✅ 
|
|
 Hindi 
|
`hi`
|
 ✅ 
|

---

## 📝 License

MIT License - see [LICENCE](LICENCE)

---

# ⚖️ LegalTech AI — Contract Scanner & Intelligence Platform
> **AI-powered contract analysis at enterprise depth. Upload a contract. In minutes, know exactly what you're signing.**
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENCE)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A.svg)](https://docs.celeryq.dev)
[![PostgreSQL + pgvector](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Polygon PoS](https://img.shields.io/badge/Blockchain-Polygon%20PoS-8247E5.svg)](https://polygon.technology)
---
## Overview
Most people sign legal contracts without truly understanding them. Even those who read every word lack the legal expertise to identify unfair clauses, power imbalances, or clauses that courts consistently refuse to enforce.
**LegalTech AI** solves this by combining a multi-stage AI analysis pipeline with Retrieval-Augmented Generation (RAG) over a curated legal precedent corpus, on-chain contract registration on Polygon PoS, multilingual support, and an interactive counter-offer generator — all delivered through a real-time streaming interface.
### Who It's For
|
 User 
|
 Use Case 
|
|
------
|
----------
|
|
**
Individual contractors & freelancers
**
|
 Understand NDAs, employment agreements, and service contracts before signing 
|
|
**
Small businesses
**
|
 Review vendor agreements and SLAs without a dedicated legal team 
|
|
**
Legal teams
**
|
 Accelerate clause-level review with AI-assisted triage and precedent citations 
|
|
**
Compliance officers
**
|
 Audit high-volume contract ingestion with structured, auditable outputs 
|
---
## Features
### 🔍 Contract Analysis Pipeline (18-Step Async Workflow)
- Upload PDF or DOCX contracts via UploadThing
- A Celery worker executes a fully orchestrated 18-step pipeline asynchronously
- Results stream back to the UI in real-time via **Server-Sent Events (SSE)** over a Redis pub/sub channel
### 🧠 AI-Powered Clause Risk Classification
- **Two-pass triage**: a rule engine (40+ regex patterns) pre-screens all clauses into GREEN / YELLOW / RED
- **GREEN clauses** are assigned SAFE/LOW results instantly — no LLM call
- **YELLOW + RED clauses** are batched (≤20 per call) and sent to the primary LLM for deep analysis
- Each clause receives: `risk_severity`, `safety_rating`, `risk_categories`, `explanation`, `recommendation`, `confidence_score`, and `problematic_language`
- Retry logic with fallback defaults on LLM or parse failures
### ⚠️ Consequence Generation
- For every HIGH and MEDIUM risk clause, a dedicated pipeline generates:
  - **Worst-case financial exposure** estimate
  - **Plain-English headline** explaining the real-world risk
  - **Probability** of the worst case occurring
### 📊 Power Asymmetry Analysis
- Detects which party holds the structural advantage across the full contract
- Outputs a 0–100 power score and a human-readable label (e.g., "Strongly Employer-Favored")
### ⚖️ Legal Precedent Retrieval (RAG)
- For every HIGH-risk clause: embeds the clause → queries **pgvector** for the top-3 most similar pre-indexed legal precedent summaries → synthesises an AI analysis
- Outputs: `precedent_summary`, `enforcement_likelihood` (one of 4 calibrated values), `confidence_score` (blended: retrieval similarity × LLM self-rating), and 1–3 `cited_cases`
- Only HIGH-risk clauses undergo this expensive pipeline step
### 🤝 Counter-Offer Generator
- On-demand feature: for any flagged clause, generates **3 distinct redline versions** (aggressive / balanced / conservative) using RAG over a "favorable clause" corpus
- Also drafts a ready-to-send **negotiation email** for the opposing party
### 📄 Summary & Pros/Cons Card
- Executive one-liner, overall risk score (0–100), negotiating power assessment
- Top 3 red flags and top 2 leverage points
- Recommendation: "Sign", "Sign with Changes", or "Do Not Sign"
### 💬 RAG Q&A Chat
- After analysis, users can ask free-form questions about their contract
- Contract clause text is embedded and stored in pgvector for semantic Q&A retrieval
### 🌐 Multilingual Support
- Auto-detects contract language via `langdetect`
- Translates non-English contracts (ES, FR, DE, PT, HI) to English for analysis using DeepL API
- Translates results back to the user's language after analysis
### ⛓️ Blockchain Registration (Polygon PoS)
- Contracts can be registered on-chain: their **keccak256 hash + IPFS CID** are written to a custom `ContractRegistry` Solidity contract on Polygon PoS
- Every audit trail event (upload, analysis, view, share) is anchored on-chain
- Celery Beat periodically polls pending transactions for confirmation
- On-chain status and block number are stored and surfaced through the API
### 📑 PDF Report Generation
- Generates a full-detail PDF report using **WeasyPrint + Jinja2** templates
- Shareable via a signed UUID URL that does not require authentication
### 🔐 Authentication & Security
- Authentication via **Clerk** (JWT-based, verified server-side on every protected route)
- Webhook signature verification via **Svix** on the Clerk sync endpoint
- Per-user data isolation enforced at the repository layer (every query scoped by `user_id`)
- Strict 403 (not 404) on unauthorized resource access
---
## Architecture
The platform is composed of four independently deployable services plus a blockchain layer:
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
│  /api/v1/analyze          │
│  /api/v1/chat             │
│  /api/v1/counter-offer    │
│  /api/v1/precedent        │
│  /translate               │
│                           │
│  OpenRouter ──► Llama 3.3 70B (PRIMARY)
│           └──► Gemini 2.0 Flash (FAST)
│                           │
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
### Request Flow: Contract Upload → Real-Time Streaming Analysis
1. User uploads a PDF/DOCX via UploadThing (Next.js). File is stored by UploadThing's CDN and a signed URL is returned.
2. Frontend calls `POST /api/v1/upload` with the file URL and metadata.
3. API creates a `Contract` record and a `ScanJob` record (status: `queued`), then enqueues the `process_contract` Celery task. Returns `job_id` immediately — no blocking.
4. Frontend opens an EventSource to `GET /api/v1/scan/{jobId}/stream?token=<jwt>`.
5. The API subscribes to the Redis channel `scan:{jobId}` and proxies events as SSE.
6. The Celery worker executes all 18 pipeline steps, publishing progress, clause results, and the final `complete` event to Redis at each step.
7. The frontend receives each event in real time, rendering clause cards as they arrive.
---
## Tech Stack
### Frontend
|
 Layer 
|
 Technology 
|
|
---
|
---
|
|
 Framework 
|
 Next.js 16 (App Router) + React 19 
|
|
 Language 
|
 TypeScript 5 
|
|
 Styling 
|
 Tailwind CSS 4 
|
|
 UI Components 
|
 Radix UI primitives + shadcn/ui 
|
|
 Animation 
|
 Framer Motion 12 + GSAP 3 + Three.js 
|
|
 Auth 
|
 Clerk (
`@clerk/nextjs`
) 
|
|
 File Upload 
|
 UploadThing 7 
|
|
 State 
|
 Zustand 5 
|
|
 PDF Viewer 
|
 react-pdf 10 
|
|
 Icons 
|
 Lucide React 
|
### Backend API
|
 Layer 
|
 Technology 
|
|
---
|
---
|
|
 Framework 
|
 FastAPI 0.115 + Uvicorn 0.32 
|
|
 Language 
|
 Python 3.13 
|
|
 Validation 
|
 Pydantic v2 
|
|
 ORM 
|
 SQLAlchemy 2 (async) 
|
|
 Migrations 
|
 Alembic 1.14 
|
|
 Auth 
|
 Clerk JWT (python-jose) + Svix webhook verification 
|
|
 HTTP Client 
|
 httpx 0.28 
|
|
 PDF Generation 
|
 WeasyPrint 62 + Jinja2 3.1 
|
|
 Encryption 
|
 PyCryptodome 3.21 
|
### AI & NLP Stack
|
 Component 
|
 Technology 
|
|
---
|
---
|
|
 LLM Gateway 
|
 OpenRouter API 
|
|
 Primary Model 
|
`meta-llama/llama-3.3-70b-instruct:free`
|
|
 Fast Model 
|
`google/gemini-2.0-flash-exp:free`
|
|
 Embeddings 
|
`sentence-transformers/all-MiniLM-L6-v2`
 (384-dim, runs locally) 
|
|
 Document Parsing 
|
 PyMuPDF + python-docx + pdfminer.six 
|
|
 Language Detection 
|
 langdetect 
|
|
 Translation 
|
 DeepL API (free tier) 
|
|
 RAG Vector Search 
|
 pgvector (cosine distance) 
|
|
 NLP 
|
 spaCy 3 
|
### Database & Infrastructure
|
 Component 
|
 Technology 
|
|
---
|
---
|
|
 Database 
|
 PostgreSQL 16 (Neon serverless) 
|
|
 Vector Index 
|
 pgvector 0.8 (384-dim, cosine ops) 
|
|
 Task Queue 
|
 Celery 5.4 
|
|
 Message Broker 
|
 Upstash Redis (TLS, 
`rediss://`
) 
|
|
 Task Scheduling 
|
 Celery Beat 
|
|
 File Storage 
|
 UploadThing CDN 
|
|
 Container 
|
 Docker + Docker Compose 
|
|
 Blockchain 
|
 Polygon PoS (Hardhat) + Web3.py 7 
|
---
## AI Pipeline
### Rule Engine Triage (Pass 1)
The `risk_mapper.py` rule engine applies 40+ compiled regex patterns to every clause before any LLM call. Each clause is classified as:
- **GREEN** — no risk signals → immediate SAFE / LOW result, zero LLM cost
- **YELLOW** — moderate signals → queued for LLM analysis
- **RED** — critical signals (IP assignment, unlimited indemnity, non-compete, unilateral termination) → queued with high priority
### LLM Analysis (Pass 2 — Batched)
Only YELLOW and RED clauses proceed to the LLM. They are batched (≤20 per call) and sent to the primary model with a structured JSON output requirement. Each result is validated by Pydantic v2. On failure, the pipeline retries once with a corrective prompt; on second failure it emits a safe fallback with `confidence_score = 0.0` and flags `requires_attorney_review = true`.
### Consequence Generation
For HIGH and MEDIUM clauses, a separate LLM call generates a consequence model with `headline`, `scenario`, `financial_exposure`, and `probability`. This runs concurrently after risk classification completes.
### Power Asymmetry Analysis
The full clause list (with risk levels) is sent to the LLM, which identifies structural imbalances and outputs a 0–100 integer power score. A score above 70 is flagged as "Strongly [Party]-Favored."
### RAG — Legal Precedent Retrieval
```
HIGH-risk clause
   │
   ├─► SentenceTransformer.encode()         (384-dim vector)
   │
   ├─► pgvector cosine similarity search    (top-3, filtered by risk_category)
   │       embeddings WHERE embedding_type = 'precedent'
   │
   ├─► LLM synthesis prompt                 (clause + 3 retrieved cases)
   │       "Has this clause been tested in court? What happened?"
   │
   └─► PrecedentMatch (Pydantic)
           precedent_summary
           enforcement_likelihood  ∈ {Very Likely, Likely, Unlikely, Rarely} Enforced
           confidence_score        = avg(pgvector similarities) × LLM self-rating
           cited_cases             [1–3 CitedCase objects with name, year, jurisdiction, outcome]
```
### RAG — Counter-Offer Generation
```
Flagged clause (any risk level)
   │
   ├─► embed clause → pgvector search       (embedding_type='favorable_clause')
   │
   ├─► retrieve most similar favorable      (contract language that protects the user)
   │   variant from corpus
   │
   ├─► prompt PRIMARY_MODEL                 (original + favorable reference + context)
   │
   └─► CounterOfferResult (Pydantic)
           aggressive   { clause, explanation }
           balanced     { clause, explanation }
           conservative { clause, explanation }
           negotiation_email
```
### Streaming via Redis Pub/Sub → SSE
The Celery worker publishes structured JSON events to a per-job Redis channel (`scan:{jobId}`). The FastAPI streaming endpoint subscribes and proxies them as SSE events to the browser's `EventSource`. Event types: `progress`, `clause`, `complete`, `error`. Heartbeats are sent every 15 seconds to keep the connection alive.
### Model Routing
|
 Pipeline Step 
|
 Model Used 
|
 Why 
|
|
---
|
---
|
---
|
|
 Contract type detection 
|
 Gemini 2.0 Flash (FAST) 
|
 Requires only first 1000 tokens, latency-sensitive 
|
|
 Risk classification 
|
 Llama 3.3 70B (PRIMARY) 
|
 Requires deep legal reasoning 
|
|
 Consequence generation 
|
 Llama 3.3 70B (PRIMARY) 
|
 Requires precise financial language 
|
|
 Power asymmetry 
|
 Llama 3.3 70B (PRIMARY) 
|
 Full clause context required 
|
|
 Precedent synthesis 
|
 Llama 3.3 70B (PRIMARY) 
|
 Legal accuracy is critical 
|
|
 Summary card 
|
 Gemini 2.0 Flash (FAST) 
|
 Aggregation task, latency matters 
|
|
 Counter-offer 
|
 Llama 3.3 70B (PRIMARY) 
|
 Must produce legally coherent redlines 
|
### Retry & Fallback Logic
All LLM calls implement:
- Exponential backoff on HTTP 429 / 5xx (respects `Retry-After` header)
- 1 retry with corrective prompt on JSON parse or Pydantic validation failure
- Safe Pydantic defaults returned on second failure (never crash)
- Celery task-level retry: up to 3 attempts with exponential backoff (`60 × 2^attempt` seconds)
- Circuit breaker via `pybreaker` on the blockchain service
---
## Folder Structure
```
Legal-Tech/
├── apps/
│   ├── web/                     # Next.js 16 frontend
│   │   └── src/
│   │       ├── app/
│   │       │   ├── (app)/       # Authenticated app routes
│   │       │   │   ├── dashboard/
│   │       │   │   ├── upload/
│   │       │   │   ├── scan/
│   │       │   │   ├── chat/
│   │       │   │   ├── report/
│   │       │   │   ├── history/
│   │       │   │   └── settings/
│   │       │   ├── (auth)/      # Clerk sign-in / sign-up pages
│   │       │   ├── api/         # Next.js API routes (UploadThing handler)
│   │       │   └── share/       # Public report sharing
│   │       ├── components/      # Shared UI components
│   │       ├── features/        # Feature-scoped modules
│   │       │   ├── analysis/
│   │       │   ├── chat/
│   │       │   ├── counter-offer/
│   │       │   ├── dashboard/
│   │       │   ├── multilingual/
│   │       │   ├── power/
│   │       │   ├── precedent/
│   │       │   ├── report/
│   │       │   ├── summary/
│   │       │   └── upload/
│   │       ├── hooks/           # Custom React hooks
│   │       ├── lib/             # Shared utilities and API client
│   │       ├── store/           # Zustand global state
│   │       └── types/           # TypeScript type definitions
│   │
│   └── worker/                  # Celery worker application
│       ├── celery_app.py        # Celery + Beat configuration
│       ├── pipeline/            # Thin pipeline orchestration steps
│       │   ├── step_01_download.py
│       │   ├── step_02_decrypt.py
│       │   ├── step_03_parse.py
│       │   └── step_04_detect_type.py
│       └── tasks/               # Celery task definitions
│           ├── process_contract.py      # 18-step main pipeline
│           ├── embed_contract.py        # pgvector embedding task
│           ├── generate_counter_offer.py
│           ├── generate_report.py
│           ├── contract_analysis.py
│           ├── blockchain_tasks.py      # Beat: tx confirmation + health
│           ├── register_contract_on_chain.py
│           ├── translate_results.py
│           └── cleanup_expired_reports.py
│
├── services/
│   ├── api/                     # FastAPI REST API
│   │   └── app/
│   │       ├── api/v1/
│   │       │   └── endpoints/   # auth, contracts, upload, analysis,
│   │       │                    # streaming, counter_offer, summary,
│   │       │                    # power, precedent, report, chat,
│   │       │                    # translate, dashboard, blockchain
│   │       ├── core/            # config.py (Pydantic Settings)
│   │       ├── db/              # session.py, base.py
│   │       ├── models/          # SQLAlchemy ORM models
│   │       ├── repositories/    # Data access layer (query-only)
│   │       ├── schemas/         # Pydantic request/response schemas
│   │       ├── services/        # Business logic layer
│   │       ├── utils/           # Helpers
│   │       ├── workers/         # SSE streaming worker
│   │       └── migrations/      # Alembic migration scripts
│   │
│   └── ai/                      # Standalone AI microservice (FastAPI)
│       └── app/
│           ├── api/routes/      # chat, translate, analyze,
│           │                    # counter_offer, precedent
│           ├── models/          # openrouter_client.py, model_config.py
│           ├── pipelines/       # AI pipeline modules
│           │   ├── clause_extraction.py
│           │   ├── type_detection.py
│           │   ├── risk_classification.py   # Two-pass triage + LLM
│           │   ├── consequence_generation.py
│           │   ├── power_analysis.py
│           │   ├── precedent_retrieval.py   # RAG pipeline
│           │   ├── counter_offer.py         # RAG counter-offer
│           │   ├── summary.py
│           │   └── multilingual_pipeline.py
│           ├── prompts/         # Prompt templates (*.txt files)
│           │   ├── risk_analysis.txt
│           │   ├── counter_offer.txt
│           │   ├── precedent.txt
│           │   ├── consequence.txt
│           │   ├── power_asymmetry.txt
│           │   ├── summary.txt
│           │   └── type_detection.txt
│           ├── rules/           # Rule engine
│           │   ├── regex_rules.py   # 40+ compiled regex patterns
│           │   └── risk_mapper.py   # Triage → GREEN/YELLOW/RED
│           ├── multilingual/    # DeepL translator + language detector
│           ├── parser/          # PDF/DOCX parsing
│           ├── rag/             # RAG utilities
│           └── utils/           # confidence_scorer.py, prompt_loader.py
│
├── blockchain/                  # Smart contracts (Hardhat)
│   ├── contracts/
│   │   ├── ContractRegistry.sol # Immutable hash registry on Polygon PoS
│   │   └── AuditTrail.sol       # On-chain audit event anchoring
│   ├── ignition/                # Hardhat Ignition deployment modules
│   ├── abis/                    # Compiled ABI JSON
│   └── scripts/                 # Deployment scripts
│
├── agents/                      # Agent configuration (multi-agent dev)
│   ├── backend/prompt.md        # Backend agent system prompt + rules
│   ├── frontend/                # Frontend agent configuration
│   ├── reviewer/                # Code review agent
│   └── orchestrator/            # Orchestration agent
│
├── docs/                        # Extended documentation
├── scripts/                     # DB seeding, deployment helpers
├── tests/                       # Integration and unit tests
├── docker-compose.yml           # Local dev: db, redis, api, ai, worker
└── .env.example                 # Environment variable template
```
---
## Environment Variables
Copy `.env.example` to `.env` and fill in the values:
```bash
cp .env.example .env
```
```env
# ── Frontend ──────────────────────────────────────────────────────────────
# URL of the FastAPI backend (consumed by Next.js server components)
NEXT_PUBLIC_API_URL=http://localhost:8000
# Clerk publishable key (from Clerk Dashboard > API Keys)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
# Clerk secret key (server-side auth verification)
CLERK_SECRET_KEY=sk_test_...
# UploadThing — file storage CDN
UPLOADTHING_SECRET=sk_live_...
UPLOADTHING_APP_ID=your-app-id
# ── Backend API ───────────────────────────────────────────────────────────
# PostgreSQL with pgvector (asyncpg driver required)
DATABASE_URL=postgresql+asyncpg://user:password@host/legaltech
# Upstash Redis — task broker and SSE pub/sub (use rediss:// for TLS)
REDIS_URL=rediss://default:password@host.upstash.io:6379?ssl_cert_reqs=none
# Clerk webhook secret (from Clerk Dashboard > Webhooks)
CLERK_WEBHOOK_SECRET=whsec_...
# Clerk JWKS URL for JWT verification
CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json
# ── AI Service ────────────────────────────────────────────────────────────
# OpenRouter API key (openrouter.ai — free models supported)
OPENROUTER_API_KEY=sk-or-...
# Primary LLM — deep reasoning tasks (risk classification, precedents)
PRIMARY_MODEL=meta-llama/llama-3.3-70b-instruct:free
# Fast LLM — latency-sensitive tasks (type detection, summary)
FAST_MODEL=google/gemini-2.0-flash-exp:free
# DeepL API key — for multilingual translation (free tier: 500k chars/month)
DEEPL_API_KEY=...
# Sentence-transformers embedding model (runs locally, no API cost)
EMBEDDING_MODEL=all-MiniLM-L6-v2
# ── Blockchain (optional) ─────────────────────────────────────────────────
# Polygon RPC URL (Alchemy, Infura, or public)
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/...
# Deployer wallet private key
POLYGON_PRIVATE_KEY=0x...
# Deployed ContractRegistry contract address
CONTRACT_REGISTRY_ADDRESS=0x...
# ── Shared ────────────────────────────────────────────────────────────────
# URL of the AI microservice (internal network in Docker)
AI_SERVICE_URL=http://localhost:8001
# Environment flag
ENVIRONMENT=development
```
---
## Local Development Setup
### Prerequisites
|
 Tool 
|
 Version 
|
|
---
|
---
|
|
 Python 
|
 3.13+ 
|
|
 Node.js 
|
 20+ 
|
|
 Docker + Docker Compose 
|
 Latest stable 
|
|
 Git 
|
 Any 
|
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
### 3. Start Databases and Infrastructure
```bash
docker compose up db redis -d
```
### 4. Set Up the Backend API
```bash
cd services/api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Run database migrations
alembic upgrade head
# Start API server
python run.py
# → http://localhost:8000
```
### 5. Set Up the AI Service
```bash
cd services/ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
# → http://localhost:8001
```
### 6. Set Up the Celery Worker
```bash
cd apps/worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Start the worker
celery -A celery_app worker --loglevel=info
# (Optional) Start the Beat scheduler for periodic tasks
celery -A celery_app beat --loglevel=info
```
### 7. Set Up the Frontend
```bash
cd apps/web
npm install
npm run dev
# → http://localhost:3000
```
### 8. (Optional) Seed Legal Precedents into pgvector
```bash
cd services/ai
python scripts/seed_precedents.py
```
---
## Running with Docker Compose
To spin up all services (API, AI, Worker, PostgreSQL, Redis) in one command:
```bash
docker compose up --build
```
Service ports:
|
 Service 
|
 Port 
|
|
---
|
---
|
|
 Next.js (run separately) 
|
`3000`
|
|
 FastAPI (API) 
|
`8000`
|
|
 FastAPI (AI) 
|
`8001`
|
|
 PostgreSQL 
|
`5433`
 (mapped from 5432) 
|
|
 Redis 
|
`6379`
|
---
## API Overview
All protected endpoints require a `Bearer <clerk_jwt>` token in the `Authorization` header.
### Authentication
|
 Method 
|
 Path 
|
 Description 
|
|
---
|
---
|
---
|
|
`POST`
|
`/api/v1/webhooks/clerk`
|
 Clerk user sync webhook (Svix-verified) 
|
### Contracts & Upload
|
 Method 
|
 Path 
|
 Description 
|
|
---
|
---
|
---
|
|
`POST`
|
`/api/v1/upload`
|
 Create contract + enqueue scan job 
|
|
`GET`
|
`/api/v1/contracts`
|
 List user's contracts 
|
|
`GET`
|
`/api/v1/contracts/{id}`
|
 Get contract details 
|
|
`DELETE`
|
`/api/v1/contracts/{id}`
|
 Delete contract and all results 
|
### Analysis & Streaming
|
 Method 
|
 Path 
|
 Description 
|
|
---
|
---
|
---
|
|
`POST`
|
`/api/v1/scan`
|
 Trigger analysis on existing contract 
|
|
`GET`
|
`/api/v1/scan/{jobId}/status`
|
 Poll scan job status 
|
|
`GET`
|
`/api/v1/scan/{jobId}/stream?token=`
|
 SSE stream of clause results 
|
|
`GET`
|
`/api/v1/scan/{jobId}/clauses`
|
 Fetch all clause results 
|
### AI Features (On-demand)
|
 Method 
|
 Path 
|
 Description 
|
|
---
|
---
|
---
|
|
`POST`
|
`/api/v1/counter-offer`
|
 Generate 3 counter-offer versions for a clause 
|
|
`GET`
|
`/api/v1/summary/{contractId}`
|
 Get summary card 
|
|
`GET`
|
`/api/v1/power/{contractId}`
|
 Get power asymmetry analysis 
|
|
`GET`
|
`/api/v1/precedent/{clauseId}`
|
 Get legal precedent match 
|
|
`POST`
|
`/api/v1/chat`
|
 Q&A chat about a contract 
|
|
`POST`
|
`/api/v1/translate`
|
 Translate text (DeepL proxy) 
|
### Reports & Dashboard
|
 Method 
|
 Path 
|
 Description 
|
|
---
|
---
|
---
|
|
`POST`
|
`/api/v1/report/{contractId}`
|
 Generate PDF report 
|
|
`GET`
|
`/api/v1/report/share/{uuid}`
|
 Public report access (no auth) 
|
|
`GET`
|
`/api/v1/dashboard`
|
 Aggregated user stats 
|
### Blockchain
|
 Method 
|
 Path 
|
 Description 
|
|
---
|
---
|
---
|
|
`POST`
|
`/api/v1/blockchain/register/{contractId}`
|
 Register contract on Polygon 
|
|
`GET`
|
`/api/v1/blockchain/status/{contractId}`
|
 On-chain registration status 
|
|
`GET`
|
`/api/v1/blockchain/health`
|
 RPC connectivity health 
|
---
## Database Design
All tables use UUIDs as primary keys. All queries are scoped by `user_id` (enforced at the repository layer).
|
 Table 
|
 Purpose 
|
|
---
|
---
|
|
`users`
|
 Synced from Clerk via webhook (id = Clerk user ID) 
|
|
`contracts`
|
 Uploaded contract metadata: 
`file_ref`
 (UploadThing URL), 
`contract_type`
, 
`detected_language`
, 
`party_roles`
|
|
`scan_jobs`
|
 Pipeline status tracker: 
`status`
 ∈ {queued, processing, complete, failed}, 
`progress_pct`
, 
`error_message`
|
|
`clauses`
|
 Per-clause analysis: 
`text`
, 
`risk_level`
, 
`risk_category`
, 
`plain_english`
, 
`worst_case_scenario`
, 
`confidence`
, 
`negotiable`
|
|
`analysis_results`
|
 Contract-level aggregates: 
`power_score`
, 
`power_label`
, 
`one_liner`
, 
`overall_risk_score`
, 
`should_sign`
, 
`leverage_points`
, 
`top_concerns`
|
|
`embeddings`
|
 pgvector table (384-dim): 
`embedding_type`
 ∈ {contract_qa, favorable_clause, precedent}, 
`context_data`
 JSONB, 
`embedding VECTOR(384)`
|
|
`precedent_matches`
|
 RAG output per HIGH-risk clause: 
`precedent_summary`
, 
`enforcement_likelihood`
, 
`confidence_score`
, 
`cited_cases`
 JSONB 
|
|
`counter_offers`
|
 Three-version counter-offers: 
`aggressive_version`
, 
`balanced_version`
, 
`conservative_version`
, 
`negotiation_email`
|
|
`reports`
|
 Generated PDF metadata: 
`share_uuid`
, 
`expires_at`
, 
`report_url`
|
|
`contract_blockchain_records`
|
 On-chain registration: 
`contract_hash`
, 
`polygon_tx_hash`
, 
`polygon_block_number`
, 
`registration_status`
, 
`ipfs_cid`
|
|
`audit_trail_events`
|
 Per-event audit log anchored on-chain: 
`event_type`
, 
`polygon_tx_hash`
, 
`on_chain_status`
|
### pgvector Index
```sql
CREATE INDEX embeddings_embedding_idx
ON embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```
---
## Scalability Considerations
### Async-First Design
- FastAPI API is fully async (SQLAlchemy async sessions, httpx async client)
- Celery worker executes pipeline steps sequentially within a task to avoid race conditions on shared DB state, but multiple worker replicas can process different contracts in parallel
### Queue-Based Decoupling
- `POST /upload` returns in <200ms — the 18-step pipeline runs entirely in the background
- Celery Beat handles all scheduled maintenance (blockchain confirmation polling, report cleanup) without blocking request handlers
### Vector Search Performance
- `all-MiniLM-L6-v2` produces compact 384-dim vectors (vs 1536-dim for OpenAI embeddings) — IVFFlat index keeps search latency <50ms even at scale
- Precedent and favorable-clause corpora are pre-seeded; they do not grow with user uploads
### LLM Cost & Latency Optimization
- Rule engine eliminates LLM calls for GREEN clauses (typically 40–60% of all clauses)
- Batching (≤20 clauses/call) reduces LLM round trips by ~20×
- Model routing sends lightweight tasks to Gemini Flash and heavy reasoning to Llama 70B
- All free-tier OpenRouter models — zero per-token cost during development
### Caching
- Blockchain health status is cached in Redis with a 90-second TTL to avoid hammering the RPC
- Celery result backend is Redis — task state is persisted and queryable
### Retry & Circuit Breaker
- OpenRouter client: exponential backoff on 429/5xx, respects `Retry-After` header
- Celery tasks: 3 retries with `60 × 2^attempt` second delays
- Blockchain service: `pybreaker` circuit breaker to prevent cascading failures on RPC downtime
---
## Security
|
 Concern 
|
 Implementation 
|
|
---
|
---
|
|
**
Authentication
**
|
 Clerk JWT verified on every protected route via 
`get_current_user_id`
 dependency. JWKS URL verified, not shared secret. 
|
|
**
Webhook Verification
**
|
 Clerk webhooks verified via Svix library before any processing. Invalid signatures → 400. 
|
|
**
Resource Isolation
**
|
 All DB queries filter by 
`user_id`
. A user can never read another user's contract or clause. Unauthorized access returns 403 on most resources, 404 on contracts (to avoid existence leakage). 
|
|
**
File Security
**
|
 Files are stored by UploadThing CDN and referenced only by URL. File bytes are never stored in the database. 
|
|
**
Secrets Handling
**
|
 All secrets loaded from environment via Pydantic 
`BaseSettings`
. Never logged. Never hardcoded. 
|
|
**
SSE Auth
**
|
 EventSource (browser API) cannot send 
`Authorization`
 headers. The SSE endpoint accepts a 
`?token=<jwt>`
 query parameter and validates it internally before subscribing to the Redis channel. 
|
|
**
Rate Limiting
**
|
 Per-user rate limiting via Upstash Redis. 
|
|
**
Encryption
**
|
 PyCryptodome available for client-side encrypted document support (decryption key never stored). 
|
|
**
On-Chain Integrity
**
|
 Contract hashes registered on Polygon are immutable — tamper-evident proof of document state at registration time. 
|
---
## Blockchain Layer
Two Solidity contracts are deployed on Polygon PoS:
### `ContractRegistry.sol`
- Stores `keccak256(pdfBytes)` + `keccak256(metadata)` + IPFS CID for each contract
- Append-only: once registered, a record cannot be modified or deleted
- Emit `ContractRegistered` event on each registration (indexed by `contractHash` and `uploader`)
- Paginated hash retrieval for registry enumeration
### `AuditTrail.sol`
- Records individual audit events (upload, view, analysis, share) on-chain
- Each event is linked to a contract hash and actor address
### Celery Beat Maintenance
- **Every 5 min**: `confirm_blockchain_records` — polls Polygon for transaction receipts on all `pending` records; updates `registration_status = 'confirmed'` and stores `block_number`
- **Every 10 min**: `blockchain_health_monitor` — checks RPC connectivity and publishes health status to Redis (`blockchain:health:status`, 90s TTL)
---
## Future Improvements
- **Parallel clause processing** — use `asyncio.gather` or `ThreadPoolExecutor` to run precedent retrieval across all HIGH-risk clauses concurrently (currently sequential)
- **pgvector HNSW index** — migrate from IVFFlat to HNSW for better recall at high vector counts
- **Streaming LLM output** — surface token-level streaming to the UI for consequence and counter-offer generation (infrastructure already supports SSE)
- **Clause comparison across contracts** — embed all user contracts and surface semantically similar clauses across different agreements
- **Model fallback chain** — if PRIMARY_MODEL quota is exhausted, automatically fall back to FAST_MODEL or a configurable tertiary model
- **Fine-tuned embeddings** — fine-tune `all-MiniLM-L6-v2` on legal domain text for improved retrieval accuracy on niche clause types
- **IPFS pinning** — integrate Pinata or web3.storage to automatically pin uploaded contracts to IPFS before on-chain registration
- **Multi-party analysis** — support contracts with more than two parties; assign per-party risk profiles
- **Attorney review workflow** — flag clauses with `confidence < 0.7` for human review in a dedicated queue with e-mail notifications
- **Audit export** — CSV/JSON export of all clause-level audit trail events per contract
---
## Screenshots / Demo
> _Screenshots and demo recordings will be added in an upcoming release._
To run a local demo:
1. Complete the local development setup above
2. Navigate to `http://localhost:3000`
3. Sign in with Clerk
4. Upload any PDF or DOCX contract via the Upload page
5. Watch clause results stream in real time on the Scan page
---
## Deployment
### Production Architecture
```
Vercel (Next.js frontend)
    │
    │ HTTPS
    ▼
Railway / Render (FastAPI API — services/api)   ←── Neon PostgreSQL (pgvector)
                                                ←── Upstash Redis (TLS)
    │
    │ internal HTTP
    ▼
Railway / Render (FastAPI AI — services/ai)
Railway / Render (Celery Worker — apps/worker)
Railway / Render (Celery Beat — scheduled tasks)
```
### Environment-Specific Notes
- Set `ENVIRONMENT=production` in all services
- Use `rediss://` (TLS) for the Redis URL in production (Upstash requires it)
- Use `postgresql+asyncpg://` for the DATABASE_URL (not `postgresql://`)
- Deploy `ContractRegistry.sol` and `AuditTrail.sol` to Polygon Mainnet or Amoy Testnet via Hardhat Ignition
- Configure Clerk's production instance and update all `CLERK_*` variables
### Database Migrations in Production
```bash
cd services/api
alembic upgrade head
```
---
## Contribution Guide
We welcome contributions! Please follow these guidelines:
### Getting Started
1. Fork the repository and clone your fork
2. Create a feature branch from `main`: `git checkout -b feat/your-feature`
3. Complete the local development setup
4. Make your changes, ensuring all existing tests pass
### Code Standards
**Python (backend/worker/AI service)**
- Python 3.13, fully typed (`mypy`-compatible)
- All functions have type hints and docstrings
- Async functions use `async def` — do not mix sync and async in the same pipeline
- Use structured logging (`key=value` format) — never `print()`
- Access all config via `app.core.config.settings` — never `os.environ` directly
- Repository layer: queries only, zero business logic
- Service layer: business logic only, zero raw SQL
**TypeScript (frontend)**
- Strict TypeScript mode
- Components are single-responsibility, co-located with their feature module
- State via Zustand stores — no prop-drilling beyond 2 levels
- Use Radix UI primitives for accessible interactive components
### Pull Request Process
1. Ensure your branch is up to date with `main`
2. Write or update tests for your changes
3. Run the test suite: `pytest tests/` (backend) and `npm run lint` (frontend)
4. Open a PR with a clear title and description of what changed and why
5. Link any related issues
### Commit Convention
Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat(ai): add multilingual support for Hindi contracts
fix(worker): handle empty clause list in power analysis
docs(readme): update environment variable table
```
### Branch Naming
- `feat/<scope>/<description>` — new features
- `fix/<scope>/<description>` — bug fixes
- `docs/<description>` — documentation only
- `refactor/<scope>/<description>` — non-functional refactors
- `chore/<description>` — build/tooling changes
---
## License
MIT License — see [LICENCE](./LICENCE) for details.
Copyright (c) 2026 Soumojit Das
---
<p align="center">
  Built with ⚖️ and 🤖 to make legal contracts accessible to everyone.
</p>
*Last updated: May 2026*
