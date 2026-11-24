"""
lead_scoring.py - Adaptive, Configurable & Predictive Lead Scoring Engine
Cynbit AI Business Intelligence & Lead Automation
"""

import re
from typing import Tuple, List, Dict, Optional
from .schemas import Lead, ScoreBreakdown, ScoringWeightsConfig

HIGH_ICP_INDUSTRIES = [
    "supply chain & logistics", "cloud infrastructure saas", "healthcare & medtech",
    "fintech & payments", "cybersecurity", "travel & hospitality saas", "venture capital & private equity"
]

MEDIUM_ICP_INDUSTRIES = [
    "industrial manufacturing", "renewable energy & utilities", "e-commerce & retail",
    "b2b services", "telecom", "aerospace", "enterprise software", "data analytics"
]

DISQUALIFIED_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "mailinator.com", "tempmail.com"]

# Default system configuration
DEFAULT_CONFIG = ScoringWeightsConfig()


def calculate_firmographic_score(lead: Lead) -> Tuple[float, List[str]]:
    """Calculates firmographic score (0-100) adaptively."""
    score = 0.0
    factors = []
    
    # 1. Industry Affinity (Adaptive matching)
    ind = lead.industry.lower()
    if any(target in ind for target in HIGH_ICP_INDUSTRIES):
        score += 40
        factors.append(f"+40 High-affinity ICP industry: {lead.industry}")
    elif any(target in ind for target in MEDIUM_ICP_INDUSTRIES):
        score += 30
        factors.append(f"+30 Commercial industry: {lead.industry}")
    elif any(k in ind for k in ["tech", "software", "digital", "data", "ai", "cloud", "platform", "media"]):
        score += 35
        factors.append(f"+35 Technology-aligned sector: {lead.industry}")
    elif "education" in ind or "personal" in ind or "student" in ind:
        score += 5
        factors.append(f"-35 Non-commercial industry: {lead.industry}")
    else:
        score += 24
        factors.append(f"+24 General commercial sector: {lead.industry}")

    # 2. Company Size Fit (Flexible parsing)
    size = str(lead.company_size).strip()
    if any(s in size for s in ["51-200", "201-500", "100-250", "250-500"]):
        score += 30
        factors.append(f"+30 Sweet spot company scale ({size} employees)")
    elif any(s in size for s in ["501-1000", "1000+", "1000-5000", "5000+"]):
        score += 28
        factors.append(f"+28 Enterprise organization scale ({size} employees)")
    elif any(s in size for s in ["11-50", "20-50"]):
        score += 22
        factors.append(f"+22 Growth-stage company scale ({size} employees)")
    else:
        score += 10
        factors.append(f"+10 Early-stage company scale ({size} employees)")

    # 3. Annual Revenue Fit (Continuous curve)
    rev = lead.annual_revenue_usd
    if rev >= 50_000_000:
        score += 30
        factors.append(f"+30 Enterprise revenue: ${rev:,.0f}/yr")
    elif rev >= 15_000_000:
        score += 26
        factors.append(f"+26 Upper mid-market revenue: ${rev:,.0f}/yr")
    elif rev >= 5_000_000:
        score += 22
        factors.append(f"+22 Mid-market revenue: ${rev:,.0f}/yr")
    elif rev >= 1_000_000:
        score += 16
        factors.append(f"+16 Growth-stage revenue: ${rev:,.0f}/yr")
    elif rev >= 100_000:
        score += 10
        factors.append(f"+10 Seed revenue: ${rev:,.0f}/yr")
    else:
        score += 3
        factors.append(f"-15 Sub-scale commercial revenue: ${rev:,.0f}/yr")

    return min(100.0, max(0.0, score)), factors


def calculate_authority_score(lead: Lead) -> Tuple[float, List[str]]:
    """Calculates decision-maker authority score (0-100) based on title seniority."""
    role = lead.contact_role.lower()
    score = 0.0
    factors = []

    if any(k in role for k in ["ceo", "chief", "cto", "cro", "cco", "coo", "cmo", "cfo", "founder", "co-founder", "president"]):
        score = 100.0
        factors.append(f"+100 Executive C-Suite authority ({lead.contact_role})")
    elif any(k in role for k in ["vp", "vice president", "head of", "partner", "general manager"]):
        score = 88.0
        factors.append(f"+88 Department leadership authority ({lead.contact_role})")
    elif "director" in role:
        score = 78.0
        factors.append(f"+78 Director-level buying authority ({lead.contact_role})")
    elif any(k in role for k in ["manager", "lead", "supervisor"]):
        score = 60.0
        factors.append(f"+60 Operational management influence ({lead.contact_role})")
    elif any(k in role for k in ["specialist", "engineer", "analyst", "representative", "coordinator"]):
        score = 40.0
        factors.append(f"+40 Individual contributor role ({lead.contact_role})")
    elif any(k in role for k in ["intern", "student", "fellow", "assistant"]):
        score = 8.0
        factors.append(f"-70 Academic / non-buyer role ({lead.contact_role})")
    else:
        score = 50.0
        factors.append(f"+50 Commercial stakeholder role ({lead.contact_role})")

    domain = lead.contact_email.split("@")[-1].lower() if "@" in lead.contact_email else ""
    if domain in DISQUALIFIED_DOMAINS:
        score = max(5.0, score - 35.0)
        factors.append(f"-35 Non-corporate email provider ({domain})")
    else:
        factors.append(f"+Corporate verified email domain ({domain})")

    return min(100.0, max(0.0, score)), factors


def calculate_behavioral_score(lead: Lead) -> Tuple[float, List[str]]:
    """Calculates engagement and buying intent score (0-100)."""
    signals = lead.engagement_signals
    score = 0.0
    factors = []

    # 1. Pricing Page Visits
    pv = signals.pricing_page_visits
    if pv >= 5:
        score += 35
        factors.append(f"+35 Intense commercial intent: {pv} pricing page visits")
    elif pv >= 2:
        score += 26
        factors.append(f"+26 Active commercial evaluation: {pv} pricing page visits")
    elif pv >= 1:
        score += 16
        factors.append(f"+16 Explored pricing page: {pv} visit")

    # 2. General Website Visits (30d)
    wv = signals.website_visits_30d
    if wv >= 20:
        score += 25
        factors.append(f"+25 High engagement: {wv} visits in 30 days")
    elif wv >= 10:
        score += 18
        factors.append(f"+18 Active visitor: {wv} visits in 30 days")
    elif wv >= 3:
        score += 10
        factors.append(f"+10 Moderate visits: {wv} visits in 30 days")
    elif wv >= 1:
        score += 5

    # 3. Webinar Attendance
    if signals.webinar_attended:
        score += 15
        factors.append("+15 Attended live product/architecture webinar")

    # 4. Whitepaper Downloads
    downloads_count = len(signals.whitepaper_downloads)
    if downloads_count >= 2:
        score += 15
        factors.append(f"+15 High content engagement: {downloads_count} whitepapers downloaded")
    elif downloads_count == 1:
        score += 10
        factors.append(f"+10 Downloaded technical whitepaper: {signals.whitepaper_downloads[0]}")

    # 5. Email Engagement
    if signals.email_open_rate >= 0.70:
        score += 5
        factors.append(f"+5 High email open rate: {signals.email_open_rate * 100:.0f}%")
    if signals.email_click_rate >= 0.30:
        score += 5
        factors.append(f"+5 High email CTR: {signals.email_click_rate * 100:.0f}%")

    return min(100.0, max(0.0, score)), factors


def calculate_budget_score(lead: Lead) -> Tuple[float, List[str]]:
    """Calculates budget and timeline urgency score (0-100)."""
    score = 0.0
    factors = []

    b_stat = lead.budget_status.lower()
    if "100k+" in b_stat:
        score += 50
        factors.append("+50 Enterprise tier approved budget ($100k+)")
    elif "50k" in b_stat:
        score += 45
        factors.append("+45 Mid-tier approved budget ($50k-$100k)")
    elif "20k" in b_stat or "exploring" in b_stat:
        score += 32
        factors.append("+32 Active exploration budget ($20k-$50k)")
    elif "review" in b_stat:
        score += 22
        factors.append("+22 Budget currently under procurement review")
    else:
        score += 5
        factors.append("-30 No formal budget allocated")

    timeline = lead.purchase_timeline.lower()
    if "immediate" in timeline or "<1 month" in timeline or "now" in timeline:
        score += 50
        factors.append("+50 Immediate buying timeline (<1 month)")
    elif "1-3 months" in timeline:
        score += 40
        factors.append("+40 High priority timeline (1-3 months)")
    elif "3-6 months" in timeline:
        score += 25
        factors.append("+25 Mid-term timeline (3-6 months)")
    else:
        score += 10
        factors.append("+10 Long-range evaluation timeline (6+ months)")

    return min(100.0, max(0.0, score)), factors


def score_lead(lead: Lead, config: Optional[ScoringWeightsConfig] = None) -> ScoreBreakdown:
    """
    Computes a composite, weighted, multi-dimensional lead score.
    Accepts custom dynamic scoring weights and threshold configurations.
    """
    cfg = config or DEFAULT_CONFIG

    firmo_score, firmo_factors = calculate_firmographic_score(lead)
    auth_score, auth_factors = calculate_authority_score(lead)
    behav_score, behav_factors = calculate_behavioral_score(lead)
    budget_score, budget_factors = calculate_budget_score(lead)

    # Normalize weights if user customizes them
    total_w = cfg.firmo_weight + cfg.auth_weight + cfg.behav_weight + cfg.budget_weight
    if total_w <= 0:
        total_w = 1.0

    w_f = cfg.firmo_weight / total_w
    w_a = cfg.auth_weight / total_w
    w_be = cfg.behav_weight / total_w
    w_bu = cfg.budget_weight / total_w

    composite = (
        w_f * firmo_score +
        w_a * auth_score +
        w_be * behav_score +
        w_bu * budget_score
    )

    # Disqualification Guardrail
    domain = lead.contact_email.split("@")[-1].lower() if "@" in lead.contact_email else ""
    role = lead.contact_role.lower()
    if domain in DISQUALIFIED_DOMAINS and any(k in role for k in ["student", "intern"]):
        composite = min(composite, 25.0)

    composite = round(composite, 1)

    # Dynamic Tier Categorization based on config thresholds
    if composite >= cfg.tier_1_min:
        tier = "Tier 1 - Hot (Immediate Sales Routing)"
        action = "Immediate AE routing; Trigger VIP autonomous calendar booking & custom enterprise brief."
        prob = min(0.90, 0.45 + (composite - cfg.tier_1_min) * 0.02)
    elif composite >= cfg.tier_2_min:
        tier = "Tier 2 - Warm (Automated Agent Nurturing)"
        action = "Autonomous Agent Nurture: dispatch tailored industry case studies and ROI calculator link."
        prob = round(0.25 + (composite - cfg.tier_2_min) * 0.01, 2)
    elif composite >= cfg.tier_3_min:
        tier = "Tier 3 - Cold (Drip Marketing Campaign)"
        action = "Enroll in bi-weekly educational newsletter & webinar invitation track."
        prob = round(0.08 + (composite - cfg.tier_3_min) * 0.007, 2)
    else:
        tier = "Disqualified (Low ICP Fit)"
        action = "Auto-archive lead; suppress sales rep outreach to preserve team bandwidth."
        prob = 0.02

    # Estimated Deal Value Projection
    base_deal_value = 24_000.0
    size = str(lead.company_size)
    if "501-1000" in size or "1000+" in size or lead.annual_revenue_usd >= 50_000_000:
        deal_value = 96_000.0
    elif "201-500" in size or lead.annual_revenue_usd >= 20_000_000:
        deal_value = 60_000.0
    elif "51-200" in size or lead.annual_revenue_usd >= 10_000_000:
        deal_value = 36_000.0
    else:
        deal_value = base_deal_value

    if "100k+" in lead.budget_status:
        deal_value = max(deal_value, 110_000.0)
    elif "50k-100k" in lead.budget_status:
        deal_value = max(deal_value, 65_000.0)

    icp_fit = round((firmo_score * 0.55 + auth_score * 0.45), 1)

    all_factors = (
        firmo_factors[:2] +
        auth_factors[:1] +
        behav_factors[:2] +
        budget_factors[:2]
    )

    return ScoreBreakdown(
        lead_id=lead.lead_id,
        firmographic_score=round(firmo_score, 1),
        authority_score=round(auth_score, 1),
        behavioral_score=round(behav_score, 1),
        budget_score=round(budget_score, 1),
        total_score=composite,
        tier=tier,
        icp_fit_percentage=icp_fit,
        estimated_deal_value_usd=round(deal_value, 2),
        conversion_probability=round(prob, 2),
        scoring_factors=all_factors,
        recommended_action=action
    )
