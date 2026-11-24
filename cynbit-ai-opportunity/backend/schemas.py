"""
schemas.py - Unconstrained Pydantic Data Models for Cynbit AI Platform
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class EngagementSignals(BaseModel):
    website_visits_30d: int = Field(default=0, ge=0, description="Website visits in last 30 days")
    pricing_page_visits: int = Field(default=0, ge=0, description="Visits to pricing page")
    whitepaper_downloads: List[str] = Field(default_factory=list, description="Downloaded resources")
    webinar_attended: bool = Field(default=False, description="Whether prospect attended a webinar")
    email_open_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Email open rate (0.0 to 1.0)")
    email_click_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Email click rate (0.0 to 1.0)")
    time_on_site_avg_sec: int = Field(default=0, ge=0, description="Average time spent on site in seconds")


class LeadBase(BaseModel):
    company_name: str = Field(..., description="Target prospect company name")
    contact_name: str = Field(..., description="Primary contact full name")
    contact_role: str = Field(..., description="Job title / decision-making capacity")
    contact_email: str = Field(..., description="Business email address")
    industry: str = Field(..., description="Industry sector")
    company_size: str = Field(default="51-200", description="Headcount bracket (e.g., 51-200, 1000+)")
    annual_revenue_usd: float = Field(default=10000000.0, ge=0, description="Estimated annual revenue in USD")
    country: str = Field(default="United States", description="Geographic headquarters")
    website: str = Field(default="https://example.com", description="Company domain")
    lead_source: str = Field(default="Website Inbound", description="Acquisition channel")
    current_crm_or_stack: str = Field(default="HubSpot", description="Current sales & CRM software")
    pain_points: List[str] = Field(default_factory=list, description="Core challenges faced")
    budget_status: str = Field(default="Under Review", description="Budget qualification status")
    purchase_timeline: str = Field(default="1-3 months", description="Expected buying timeline")
    engagement_signals: EngagementSignals = Field(default_factory=EngagementSignals)
    notes: Optional[str] = Field(default="", description="Internal notes or context")


class LeadCreate(LeadBase):
    pass


class Lead(LeadBase):
    lead_id: str = Field(..., description="Unique alphanumeric lead identifier")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ScoringWeightsConfig(BaseModel):
    firmo_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    auth_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    behav_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    budget_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    tier_1_min: float = Field(default=80.0, ge=0.0, le=100.0)
    tier_2_min: float = Field(default=60.0, ge=0.0, le=100.0)
    tier_3_min: float = Field(default=40.0, ge=0.0, le=100.0)


class ScoreBreakdown(BaseModel):
    lead_id: str
    firmographic_score: float = Field(..., ge=0, le=100)
    authority_score: float = Field(..., ge=0, le=100)
    behavioral_score: float = Field(..., ge=0, le=100)
    budget_score: float = Field(..., ge=0, le=100)
    total_score: float = Field(..., ge=0, le=100)
    tier: str
    icp_fit_percentage: float = Field(..., ge=0, le=100)
    estimated_deal_value_usd: float
    conversion_probability: float = Field(..., ge=0, le=1.0)
    scoring_factors: List[str] = Field(default_factory=list)
    recommended_action: str
    scored_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ScoredLead(BaseModel):
    lead: Lead
    score: ScoreBreakdown


class AgentDecision(BaseModel):
    lead_id: str
    decision: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning_trace: List[str]
    action_plan: List[str]
    urgency: str
    synthesized_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class OutreachDraft(BaseModel):
    lead_id: str
    channel: str = Field(default="Email")
    subject_line: Optional[str] = None
    body_content: str
    tone: str = Field(default="Strategic & Consultative")
    value_props_highlighted: List[str] = Field(default_factory=list)
    suggested_follow_up_days: int = Field(default=3)


class CadenceStep(BaseModel):
    step_number: int
    day_offset: int
    channel: str
    subject_line: Optional[str] = None
    content: str
    goal: str


class MultiTouchCadence(BaseModel):
    lead_id: str
    company_name: str
    steps: List[CadenceStep]
    total_duration_days: int = 14


class OpportunityAnalysis(BaseModel):
    lead_id: str
    company_name: str
    strategic_fit_summary: str
    potential_deal_size_usd: float
    conversion_timeframe: str
    key_pain_points_addressed: List[str]
    cynbit_solution_mapping: str
    competitive_differentiators: List[str]
    risk_assessment: str
    projected_roi_multiple: str


class BISummaryResponse(BaseModel):
    total_leads: int
    total_pipeline_value_usd: float
    average_lead_score: float
    tier_distribution: Dict[str, int]
    industry_breakdown: Dict[str, float]
    projected_won_revenue_usd: float
    high_priority_count: int
    conversion_rate_forecast: float


class RetrievedChunk(BaseModel):
    doc_id: str
    title: str
    category: str
    industry: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    content: str
    metrics: Dict[str, Any] = Field(default_factory=dict)


class AddDocumentRequest(BaseModel):
    title: str
    category: str = Field(default="Case Studies")
    industry: str = Field(default="Cross-Industry")
    keywords: List[str] = Field(default_factory=list)
    content: str
    metrics: Dict[str, Any] = Field(default_factory=dict)


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=25)
    filter_category: Optional[str] = None
    filter_industry: Optional[str] = None
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)


class RAGQueryResponse(BaseModel):
    query: str
    retrieved_chunks: List[RetrievedChunk]
    augmented_answer: str
    model_name: str
    latency_ms: float


class CopilotChatRequest(BaseModel):
    message: str
    lead_id_context: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=15)
    temperature: float = Field(default=0.7, ge=0.0, le=1.5)
    custom_system_prompt: Optional[str] = None


class CopilotChatResponse(BaseModel):
    answer: str
    sources_cited: List[RetrievedChunk]
    model_used: str
    suggested_follow_ups: List[str]
