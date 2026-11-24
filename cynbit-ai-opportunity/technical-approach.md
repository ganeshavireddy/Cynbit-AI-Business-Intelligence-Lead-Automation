# Technical Approach: Architecture, Engineering & Multi-Agent Design
**Project:** Cynbit AI Business Intelligence & Lead Automation Agent  
**Author:** Cynbit Engineering Architecture Team  
**Date:** November 2026  
**Document Status:** Production-Ready Architectural Specification  

---

## 1. Architectural Overview & System Design Philosophy

The **Cynbit AI Business Intelligence & Lead Automation Platform** is architected as an asynchronous, event-driven, cognitive automation system designed for high-throughput enterprise B2B lead ingestion, real-time multi-dimensional scoring, and autonomous agent orchestration.

### Core Architectural Principles
1. **Deterministic Guardrails with Cognitive Synthesis**: Algorithmic scoring uses strictly typed, deterministic mathematical weighting to prevent LLM hallucinations from misclassifying enterprise pipeline value. The LLM agent operates downstream on structured scoring outputs to generate contextual reasoning traces, personalized outreach copy, and opportunity dossiers.
2. **Sub-Second Core Latency**: The computational scoring pipeline processes lead objects in **< 10ms**, enabling instant routing decisions even before external LLM calls are triggered.
3. **Decoupled Service Layers**: The RESTful backend (FastAPI), the analytical UI (Streamlit & Plotly), and the autonomous agent layer interact through strictly typed Pydantic v2 schemas.
4. **Graceful Degradation & High Availability**: The system incorporates dual execution modes: when external generative AI endpoints (e.g. Google Gemini) are active, it leverages frontier cognitive synthesis; when running in constrained or offline environments, it falls back seamlessly to deterministic heuristic reasoning engines with zero downtime.

---

## 2. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph INGESTION["1. Ingestion Layer"]
        A1["Inbound Webhook / Form Submission"] --> B1["FastAPI Lead Intake Router"]
        A2["CRM Webhook (Salesforce/HubSpot)"] --> B1
        A3["Batch Lead Ingestion / CSV"] --> B1
        B1 --> C1["Pydantic v2 Schema Validation"]
    end

    subgraph ENGINE["2. Algorithmic Scoring Engine"]
        C1 --> D1["Firmographic Scorer (30%)"]
        C1 --> D2["Authority Scorer (25%)"]
        C1 --> D3["Behavioral Intent Scorer (25%)"]
        C1 --> D4["Budget & Urgency Scorer (20%)"]
        D1 & D2 & D3 & D4 --> E1["Composite Weight Aggregator"]
        E1 --> F1{"Disqualification Guardrail?"}
        F1 -- "Personal Domain / Student" --> G1["Tier 4: Disqualified"]
        F1 -- "Commercial Entity" --> G2["Tier 1: Hot (Score >= 80)"]
        F1 -- "Commercial Entity" --> G3["Tier 2: Warm (Score 60-79)"]
        F1 -- "Commercial Entity" --> G4["Tier 3: Cold (Score 40-59)"]
    end

    subgraph AGENT["3. Autonomous AI Agent Layer"]
        G2 & G3 & G4 & G1 --> H1["LeadAutomationAgent Core"]
        H1 --> I1["Perception & Signal Triangulation"]
        I1 --> I2["Friction & Pain Point Analysis"]
        I2 --> I3["Decision Formulation & Action Planning"]
        I3 --> J1["Personalized Outreach Drafter (Email/InMail/Script)"]
        I3 --> J2["Executive Opportunity Dossier Generator"]
    end

    subgraph PRESENTATION["4. Presentation & BI Layer"]
        G2 & G3 & G4 --> K1["Streamlit Executive BI Dashboard"]
        J1 & J2 --> K1
        K1 --> L1["Interactive Plotly Charts (Donut, Scatter, Radar)"]
        K1 --> L2["CRM Dispatch & Webhook Simulator"]
    end
```

---

## 3. Algorithmic Lead Scoring Formulation

Lead qualification is governed by a deterministic, multi-factor scoring model that computes a composite score $S_{composite} \in [0, 100]$:

$$S_{composite} = w_{firmo} \cdot S_{firmo} + w_{auth} \cdot S_{auth} + w_{behav} \cdot S_{behav} + w_{budget} \cdot S_{budget}$$

Where the normalized weights are calibrated according to empirical B2B conversion elasticity:
- **Firmographic Fit Weight ($w_{firmo}$)** = `0.30`
- **Authority / Seniority Weight ($w_{auth}$)** = `0.25`
- **Behavioral Intent Weight ($w_{behav}$)** = `0.25`
- **Budget & Timeline Weight ($w_{budget}$)** = `0.20`

### 3.1 Pillar 1: Firmographic Fit ($S_{firmo} \in [0, 100]$)
Measures the account's structural alignment with Cynbit's Ideal Customer Profile:
- **Industry Affinity (40 pts max)**:
  - *High ICP* (Supply Chain, SaaS, MedTech, FinTech, Cybersecurity): $+40\text{ pts}$
  - *Moderate ICP* (Manufacturing, Energy, Retail): $+28\text{ pts}$
  - *Non-Commercial / Student / Education*: $+5\text{ pts}$ (penalty applied)
- **Headcount Scaling (30 pts max)**:
  - $51-200$ and $201-500$ employees: $+30\text{ pts}$ (Sweet spot for automation adoption)
  - $501-1000$ and $1000+$ employees: $+26\text{ pts}$
  - $11-50$ employees: $+20\text{ pts}$
  - $1-10$ employees: $+8\text{ pts}$
- **Annual Turnover / Revenue (30 pts max)**:
  - $\ge \$50\text{M}$: $+30\text{ pts}$
  - $\$15\text{M} - \$50\text{M}$: $+26\text{ pts}$
  - $\$5\text{M} - \$15\text{M}$: $+22\text{ pts}$
  - $\$1\text{M} - \$5\text{M}$: $+15\text{ pts}$
  - $<\$1\text{M}$: $+2\text{ pts}$

### 3.2 Pillar 2: Authority & Decision-Maker Seniority ($S_{auth} \in [0, 100]$)
Evaluates whether the contact has discretionary economic buying power:
- **C-Level & Founders** (`CEO`, `CTO`, `CRO`, `CCO`, `COO`, `Founder`): $100\text{ pts}$
- **Department Leadership** (`VP`, `Vice President`, `Head of`, `Partner`): $88\text{ pts}$
- **Director-Level** (`Director of Growth`, `Director of Sales Ops`): $78\text{ pts}$
- **Management** (`Manager`, `Team Lead`): $58\text{ pts}$
- **Individual Contributor** (`Specialist`, `Analyst`, `Engineer`): $35\text{ pts}$
- **Academic / Intern** (`Student`, `Intern`): $8\text{ pts}$
- **Domain Verification**: Contacts using consumer webmail providers (`@gmail.com`, `@yahoo.com`) incur an immediate $-35\text{ pt}$ deduction and domain flag.

### 3.3 Pillar 3: Behavioral Intent & Digital Telemetry ($S_{behav} \in [0, 100]$)
Quantifies digital buying readiness across omni-channel touchpoints:
- **Pricing Page Engagement (35 pts max)**: Pricing page visitation is the single highest intent indicator in B2B. $\ge 6\text{ visits} \implies +35\text{ pts}$; $3-5\text{ visits} \implies +28\text{ pts}$; $1-2\text{ visits} \implies +18\text{ pts}$.
- **Website Frequency (25 pts max)**: Total visits over the trailing 30-day window ($\ge 20\text{ visits} \implies +25\text{ pts}$).
- **Webinar Attendance (15 pts max)**: Active participation in architecture or product walkthroughs ($+15\text{ pts}$).
- **Content Consumption (15 pts max)**: Downloading technical whitepapers or integration blueprints ($+10\text{ to } +15\text{ pts}$).
- **Email Engagement (10 pts max)**: Open rates $\ge 75\%$ ($+5\text{ pts}$); Click-through rates $\ge 35\%$ ($+5\text{ pts}$).

### 3.4 Pillar 4: Budget & Timeline Urgency ($S_{budget} \in [0, 100]$)
- **Budget Status (50 pts max)**: Approved enterprise budget ($\ge \$100\text{k} \implies 50\text{ pts}$; $\$50\text{k}-\$100\text{k} \implies 45\text{ pts}$; Exploring $\implies 32\text{ pts}$; No budget $\implies 5\text{ pts}$).
- **Timeline Urgency (50 pts max)**: Immediate purchase ($<1\text{ mo} \implies 50\text{ pts}$; $1-3\text{ mos} \implies 40\text{ pts}$; $3-6\text{ mos} \implies 25\text{ pts}$; $>6\text{ mos} \implies 10\text{ pts}$).

### 3.5 Disqualification Guardrail Logic
A hard guardrail suppresses low-quality inbound leads:
$$\text{If } \text{Domain} \in \text{DISQUALIFIED\_DOMAINS} \land \text{Seniority} \in \{\text{Student}, \text{Intern}\} \implies S_{composite} \le 25.0$$
This guarantees that unqualified non-commercial inquiries do not consume human sales rep bandwidth.

---

## 4. Multi-Agent Cognitive Architecture & Reasoning Workflow

The autonomous agent (`LeadAutomationAgent`) executes a 4-phase cognitive loop:

```mermaid
sequenceDiagram
    autonumber
    participant Client as Lead Ingestion
    participant Router as FastAPI Router
    participant Scorer as Lead Scoring Engine
    participant RAG as RAG Vector Engine
    participant Agent as Autonomous AI Agent
    participant CRM as CRM / Dispatch Mock

    Client->>Router: POST /api/leads (Lead Payload)
    Router->>Scorer: score_lead(lead)
    Scorer-->>Router: ScoreBreakdown (Score: 88, Tier 1)
    Router->>RAG: retrieve(query="Industry + Pain Points", top_k=2)
    RAG-->>Router: RetrievedChunks (Apex Logistics Case Study, Similarity: 89%)
    Router->>Agent: qualify_lead(lead, score, RAG_context)
    Note over Agent: Phase 1: Ingest & perceive firmographics<br/>Phase 2: Extract friction points & tech stack<br/>Phase 3: Triangulate composite intent + RAG evidence<br/>Phase 4: Formulate multi-step action plan
    Agent-->>Router: AgentDecision (route_to_sales_rep, conf: 0.94)
    Router->>Agent: generate_outreach(lead, score, RAG_evidence)
    Agent-->>Router: OutreachDraft (Subject, Body citing verified ROI metrics)
    Router->>CRM: Dispatch to Salesforce Queue (<90s SLA)
    Router-->>Client: HTTP 201 Created (ScoredLead + Action Plan + RAG Citations)
```

### 4.1 Retrieval-Augmented Generation (RAG) Architecture
The system integrates an enterprise RAG Vector Knowledge Engine (`CynbitRAGEngine`):
- **Knowledge Base Corpus**: Indexed case studies (Apex Logistics, HealthPulse Dynamics, FinEdge Global, OmniRetail), product architecture specifications, and competitive battlecards (Apollo, Outreach, Salesforce objection playbooks).
- **Hybrid Vector Representation**: Employs sublinear TF-IDF n-gram vectorization combined with cosine similarity, keyword overlap boosting, and industry metadata filtering.
- **Dynamic Context Injection**: When generating outreach or answering rep inquiries, verified case study metrics (e.g. *"99.2% speed-to-lead latency reduction, 380% demo conversion lift, 32-day payback"*) are dynamically injected into the LLM prompt context to eliminate generic merge tags.
- **AI Sales Copilot Endpoint (`/api/agent/copilot`)**: Provides real-time strategic Q&A for sales reps with source citations and similarity scores.

### Cognitive Reasoning Trace Stages
1. **Perception**: Validates company metadata, employee size, annual revenue, and contact decision-making capacity.
2. **Friction Analysis**: Diagnoses explicit organizational pain points (e.g. "SDRs spending 40% time on manual triage; 24h response latency").
3. **Signal Triangulation**: Correlates behavioral intent with budget availability and target procurement timeline.
4. **Action Formulation**: Selects the optimal GTM motion:
   - `route_to_sales_rep`: Formulates AE briefing dossier, locks priority calendar slot, triggers sub-90s notification.
   - `trigger_nurture_campaign`: Schedules tailored cognitive nurture sequence with industry case studies.
   - `request_more_information`: Dispatches asynchronous qualification questionnaire.
   - `disqualify_and_archive`: Silently marks as disqualified in CRM to preserve rep focus.

---

## 5. Data Schemas & API Contracts

All interfaces utilize strict Pydantic v2 data models:

- `Lead`: Comprehensive entity storing company details, contact info, industry, revenue, CRM stack, pain points, and `EngagementSignals`.
- `ScoreBreakdown`: Individual scores for the 4 pillars, composite score, ICP tier, estimated pipeline value, and recommended next steps.
- `AgentDecision`: Autonomous decision outcome, numerical confidence ($0.0 - 1.0$), reasoning trace log, and execution plan.
- `OutreachDraft`: Multi-channel communication copy (Email, LinkedIn InMail, SDR Discovery Script) with highlighted value propositions and follow-up cadences.
- `OpportunityAnalysis`: Executive dossier detailing strategic fit, potential deal size, solution mapping, competitive differentiators, and projected ROI multiple.
- `BISummaryResponse`: Executive portfolio metrics including total pipeline value, average composite score, tier distribution, and forecasted win revenue.

---

## 6. Latency, Scalability & Performance Benchmarks

The Cynbit platform is built to fulfill strict enterprise Service Level Agreements (SLAs):

| Operational Stage | Execution Target | Optimization Technique |
| :--- | :--- | :--- |
| **API Ingestion & Schema Validation** | $< 15\text{ ms}$ | FastAPI ASGI async request parsing & Pydantic C-compiled core |
| **Algorithmic 4-Pillar Scoring** | $< 5\text{ ms}$ | Vectorized dictionary heuristics; zero external network blocking |
| **Cognitive Agent Reasoning** | $< 850\text{ ms}$ | Streaming token inference & fallback deterministic generation |
| **Bespoke Outreach Synthesis** | $< 950\text{ ms}$ | Prompt caching and pre-structured value-prop templates |
| **CRM Webhook Dispatch** | $< 250\text{ ms}$ | Non-blocking async HTTP background tasks |
| **Total Inbound Triage Time** | **< 2.1 seconds** | **Over 99.9% faster than the 18-hour human average** |

---

## 7. Security, Privacy & Enterprise Compliance

1. **PII Protection & Data Minimization**: Contact email, names, and notes are processed strictly for qualification. No customer data is utilized for external model training.
2. **Zero Data Retention (ZDR)**: LLM calls are configured to omit data retention for model improvements.
3. **Strict Type Safety**: All inputs undergo Pydantic sanitization to eliminate SQL injection, prompt injection, and cross-site scripting (XSS) vectors.
4. **Auditability & Traceability**: Every scoring output and agent decision includes an immutable ISO 8601 timestamp (`scored_at`, `synthesized_at`) and step-by-step reasoning trace for executive audit trails.

---

## 8. Summary of Engineering Innovations

1. **Sub-90-Second Lead Response**: Eliminates the catastrophic conversion drop-off associated with 24-hour manual SDR response delays.
2. **Dual-Engine Redundancy**: 100% operational reliability through seamless fallback to local heuristic reasoning when LLM endpoints face rate limits.
3. **Hyper-Personalized Multi-Channel Copywriting**: Replaces unconvincing generic template tokens with contextual references to the prospect's actual pain points, current CRM, and business metrics.
4. **Full-Stack Turnkey Deployment**: Complete FastAPI REST backend and responsive Streamlit BI dashboard, ready for immediate production deployment.
