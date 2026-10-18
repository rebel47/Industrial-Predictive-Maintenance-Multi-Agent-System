from typing import Dict, Any, List
from app.graph.state import InvestigationState, Evidence
from app.rag.retrieval import HybridIndustrialRetriever

class RAGKnowledgeAgent:
    """Internal technical documentation retrieval agent."""

    def __init__(self):
        self.retriever = HybridIndustrialRetriever()

    def run(self, state: InvestigationState) -> Dict[str, Any]:
        asset_id = state.get("asset_id", "P-104")
        user_question = state.get("user_question", "")
        sensor_findings = state.get("sensor_findings", {})
        
        # Build enriched retrieval query
        symptom_keywords = []
        if sensor_findings:
            anomalies = sensor_findings.get("anomalies", [])
            for a in anomalies:
                symptom_keywords.append(a.get("signal", ""))
            iso_info = sensor_findings.get("iso_severity")
            if iso_info:
                symptom_keywords.append(iso_info.get("zone", ""))
                symptom_keywords.append(iso_info.get("severity", ""))

        enriched_query = f"{user_question} {asset_id} {' '.join(symptom_keywords)} troubleshooting limits"
        retrieved_chunks = self.retriever.retrieve(
            query=enriched_query,
            asset_id=asset_id,
            top_k=4
        )

        internal_evidence: List[Evidence] = []
        missing_evidence: List[str] = []

        if not retrieved_chunks:
            missing_evidence.append(f"No internal technical manuals or incident records found for query: '{user_question}'.")
        else:
            for idx, chunk in enumerate(retrieved_chunks):
                ev_id = f"E-RAG-{idx+1:02d}"
                claim = (
                    f"[{chunk['document_type'].upper()}] {chunk['title']} - {chunk['section']}: "
                    f"{chunk['passage'][:280].replace(chr(10), ' ')}..."
                )
                ref = f"{chunk['document_id']} ({chunk['section']})"
                
                # Determine supported hypotheses
                supports = []
                lower_p = chunk['passage'].lower()
                if "bearing" in lower_p or "bpfi" in lower_p or "bpfo" in lower_p:
                    supports.append("bearing_damage")
                if "misalignment" in lower_p or "coupling" in lower_p:
                    supports.append("misalignment")
                if "cavitation" in lower_p:
                    supports.append("cavitation")
                if "loto" in lower_p or "sop-042" in lower_p:
                    supports.append("safety_isolation")

                internal_evidence.append({
                    "evidence_id": ev_id,
                    "source_type": "internal",
                    "claim": claim,
                    "source_reference": ref,
                    "supports": supports,
                    "contradicts": [],
                    "credibility": "internal_authorized"
                })

        return {
            "internal_evidence": state.get("internal_evidence", []) + internal_evidence,
            "missing_evidence": state.get("missing_evidence", []) + missing_evidence
        }
