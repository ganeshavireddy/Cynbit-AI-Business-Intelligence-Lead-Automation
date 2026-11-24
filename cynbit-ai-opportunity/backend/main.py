"""
main.py - Unconstrained FastAPI Backend for Cynbit AI Platform
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .schemas import (
    Lead, LeadCreate, ScoreBreakdown, ScoredLead,
    AgentDecision, OutreachDraft, OpportunityAnalysis, BISummaryResponse,
    RetrievedChunk, AddDocumentRequest, RAGQueryRequest, RAGQueryResponse,
    CopilotChatRequest, CopilotChatResponse, ScoringWeightsConfig, MultiTouchCadence
)
from .lead_scoring import score_lead, DEFAULT_CONFIG
from .agent import LeadAutomationAgent

app = FastAPI(
    title="Cynbit AI Business Intelligence & Lead Automation Agent API",
    description="Enterprise API for Autonomous Lead Qualification, Scoring, Dynamic RAG, and Multi-Channel Sales Orchestration",
    version="2.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stores & configuration
LEADS_STORE: Dict[str, Lead] = {}
SCORES_STORE: Dict[str, ScoreBreakdown] = {}
SCORING_CONFIG: ScoringWeightsConfig = ScoringWeightsConfig()
agent = LeadAutomationAgent()


def load_initial_leads():
    """Loads sample leads from data/sample_leads.json."""
    current_dir = Path(__file__).resolve().parent
    possible_paths = [
        current_dir.parent / "data" / "sample_leads.json",
        Path("data/sample_leads.json"),
        Path("cynbit-ai-opportunity/data/sample_leads.json")
    ]
    
    data_path = None
    for p in possible_paths:
        if p.exists():
            data_path = p
            break
    
    if data_path and data_path.exists():
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                leads_data = json.load(f)
                for item in leads_data:
                    lead = Lead(**item)
                    LEADS_STORE[lead.lead_id] = lead
                    SCORES_STORE[lead.lead_id] = score_lead(lead, SCORING_CONFIG)
            print(f"[Cynbit Backend] Ingested and scored {len(LEADS_STORE)} sample leads from {data_path}.")
        except Exception as e:
            print(f"[Cynbit Backend] Error loading initial leads: {e}")
    else:
        print("[Cynbit Backend] Warning: sample_leads.json path not found.")


def persist_leads():
    """Safely saves in-memory leads back to data/sample_leads.json."""
    current_dir = Path(__file__).resolve().parent
    possible_paths = [
        current_dir.parent / "data" / "sample_leads.json",
        Path("data/sample_leads.json"),
        Path("cynbit-ai-opportunity/data/sample_leads.json")
    ]
    for p in possible_paths:
        try:
            if p.parent.exists():
                with open(p, "w", encoding="utf-8") as f:
                    json.dump([l.dict() for l in LEADS_STORE.values()], f, indent=2)
        except Exception:
            pass


load_initial_leads()


@app.on_event("startup")
def startup_event():
    if not LEADS_STORE:
        load_initial_leads()


@app.get("/", tags=["Health & Metadata"])
def root():
    return {
        "status": "healthy",
        "service": "Cynbit AI Business Intelligence & Lead Automation Platform",
        "version": "2.0.0",
        "total_active_leads": len(LEADS_STORE),
        "total_indexed_documents": len(agent.rag.documents),
        "docs_url": "/docs"
    }


# ==============================================================================
# Dynamic Scoring Configuration
# ==============================================================================
@app.get("/api/scoring/config", response_model=ScoringWeightsConfig, tags=["Scoring Config"])
def get_scoring_config():
    """Returns currently active scoring weights and tier thresholds."""
    return SCORING_CONFIG


@app.post("/api/scoring/config", response_model=ScoringWeightsConfig, tags=["Scoring Config"])
def update_scoring_config(config: ScoringWeightsConfig):
    """Updates scoring weights and dynamically recalculates all indexed leads."""
    global SCORING_CONFIG
    SCORING_CONFIG = config
    for lead_id, lead in LEADS_STORE.items():
        SCORES_STORE[lead_id] = score_lead(lead, SCORING_CONFIG)
    return SCORING_CONFIG


# ==============================================================================
# Lead Ingestion & Management
# ==============================================================================
@app.get("/api/leads", response_model=List[ScoredLead], tags=["Leads"])
def list_leads(
    tier: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100)
):
    results = []
    for lead_id, lead in LEADS_STORE.items():
        score = SCORES_STORE.get(lead_id) or score_lead(lead, SCORING_CONFIG)
        if tier and tier.lower() not in score.tier.lower():
            continue
        if industry and industry.lower() not in lead.industry.lower():
            continue
        if min_score is not None and score.total_score < min_score:
            continue
        if search:
            query = search.lower()
            if query not in lead.company_name.lower() and query not in lead.contact_name.lower():
                continue
        results.append(ScoredLead(lead=lead, score=score))

    results.sort(key=lambda x: x.score.total_score, reverse=True)
    return results


@app.get("/api/leads/{lead_id}", response_model=ScoredLead, tags=["Leads"])
def get_lead(lead_id: str):
    if lead_id not in LEADS_STORE:
        raise HTTPException(status_code=404, detail=f"Lead with id '{lead_id}' not found.")
    lead = LEADS_STORE[lead_id]
    score = SCORES_STORE.get(lead_id) or score_lead(lead, SCORING_CONFIG)
    return ScoredLead(lead=lead, score=score)


@app.post("/api/leads", response_model=ScoredLead, status_code=status.HTTP_201_CREATED, tags=["Leads"])
def create_lead(payload: LeadCreate):
    new_id = f"LEAD-{1000 + len(LEADS_STORE) + 1}"
    lead_dict = payload.dict()
    lead_dict["lead_id"] = new_id
    lead = Lead(**lead_dict)
    score = score_lead(lead, SCORING_CONFIG)
    LEADS_STORE[new_id] = lead
    SCORES_STORE[new_id] = score
    persist_leads()
    return ScoredLead(lead=lead, score=score)


@app.post("/api/leads/bulk", response_model=List[ScoredLead], status_code=status.HTTP_201_CREATED, tags=["Leads"])
def bulk_create_leads(leads_list: List[LeadCreate]):
    """Ingests and scores an unconstrained batch of leads."""
    created = []
    for payload in leads_list:
        new_id = f"LEAD-{1000 + len(LEADS_STORE) + 1}"
        lead_dict = payload.dict()
        lead_dict["lead_id"] = new_id
        lead = Lead(**lead_dict)
        score = score_lead(lead, SCORING_CONFIG)
        LEADS_STORE[new_id] = lead
        SCORES_STORE[new_id] = score
        created.append(ScoredLead(lead=lead, score=score))
    persist_leads()
    return created


@app.post("/api/leads/{lead_id}/score", response_model=ScoreBreakdown, tags=["Scoring"])
def recalculate_score(lead_id: str):
    if lead_id not in LEADS_STORE:
        raise HTTPException(status_code=404, detail=f"Lead with id '{lead_id}' not found.")
    lead = LEADS_STORE[lead_id]
    score = score_lead(lead, SCORING_CONFIG)
    SCORES_STORE[lead_id] = score
    return score


@app.post("/api/leads/batch-score", tags=["Scoring"])
def batch_score():
    for lead_id, lead in LEADS_STORE.items():
        SCORES_STORE[lead_id] = score_lead(lead, SCORING_CONFIG)
    return {"message": f"Successfully re-scored {len(LEADS_STORE)} leads with active configuration."}


# ==============================================================================
# Autonomous AI Agent & Cadence
# ==============================================================================
@app.post("/api/leads/{lead_id}/agent/qualify", response_model=AgentDecision, tags=["AI Agent"])
def agent_qualify(lead_id: str):
    if lead_id not in LEADS_STORE:
        raise HTTPException(status_code=404, detail=f"Lead with id '{lead_id}' not found.")
    lead = LEADS_STORE[lead_id]
    score = SCORES_STORE.get(lead_id) or score_lead(lead, SCORING_CONFIG)
    return agent.qualify_lead(lead, score)


@app.post("/api/leads/{lead_id}/agent/outreach", response_model=OutreachDraft, tags=["AI Agent"])
def agent_outreach(
    lead_id: str,
    channel: str = Query("Email"),
    tone: str = Query("Strategic & Consultative")
):
    if lead_id not in LEADS_STORE:
        raise HTTPException(status_code=404, detail=f"Lead with id '{lead_id}' not found.")
    lead = LEADS_STORE[lead_id]
    score = SCORES_STORE.get(lead_id) or score_lead(lead, SCORING_CONFIG)
    return agent.generate_outreach(lead, score, channel=channel, tone=tone)


@app.post("/api/leads/{lead_id}/agent/cadence", response_model=MultiTouchCadence, tags=["AI Agent"])
def agent_cadence(lead_id: str):
    """Synthesizes a complete 4-step multi-touch outreach cadence across 14 days."""
    if lead_id not in LEADS_STORE:
        raise HTTPException(status_code=404, detail=f"Lead with id '{lead_id}' not found.")
    lead = LEADS_STORE[lead_id]
    score = SCORES_STORE.get(lead_id) or score_lead(lead, SCORING_CONFIG)
    return agent.generate_cadence(lead, score)


@app.post("/api/leads/{lead_id}/agent/opportunity", response_model=OpportunityAnalysis, tags=["AI Agent"])
def agent_opportunity_analysis(lead_id: str):
    if lead_id not in LEADS_STORE:
        raise HTTPException(status_code=404, detail=f"Lead with id '{lead_id}' not found.")
    lead = LEADS_STORE[lead_id]
    score = SCORES_STORE.get(lead_id) or score_lead(lead, SCORING_CONFIG)
    return agent.analyze_opportunity(lead, score)


# ==============================================================================
# RAG Knowledge Base & AI Copilot
# ==============================================================================
@app.get("/api/rag/documents", response_model=List[Dict[str, Any]], tags=["RAG & Knowledge Base"])
def list_knowledge_documents():
    return agent.rag.documents


@app.post("/api/rag/documents", response_model=RetrievedChunk, status_code=status.HTTP_201_CREATED, tags=["RAG & Knowledge Base"])
def add_knowledge_document(payload: AddDocumentRequest):
    """Dynamically adds a custom enterprise case study, battlecard, or spec to RAG."""
    return agent.rag.add_document(payload)


@app.post("/api/rag/query", response_model=RAGQueryResponse, tags=["RAG & Knowledge Base"])
def query_rag_knowledge(payload: RAGQueryRequest):
    result = agent.rag.generate_rag_answer(
        query=payload.query,
        top_k=payload.top_k
    )
    return RAGQueryResponse(
        query=result["query"],
        retrieved_chunks=result["retrieved_chunks"],
        augmented_answer=result["answer"],
        model_name=result["model_name"],
        latency_ms=result["latency_ms"]
    )


@app.post("/api/agent/copilot", response_model=CopilotChatResponse, tags=["AI Agent"])
def sales_copilot(payload: CopilotChatRequest):
    lead_context_str = ""
    if payload.lead_id_context and payload.lead_id_context in LEADS_STORE:
        l = LEADS_STORE[payload.lead_id_context]
        s = SCORES_STORE.get(payload.lead_id_context) or score_lead(l, SCORING_CONFIG)
        lead_context_str = (
            f"Target: {l.company_name} | Industry: {l.industry} | Role: {l.contact_role} | "
            f"Score: {s.total_score}/100 ({s.tier}) | Current CRM: {l.current_crm_or_stack} | "
            f"Pain Points: {', '.join(l.pain_points)}"
        )

    result = agent.answer_copilot_query(
        query=payload.message,
        lead_context=lead_context_str,
        top_k=payload.top_k,
        temperature=payload.temperature,
        custom_system_prompt=payload.custom_system_prompt
    )

    return CopilotChatResponse(
        answer=result["answer"],
        sources_cited=result["retrieved_chunks"],
        model_used=result["model_name"],
        suggested_follow_ups=result.get("suggested_follow_ups", [])
    )


# ==============================================================================
# Business Intelligence & Full Data Export
# ==============================================================================
@app.get("/api/bi/summary", response_model=BISummaryResponse, tags=["Business Intelligence"])
def bi_summary():
    total_leads = len(LEADS_STORE)
    if total_leads == 0:
        return BISummaryResponse(
            total_leads=0,
            total_pipeline_value_usd=0.0,
            average_lead_score=0.0,
            tier_distribution={},
            industry_breakdown={},
            projected_won_revenue_usd=0.0,
            high_priority_count=0,
            conversion_rate_forecast=0.0
        )

    total_pipeline = 0.0
    total_projected_won = 0.0
    scores_sum = 0.0
    tier_dist = {"Tier 1 (Hot)": 0, "Tier 2 (Warm)": 0, "Tier 3 (Cold)": 0, "Disqualified": 0}
    industry_pipeline: Dict[str, float] = {}
    high_priority = 0

    for lead_id, lead in LEADS_STORE.items():
        score = SCORES_STORE.get(lead_id) or score_lead(lead, SCORING_CONFIG)
        total_pipeline += score.estimated_deal_value_usd
        total_projected_won += (score.estimated_deal_value_usd * score.conversion_probability)
        scores_sum += score.total_score

        if "Tier 1" in score.tier:
            tier_dist["Tier 1 (Hot)"] += 1
            high_priority += 1
        elif "Tier 2" in score.tier:
            tier_dist["Tier 2 (Warm)"] += 1
        elif "Tier 3" in score.tier:
            tier_dist["Tier 3 (Cold)"] += 1
        else:
            tier_dist["Disqualified"] += 1

        ind = lead.industry
        industry_pipeline[ind] = industry_pipeline.get(ind, 0.0) + score.estimated_deal_value_usd

    avg_score = round(scores_sum / total_leads, 1)
    overall_conv_forecast = round((total_projected_won / total_pipeline) * 100, 1) if total_pipeline > 0 else 0.0

    return BISummaryResponse(
        total_leads=total_leads,
        total_pipeline_value_usd=round(total_pipeline, 2),
        average_lead_score=avg_score,
        tier_distribution=tier_dist,
        industry_breakdown=industry_pipeline,
        projected_won_revenue_usd=round(total_projected_won, 2),
        high_priority_count=high_priority,
        conversion_rate_forecast=overall_conv_forecast
    )


@app.get("/api/bi/insights", tags=["Business Intelligence"])
def bi_insights():
    leads = list(LEADS_STORE.values())
    pain_freq: Dict[str, int] = {}
    for l in leads:
        for p in l.pain_points:
            pain_freq[p] = pain_freq.get(p, 0) + 1

    sorted_pains = sorted(pain_freq.items(), key=lambda x: x[1], reverse=True)
    return {
        "market_diagnostics": [
            "Inbound triage latency (24-48h) represents the #1 revenue bottleneck across 68% of enterprise prospects.",
            "High intent leads with >4 pricing visits show a 3.4x higher conversion velocity when contacted in <90 seconds.",
            "Mid-market SaaS and Supply Chain accounts present the lowest customer acquisition cost (CAC) and fastest deal cycle."
        ],
        "top_friction_points": [{"pain_point": k, "frequency": v} for k, v in sorted_pains[:5]],
        "recommended_strategic_focus": "Automate SDR inbound qualification immediately for Tier 1 leads to eliminate drop-off."
    }


@app.get("/api/leads/export/json", tags=["Data Export"])
def export_leads_json():
    """Exports all stored leads and their multi-dimensional scores as structured JSON."""
    export_data = []
    for lead_id, lead in LEADS_STORE.items():
        score = SCORES_STORE.get(lead_id) or score_lead(lead, SCORING_CONFIG)
        export_data.append({"lead": lead.dict(), "score": score.dict()})
    return JSONResponse(content=export_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
