"""
rag_engine.py - Unconstrained Retrieval-Augmented Generation (RAG) & Dynamic Vector Engine
Cynbit Technologies
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .schemas import RetrievedChunk, AddDocumentRequest

# Check for LLM API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

_gemini_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        _gemini_client = None


class CynbitRAGEngine:
    """
    Unconstrained Enterprise RAG Engine supporting dynamic document indexing,
    arbitrary top-k retrieval, custom similarity thresholds, and multi-LLM generation.
    """

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.doc_texts: List[str] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_vectors: Optional[np.ndarray] = None
        self.data_file_path: Optional[Path] = None
        self.load_knowledge_base()

    def load_knowledge_base(self):
        """Loads and indexes documents from data/knowledge_base/cynbit_knowledge.json."""
        current_dir = Path(__file__).resolve().parent
        possible_paths = [
            current_dir.parent / "data" / "knowledge_base" / "cynbit_knowledge.json",
            Path("data/knowledge_base/cynbit_knowledge.json"),
            Path("cynbit-ai-opportunity/data/knowledge_base/cynbit_knowledge.json")
        ]

        for p in possible_paths:
            if p.exists():
                self.data_file_path = p
                break

        if self.data_file_path and self.data_file_path.exists():
            try:
                with open(self.data_file_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                self._reindex_vectors()
                print(f"[Cynbit RAG Engine] Indexed {len(self.documents)} enterprise knowledge documents.")
            except Exception as e:
                print(f"[Cynbit RAG Engine] Error loading knowledge base: {e}")
        else:
            print("[Cynbit RAG Engine] Warning: Knowledge base file not found.")

    def _reindex_vectors(self):
        """Recomputes TF-IDF vector matrix across all loaded documents."""
        self.doc_texts = []
        for doc in self.documents:
            combined_text = (
                f"{doc.get('title', '')} "
                f"{doc.get('category', '')} "
                f"{doc.get('industry', '')} "
                f"{' '.join(doc.get('keywords', []))} "
                f"{doc.get('content', '')}"
            )
            self.doc_texts.append(combined_text)

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True
        )
        self.doc_vectors = self.vectorizer.fit_transform(self.doc_texts)

    def add_document(self, req: AddDocumentRequest) -> RetrievedChunk:
        """Dynamically ingests a new document into the knowledge base and reindexes vectors."""
        new_id = f"DOC-{len(self.documents) + 1:03d}"
        doc_dict = {
            "doc_id": new_id,
            "title": req.title,
            "category": req.category,
            "industry": req.industry,
            "keywords": req.keywords,
            "content": req.content,
            "metrics": req.metrics
        }
        self.documents.append(doc_dict)
        self._reindex_vectors()

        # Persist to JSON file
        if self.data_file_path and self.data_file_path.exists():
            try:
                with open(self.data_file_path, "w", encoding="utf-8") as f:
                    json.dump(self.documents, f, indent=2)
            except Exception as e:
                print(f"[Cynbit RAG Engine] Warning: Could not persist document to file: {e}")

        return RetrievedChunk(
            doc_id=new_id,
            title=req.title,
            category=req.category,
            industry=req.industry,
            similarity_score=1.0,
            content=req.content,
            metrics=req.metrics
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_category: Optional[str] = None,
        filter_industry: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[RetrievedChunk]:
        """
        Retrieves top-k semantically matching documents with optional threshold filtering.
        """
        if not self.documents or self.vectorizer is None or self.doc_vectors is None:
            return []

        query_vec = self.vectorizer.transform([query])
        cosine_sims = cosine_similarity(query_vec, self.doc_vectors).flatten()

        query_lower = query.lower()
        scored_docs = []

        for idx, doc in enumerate(self.documents):
            sim_score = float(cosine_sims[idx])

            if filter_category and filter_category.lower() not in doc.get("category", "").lower():
                continue

            if filter_industry and doc.get("industry") != "Cross-Industry":
                if filter_industry.lower() not in doc.get("industry", "").lower():
                    continue

            # Semantic keyword & topic boost
            kw_boost = 0.0
            for kw in doc.get("keywords", []):
                if kw.lower() in query_lower:
                    kw_boost += 0.06

            if doc.get("industry", "").lower() in query_lower:
                kw_boost += 0.10

            final_score = min(1.0, round(sim_score + kw_boost, 3))
            if final_score >= min_similarity:
                scored_docs.append((final_score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc in scored_docs[:top_k]:
            results.append(RetrievedChunk(
                doc_id=doc["doc_id"],
                title=doc["title"],
                category=doc["category"],
                industry=doc["industry"],
                similarity_score=score,
                content=doc["content"],
                metrics=doc.get("metrics", {})
            ))

        return results

    def build_rag_context(self, query: str, top_k: int = 3) -> str:
        """Constructs prompt context from retrieved documents."""
        chunks = self.retrieve(query, top_k=top_k)
        if not chunks:
            return ""

        context_lines = ["\n=== RETRIEVED ENTERPRISE EVIDENCE (RAG) ==="]
        for i, chunk in enumerate(chunks, 1):
            context_lines.append(f"[{i}] {chunk.title} (Match Score: {chunk.similarity_score * 100:.1f}%)")
            context_lines.append(f"Category: {chunk.category} | Industry: {chunk.industry}")
            context_lines.append(f"Content: {chunk.content}")
            if chunk.metrics:
                metrics_str = ", ".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in chunk.metrics.items())
                context_lines.append(f"Verified Metrics: {metrics_str}")
            context_lines.append("")
        return "\n".join(context_lines)

    def generate_rag_answer(
        self,
        query: str,
        lead_context: Optional[str] = None,
        top_k: int = 3,
        temperature: float = 0.7,
        custom_system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates augmented responses using Gemini, OpenAI-compatible endpoint,
        or the built-in Cynbit Cognitive Synthesizer.
        """
        start_time = time.time()
        retrieved_chunks = self.retrieve(query, top_k=top_k)
        rag_context = self.build_rag_context(query, top_k=top_k)

        base_system = custom_system_prompt or (
            "You are the Cynbit AI Revenue Intelligence Copilot, an expert advisor for enterprise B2B sales automation.\n"
            "Answer the question accurately using the provided enterprise knowledge.\n"
            "Cite specific metrics, case studies, and percentages."
        )

        prompt = f"{base_system}\n\n{rag_context}\n\n"
        if lead_context:
            prompt += f"CURRENT PROSPECT CONTEXT:\n{lead_context}\n\n"
        prompt += f"QUESTION: {query}\n"

        answer = ""
        model_name = "Cynbit Cognitive Engine (RAG-Augmented)"

        # 1. Check Gemini
        if _gemini_client:
            try:
                response = _gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if response and response.text:
                    answer = response.text
                    model_name = "Gemini 2.5 Flash (RAG-Augmented)"
            except Exception as e:
                print(f"[Cynbit RAG] Gemini API call exception: {e}")

        # 2. Check OpenAI-compatible endpoint
        if not answer and OPENAI_API_KEY:
            try:
                import requests as rq
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                body = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature
                }
                res = rq.post(f"{OPENAI_API_BASE}/chat/completions", headers=headers, json=body, timeout=8.0)
                if res.status_code == 200:
                    answer = res.json()["choices"][0]["message"]["content"]
                    model_name = "OpenAI-Compatible LLM (RAG-Augmented)"
            except Exception as e:
                print(f"[Cynbit RAG] OpenAI compatible API exception: {e}")

        # 3. High-Quality Cognitive Synthesizer Fallback
        if not answer:
            answer = self._synthesize_offline_rag_answer(query, retrieved_chunks, lead_context)

        latency = round((time.time() - start_time) * 1000, 1)
        follow_ups = self._generate_suggested_follow_ups(query, retrieved_chunks)

        return {
            "query": query,
            "answer": answer,
            "retrieved_chunks": retrieved_chunks,
            "model_name": model_name,
            "latency_ms": latency,
            "suggested_follow_ups": follow_ups
        }

    def _synthesize_offline_rag_answer(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        lead_context: Optional[str] = None
    ) -> str:
        if not chunks:
            return (
                "No direct knowledge base matches were found. "
                "Cynbit provides autonomous lead scoring, sub-90s inbound triage, and native CRM synchronization."
            )

        top = chunks[0]
        response_parts = []
        response_parts.append(f"### 💡 Strategic Intelligence: {top.title}\n")
        response_parts.append(f"Based on Cynbit's indexed enterprise knowledge base (**{top.category}**, {top.industry}), here is the validated recommendation:\n")
        response_parts.append(f"> {top.content}\n")

        if top.metrics:
            response_parts.append("#### 📊 Key Verified Metrics & Proof Points:")
            for k, v in top.metrics.items():
                metric_name = k.replace("_", " ").title()
                response_parts.append(f"- **{metric_name}**: `{v}`")
            response_parts.append("")

        if len(chunks) > 1:
            response_parts.append("#### 🔗 Supporting Enterprise Evidence:")
            for c in chunks[1:]:
                response_parts.append(f"- **{c.title}** ({c.category}): Match Score `{c.similarity_score * 100:.0f}%`")
            response_parts.append("")

        if lead_context:
            response_parts.append(f"#### 🎯 Application to Target Lead:\n")
            response_parts.append(f"Leverage this evidence directly in your conversation to address their specific operational concerns and demonstrate proven ROI.")

        return "\n".join(response_parts)

    def _generate_suggested_follow_ups(self, query: str, chunks: List[RetrievedChunk]) -> List[str]:
        q = query.lower()
        if "pricing" in q or "cost" in q:
            return [
                "What is the ROI payback period for the Enterprise Suite?",
                "How do Cynbit pricing tiers compare to hiring additional SDRs?",
                "Can we run a 14-day rapid proof-of-concept pilot?"
            ]
        elif "apollo" in q or "competitor" in q or "outreach" in q:
            return [
                "How do we handle prospects who already pay for Salesforce or HubSpot?",
                "What is our response rate benchmark compared to generic email sequencers?",
                "Can Cynbit replace our existing outbound data vendors?"
            ]
        elif "compliance" in q or "hipaa" in q or "security" in q:
            return [
                "What is Cynbit's data retention policy for enterprise LLM calls?",
                "How does Cynbit handle PII redaction before lead scoring?",
                "Is there an audit log of every autonomous agent routing decision?"
            ]
        else:
            return [
                "Show me the Apex Logistics case study ROI metrics.",
                "How does Cynbit's 4-Pillar Scoring Engine calculate intent?",
                "What are the commercial pricing packages for mid-market accounts?"
            ]
