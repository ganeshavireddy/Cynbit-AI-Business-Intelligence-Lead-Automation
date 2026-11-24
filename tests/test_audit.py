import requests
import json

BASE = "http://127.0.0.1:8000"
results = []

def record(name, status, err=None):
    results.append({"test": name, "status": status, "error": err})
    icon = "✅" if status == "PASS" else "❌"
    print(f"{icon} [{status}] {name}" + (f": {err}" if err else ""))

def run():
    # 1. Health
    try:
        r = requests.get(f"{BASE}/")
        assert r.status_code == 200
        assert "service" in r.json()
        record("Root Health Check", "PASS")
    except Exception as e:
        record("Root Health Check", "FAIL", str(e))

    # 2. List Leads
    try:
        r = requests.get(f"{BASE}/api/leads")
        assert r.status_code == 200
        leads = r.json()
        assert len(leads) > 0
        record("List & Filter Leads", "PASS")
    except Exception as e:
        record("List & Filter Leads", "FAIL", str(e))

    active_id = leads[0]["lead"]["lead_id"]

    # 3. Get Single Lead
    try:
        r = requests.get(f"{BASE}/api/leads/{active_id}")
        assert r.status_code == 200
        assert r.json()["lead"]["lead_id"] == active_id
        record(f"Get Single Lead ({active_id})", "PASS")
    except Exception as e:
        record(f"Get Single Lead ({active_id})", "FAIL", str(e))

    # 4. Create Lead
    try:
        payload = {
            "company_name": "Audit BioSystems",
            "contact_name": "Dr. Alan Grant",
            "contact_role": "VP Clinical Ops",
            "contact_email": "alan@auditbio.com",
            "industry": "Healthcare & MedTech",
            "company_size": "201-500",
            "annual_revenue_usd": 65000000,
            "country": "United States",
            "current_crm_or_stack": "HubSpot",
            "budget_status": "Approved ($100k+)",
            "purchase_timeline": "Immediate (<1 month)",
            "pain_points": ["HIPAA compliance validation delays"],
            "engagement_signals": {"website_visits_30d": 30, "pricing_page_visits": 8, "webinar_attended": True}
        }
        r = requests.post(f"{BASE}/api/leads", json=payload)
        assert r.status_code == 201
        assert r.json()["score"]["total_score"] > 80
        record("Create Single Lead & 4-Pillar Scoring", "PASS")
    except Exception as e:
        record("Create Single Lead & 4-Pillar Scoring", "FAIL", str(e))

    # 5. Bulk Ingestion
    try:
        batch = [{
            "company_name": f"BatchCo {i}",
            "contact_name": f"Exec {i}",
            "contact_role": "Director",
            "contact_email": f"exec{i}@batchco.com",
            "industry": "Supply Chain & Logistics",
            "annual_revenue_usd": 35000000,
            "budget_status": "Approved ($50k-$100k)",
            "purchase_timeline": "1-3 months",
            "current_crm_or_stack": "Salesforce",
            "pain_points": ["Triage delay"],
            "engagement_signals": {"website_visits_30d": 15, "pricing_page_visits": 3}
        } for i in range(2)]
        r = requests.post(f"{BASE}/api/leads/bulk", json=batch)
        assert r.status_code == 201
        assert len(r.json()) == 2
        record("Bulk Lead Ingestion", "PASS")
    except Exception as e:
        record("Bulk Lead Ingestion", "FAIL", str(e))

    # 6. Dynamic Weights Calibration
    try:
        r = requests.get(f"{BASE}/api/scoring/config")
        assert r.status_code == 200
        cfg = r.json()
        cfg["firmo_weight"] = 0.30
        cfg["auth_weight"] = 0.25
        cfg["behav_weight"] = 0.25
        cfg["budget_weight"] = 0.20
        r_post = requests.post(f"{BASE}/api/scoring/config", json=cfg)
        assert r_post.status_code == 200
        assert r_post.json()["firmo_weight"] == 0.30
        record("Dynamic Weights Calibration", "PASS")
    except Exception as e:
        record("Dynamic Weights Calibration", "FAIL", str(e))

    # 7. Agent Qualify
    try:
        r = requests.post(f"{BASE}/api/leads/{active_id}/agent/qualify")
        assert r.status_code == 200
        res = r.json()
        assert len(res["reasoning_trace"]) > 0
        assert len(res["action_plan"]) > 0
        record("Agent Autonomous Qualify Reasoning", "PASS")
    except Exception as e:
        record("Agent Autonomous Qualify Reasoning", "FAIL", str(e))

    # 8. Agent Outreach
    try:
        r = requests.post(f"{BASE}/api/leads/{active_id}/agent/outreach?channel=Email&tone=Strategic")
        assert r.status_code == 200
        assert len(r.json()["body_content"]) > 50
        record("Agent Outreach Copy Synthesis", "PASS")
    except Exception as e:
        record("Agent Outreach Copy Synthesis", "FAIL", str(e))

    # 9. 14-Day Cadence
    try:
        r = requests.post(f"{BASE}/api/leads/{active_id}/agent/cadence")
        assert r.status_code == 200
        cad = r.json()
        assert len(cad["steps"]) == 4
        assert cad["total_duration_days"] == 14
        record("14-Day Multi-Touch Cadence Generation", "PASS")
    except Exception as e:
        record("14-Day Multi-Touch Cadence Generation", "FAIL", str(e))

    # 10. Opportunity Analysis
    try:
        r = requests.post(f"{BASE}/api/leads/{active_id}/agent/opportunity")
        assert r.status_code == 200
        opp = r.json()
        assert opp["potential_deal_size_usd"] > 0
        record("Executive Opportunity Dossier Analysis", "PASS")
    except Exception as e:
        record("Executive Opportunity Dossier Analysis", "FAIL", str(e))

    # 11. RAG Documents & Query
    try:
        r = requests.get(f"{BASE}/api/rag/documents")
        assert r.status_code == 200
        assert len(r.json()) >= 12
        rq = requests.post(f"{BASE}/api/rag/query", json={"query": "Apex Logistics Salesforce", "top_k": 3})
        assert rq.status_code == 200
        assert len(rq.json()) > 0
        record("RAG Knowledge Documents & Semantic Query", "PASS")
    except Exception as e:
        record("RAG Knowledge Documents & Semantic Query", "FAIL", str(e))

    # 12. Copilot Chat
    try:
        r = requests.post(f"{BASE}/api/agent/copilot", json={"message": "What is Cynbit data security policy?", "top_k": 3})
        assert r.status_code == 200
        res = r.json()
        assert "Zero Data Retention" in res["answer"] or "encryption" in res["answer"].lower()
        record("AI Sales Copilot RAG Grounded Chat", "PASS")
    except Exception as e:
        record("AI Sales Copilot RAG Grounded Chat", "FAIL", str(e))

    # 13. BI Summary, Insights, Export
    try:
        rs = requests.get(f"{BASE}/api/bi/summary")
        assert rs.status_code == 200
        ri = requests.get(f"{BASE}/api/bi/insights")
        assert ri.status_code == 200
        re = requests.get(f"{BASE}/api/leads/export/json")
        assert re.status_code == 200
        record("BI Summary, Insights & Full JSON Export", "PASS")
    except Exception as e:
        record("BI Summary, Insights & Full JSON Export", "FAIL", str(e))

    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print(f"\n==========================================")
    print(f"🎯 Backend Audit: {passed}/{total} Tests Passed (100% Pass Rate)" if passed == total else f"❌ {total - passed} Tests Failed")
    print(f"==========================================")

if __name__ == "__main__":
    run()
