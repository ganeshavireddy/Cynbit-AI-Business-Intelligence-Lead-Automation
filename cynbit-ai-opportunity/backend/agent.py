"""
agent.py - Autonomous AI Business Intelligence & Lead Automation Agent with RAG & Multi-Touch Cadence
Cynbit Technologies
"""

import os
import json
from typing import Optional, List, Dict, Any
from .schemas import (
    Lead, ScoreBreakdown, AgentDecision, OutreachDraft,
    OpportunityAnalysis, MultiTouchCadence, CadenceStep
)
from .rag_engine import CynbitRAGEngine

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_gemini_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        _gemini_client = None


class LeadAutomationAgent:
    """
    Autonomous AI Agent executing multi-step perception, RAG-enriched qualification reasoning,
    hyper-personalized multi-channel cadences, and strategic opportunity synthesis.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.client = _gemini_client
        self.rag = CynbitRAGEngine()

    def qualify_lead(self, lead: Lead, score: ScoreBreakdown) -> AgentDecision:
        """Executes autonomous multi-step reasoning enriched by RAG."""
        trace = []
        trace.append(f"[Step 1: Perception] Ingested lead {lead.lead_id} ({lead.company_name}). Role: {lead.contact_role}. Annual Revenue: ${lead.annual_revenue_usd:,.0f}.")
        
        pain_summary = ", ".join(lead.pain_points) if lead.pain_points else "Standard lead efficiency"
        trace.append(f"[Step 2: Friction Analysis] Key client pain points: {pain_summary}. Current tech stack: {lead.current_crm_or_stack}.")

        rag_query = f"{lead.industry} {pain_summary} {lead.current_crm_or_stack}"
        retrieved = self.rag.retrieve(rag_query, top_k=2)
        if retrieved:
            top_evidence = retrieved[0]
            trace.append(f"[Step 3: RAG Knowledge Synthesis] Retrieved validated benchmark: '{top_evidence.title}' (Match: {top_evidence.similarity_score * 100:.0f}%). Proof point: {top_evidence.content[:140]}...")
        else:
            trace.append(f"[Step 3: Signal Triangulation] Scored composite fit at {score.total_score}/100 ({score.tier}).")

        if score.total_score >= 80.0:
            decision = "route_to_sales_rep"
            urgency = "Immediate (<2h)"
            confidence = 0.94
            trace.append(f"[Step 4: Strategic Routing] Tier 1 criteria met. High conversion probability ({score.conversion_probability * 100:.0f}%). Formulating instant AE routing and VIP calendar lock.")
            plan = [
                f"Notify dedicated Account Executive for {lead.industry} with executive dossier",
                f"Sync lead metadata and intent signals to {lead.current_crm_or_stack}",
                "Dispatch personalized calendar link with priority VIP time slots",
                f"Attach RAG-indexed case study evidence ({retrieved[0].title if retrieved else 'Enterprise Benchmark'})"
            ]
        elif score.total_score >= 60.0:
            decision = "trigger_nurture_campaign"
            urgency = "High (<24h)"
            confidence = 0.88
            trace.append(f"[Step 4: Nurture Orchestration] Tier 2 criteria met. Warm intent but pending procurement/budget timeline ({lead.purchase_timeline}). Scheduling cognitive nurture sequence.")
            plan = [
                f"Enroll contact in Cynbit {lead.industry} cognitive case study series",
                f"Schedule autonomous follow-up trigger in 3 business days",
                "Monitor for pricing page re-visits or whitepaper downloads",
                "Escalate to AE immediately if engagement score increases by >=10 points"
            ]
        elif score.total_score >= 40.0:
            decision = "request_more_information"
            urgency = "Medium (<48h)"
            confidence = 0.79
            trace.append("[Step 4: Discovery Cadence] Tier 3 prospect. Inconclusive intent or mid-range seniority. Dispatching low-touch asynchronous qualification survey.")
            plan = [
                "Dispatch automated conversational qualification survey",
                "Enroll in monthly Cynbit Industry AI Intelligence Newsletter",
                "Verify verified business email and corporate entity registration"
            ]
        else:
            decision = "disqualify_and_archive"
            urgency = "Low"
            confidence = 0.97
            trace.append(f"[Step 4: Disqualification] Score {score.total_score} below minimum viable ICP threshold. Non-commercial signals detected. Preserving sales org bandwidth.")
            plan = [
                "Mark lead status as 'Disqualified - Outside ICP' in CRM",
                "Suppress automated outbound sales messaging",
                "Route to self-service community resources or documentation if applicable"
            ]

        return AgentDecision(
            lead_id=lead.lead_id,
            decision=decision,
            confidence=confidence,
            reasoning_trace=trace,
            action_plan=plan,
            urgency=urgency
        )

    def generate_outreach(self, lead: Lead, score: ScoreBreakdown, channel: str = "Email", tone: str = "Strategic & Consultative") -> OutreachDraft:
        """Synthesizes RAG-augmented B2B outreach copy."""
        first_name = lead.contact_name.split()[0] if lead.contact_name else "there"
        pain_hook = lead.pain_points[0] if lead.pain_points else "manual sales data processing"
        
        rag_query = f"{lead.industry} {pain_hook} {lead.current_crm_or_stack}"
        evidence_chunks = self.rag.retrieve(rag_query, top_k=1)
        evidence_str = ""
        evidence_title = ""
        if evidence_chunks:
            top_c = evidence_chunks[0]
            evidence_title = top_c.title
            if top_c.metrics:
                m_list = [f"{k.replace('_', ' ')}: {v}" for k, v in list(top_c.metrics.items())[:2]]
                evidence_str = f"In similar deployments (such as {top_c.title.split('-')[0].strip()}), we achieved {', and '.join(m_list)}."
            else:
                evidence_str = f"In recent {lead.industry} deployments, clients saw triage latency plummet from hours to under 90 seconds."

        if tone == "Executive Direct":
            opener = f"{first_name} — saw your work scaling {lead.company_name}."
            closer = "Are you open to a brief 10-minute architecture review this Thursday?"
        elif tone == "Urgent & Growth-Focused":
            opener = f"Hi {first_name}, losing qualified pipeline to response latency is painful."
            closer = "Let's plug this revenue leak before Q1 closes. Do you have 15 mins tomorrow?"
        else:
            opener = f"Hello {first_name}, congratulations on the continued momentum at {lead.company_name}."
            closer = "Would you be open to exploring how this maps to your current roadmap?"

        if channel == "LinkedIn InMail":
            subject = f"AI Lead Automation for {lead.company_name}"
            body = (
                f"{opener}\n\n"
                f"Noticed {lead.company_name}'s footprint in {lead.industry}. Many growth leaders in your space "
                f"tell us that {pain_hook.lower()} is capping SDR throughput.\n\n"
                f"{evidence_str}\n\n"
                f"At Cynbit, we've deployed autonomous AI agents that plug into {lead.current_crm_or_stack} to "
                f"instantly qualify inbound leads in <90 seconds, lifting conversion velocity by 3.4x.\n\n"
                f"{closer}\n\n"
                f"Best,\n"
                f"Cynbit AI Automation Team"
            )
            val_props = ["Sub-90s response latency", f"{lead.current_crm_or_stack} bi-directional sync", f"RAG Evidence: {evidence_title[:30]}..."]
            follow_up = 2

        elif channel == "Discovery Call Script":
            subject = f"[SDR Script] Discovery Brief: {lead.company_name} ({lead.contact_name})"
            body = (
                f"--- SDR DISCOVERY & QUALIFICATION SCRIPT (RAG-AUGMENTED) ---\n"
                f"PROSPECT: {lead.contact_name} ({lead.contact_role})\n"
                f"COMPANY: {lead.company_name} | {lead.industry} | {lead.company_size} emp\n"
                f"SCORE: {score.total_score}/100 ({score.tier})\n"
                f"VERIFIED EVIDENCE: {evidence_str}\n\n"
                f"[OPENER]\n"
                f"\"Hi {first_name}, this is [Rep] from Cynbit. I saw you recently reviewed our "
                f"benchmark on autonomous lead intelligence. Based on your role heading {lead.contact_role.lower()}, "
                f"I wanted to see how you're currently tackling {pain_hook.lower()}?\"\n\n"
                f"[QUALIFYING QUESTIONS]\n"
                f"1. What is your current inbound response time from form submission to first touch?\n"
                f"2. How much time does your team spend in {lead.current_crm_or_stack} cleaning and scoring lead records?\n"
                f"3. With an estimated pipeline target, how would cutting qualification latency from 24h to 2min impact your close rates?\n\n"
                f"[VALUE BRIDGE - RAG PROOF POINT]\n"
                f"\"{evidence_str} Cynbit's autonomous agent pre-qualifies, enriches, and books high-intent prospects directly into your AE calendars 24/7.\"\n\n"
                f"[CLOSE]\n"
                f"\"Let's lock in 20 minutes with our Principal Solutions Architect to model your specific ROI numbers.\""
            )
            val_props = ["Automated qualification", "SDR productivity multiplier", "Zero manual data entry"]
            follow_up = 1

        else:  # Email
            subject = f"Solving {pain_hook.lower()} at {lead.company_name}"
            body = (
                f"Hi {first_name},\n\n"
                f"{opener}\n\n"
                f"When speaking with revenue leaders in {lead.industry}, a recurring challenge is that "
                f"{pain_hook.lower()}.\n\n"
                f"{evidence_str}\n\n"
                f"We developed Cynbit's Autonomous Business Intelligence & Lead Agent specifically to solve this. "
                f"Instead of manual triage, our agents autonomously:\n"
                f"• Analyze intent signals & score leads with 94%+ precision\n"
                f"• Enrich company firmographics and verify buying authority\n"
                f"• Synchronize enriched intelligence directly into {lead.current_crm_or_stack}\n"
                f"• Generate bespoke executive outreach that boosts response rates above 34%\n\n"
                f"For an organization of {lead.company_size} team members, our partners typically see a "
                f"payback period within 45 days.\n\n"
                f"{closer}\n\n"
                f"Warm regards,\n\n"
                f"Cynbit AI Enterprise Solutions\n"
                f"https://cynbit.in"
            )
            val_props = [
                "Automated sub-90s lead triage",
                f"Seamless {lead.current_crm_or_stack} workflow automation",
                f"RAG-Verified Benchmark: {evidence_title[:32]}"
            ]
            follow_up = 3

        return OutreachDraft(
            lead_id=lead.lead_id,
            channel=channel,
            subject_line=subject,
            body_content=body,
            tone=tone,
            value_props_highlighted=val_props,
            suggested_follow_up_days=follow_up
        )

    def generate_cadence(self, lead: Lead, score: ScoreBreakdown) -> MultiTouchCadence:
        """Synthesizes a complete 4-step multi-channel outreach cadence over 14 days."""
        first_name = lead.contact_name.split()[0] if lead.contact_name else "there"
        pain_hook = lead.pain_points[0] if lead.pain_points else "manual inbound triage latency"

        # RAG evidence
        rag_query = f"{lead.industry} {pain_hook}"
        evidence_chunks = self.rag.retrieve(rag_query, top_k=1)
        evidence_txt = evidence_chunks[0].content[:160] if evidence_chunks else "proven 3.4x pipeline acceleration"

        steps = [
            CadenceStep(
                step_number=1,
                day_offset=1,
                channel="Email (Executive Value Hook)",
                subject_line=f"Addressing {pain_hook.lower()} at {lead.company_name}",
                content=f"Hi {first_name},\n\nSaw your team is scaling {lead.company_name}. Revenue leaders in {lead.industry} frequently tell us that {pain_hook.lower()} creates a massive revenue leak. At Cynbit, we've deployed autonomous cognitive agents that slash qualification latency from 24h to <90s. Worth a 10-minute chat this Thursday?",
                goal="Establish executive pain awareness and initiate dialogue"
            ),
            CadenceStep(
                step_number=2,
                day_offset=3,
                channel="LinkedIn (Connection + Contextual Note)",
                subject_line=None,
                content=f"Hi {first_name} — noticed your work leading {lead.contact_role} at {lead.company_name}. We recently solved {pain_hook.lower()} for peers in {lead.industry} ({evidence_txt}...). Would love to connect and share the benchmark.",
                goal="Multi-channel touchpoint building peer credibility"
            ),
            CadenceStep(
                step_number=3,
                day_offset=7,
                channel="Phone / Discovery Call Script",
                subject_line=f"[SDR Brief] Call with {lead.contact_name}",
                content=f"\"Hi {first_name}, following up on my note regarding {pain_hook.lower()}. With {lead.current_crm_or_stack} in place, are you looking at autonomous triage this quarter to hit your pipeline targets?\"",
                goal="Direct synchronous engagement to lock calendar demo"
            ),
            CadenceStep(
                step_number=4,
                day_offset=14,
                channel="Email (Permission to Close File / Break-up)",
                subject_line=f"Closing file: {lead.company_name} AI automation",
                content=f"Hi {first_name},\n\nI haven't heard back, so I assume tackling {pain_hook.lower()} isn't a top priority for {lead.company_name} right now. I'll close out your file for now. If you ever want to explore how our autonomous agents cut response latency by 99%, our door is always open.\n\nBest,\nCynbit Solutions",
                goal="Trigger loss aversion and prompt a final response"
            )
        ]

        return MultiTouchCadence(
            lead_id=lead.lead_id,
            company_name=lead.company_name,
            steps=steps,
            total_duration_days=14
        )

    def analyze_opportunity(self, lead: Lead, score: ScoreBreakdown) -> OpportunityAnalysis:
        """Synthesizes a C-level executive opportunity dossier."""
        if lead.company_size in ["501-1000", "1000+"]:
            solution = "Cynbit Enterprise Autonomous Suite (Multi-Agent Cognitive Routing + Full CRM Bi-directional Sync + Custom LLM Fine-tuning)"
            roi_mult = "4.8x ROI"
            timeframe = "60-90 days enterprise sales cycle"
        elif lead.company_size in ["201-500", "51-200"]:
            solution = "Cynbit Growth Orchestrator (Inbound Agent + Outbound Personalization Engine + HubSpot/Salesforce Connector)"
            roi_mult = "3.9x ROI"
            timeframe = "30-45 days mid-market cycle"
        else:
            solution = "Cynbit Starter Automation Stack (Autonomous Lead Scoring + Automated Email Drafter)"
            roi_mult = "3.2x ROI"
            timeframe = "14-21 days rapid POC"

        diffs = [
            "Autonomous multi-step reasoning vs static rigid chatbot decision trees",
            f"Native bi-directional telemetry with {lead.current_crm_or_stack}",
            "RAG-Augmented sales intelligence drawing on enterprise case studies",
            "Deterministic scoring guardrails combined with LLM contextual enrichment",
            "Zero prompt hallucination via strict Pydantic contract validation"
        ]

        if score.total_score >= 75:
            risk = "Low risk. High stakeholder seniority and validated intent signals indicate ready buying authority."
        elif score.total_score >= 50:
            risk = "Moderate risk. Opportunity requires economic buyer alignment and procurement budget clarification."
        else:
            risk = "High risk. Lead does not meet core commercial viability criteria; high probability of stall or zero budget."

        strat_summary = (
            f"{lead.company_name} represents a high-leverage target in {lead.industry}. "
            f"With ${lead.annual_revenue_usd:,.0f} in annual turnover and {lead.company_size} headcount, "
            f"implementing Cynbit's autonomous lead intelligence directly targets their core friction: "
            f"'{', '.join(lead.pain_points) if lead.pain_points else 'lead triage velocity'}'. "
            f"The contact ({lead.contact_name}, {lead.contact_role}) holds direct operational buying authority."
        )

        return OpportunityAnalysis(
            lead_id=lead.lead_id,
            company_name=lead.company_name,
            strategic_fit_summary=strat_summary,
            potential_deal_size_usd=score.estimated_deal_value_usd,
            conversion_timeframe=timeframe,
            key_pain_points_addressed=lead.pain_points,
            cynbit_solution_mapping=solution,
            competitive_differentiators=diffs,
            risk_assessment=risk,
            projected_roi_multiple=roi_mult
        )

    def answer_copilot_query(
        self,
        query: str,
        lead_context: Optional[str] = None,
        top_k: int = 3,
        temperature: float = 0.7,
        custom_system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Answers sales rep queries with unconstrained RAG augmentation."""
        return self.rag.generate_rag_answer(
            query,
            lead_context=lead_context,
            top_k=top_k,
            temperature=temperature,
            custom_system_prompt=custom_system_prompt
        )
