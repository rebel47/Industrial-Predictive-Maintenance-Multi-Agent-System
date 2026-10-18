from typing import Dict, Any, List
from app.graph.state import InvestigationState, Evidence
from app.tools.web_search import WebSearchClient

class WebResearchAgent:
    """External technical documentation and manufacturer advisory research agent."""

    def __init__(self):
        self.search_client = WebSearchClient()

    def run(self, state: InvestigationState) -> Dict[str, Any]:
        asset_id = state.get("asset_id", "P-104")
        asset_model = state.get("asset_model", "FlowMax P-100 / SKF 6205")
        user_question = state.get("user_question", "")
        
        # Target queries based on observed symptoms
        query = f"{asset_model} bearing vibration temperature advisory troubleshooting"
        findings = self.search_client.search_technical_sources(
            query=query,
            equipment_model=asset_model,
            max_results=3
        )

        web_evidence: List[Evidence] = []
        for idx, doc in enumerate(findings):
            ev_id = f"E-WEB-{idx+1:02d}"
            claim = f"[{doc.get('publisher', 'OEM')}] {doc.get('title', 'Service Advisory')}: {doc.get('snippet', '')}"
            ref = f"{doc.get('url', 'N/A')} (Pub: {doc.get('published_date', 'N/A')})"
            
            supports = []
            contradicts = []
            lower_s = claim.lower()
            if "bpfi" in lower_s or "raceway" in lower_s or "bearing" in lower_s:
                supports.append("bearing_damage")
            if "misalignment" in lower_s and "temperature" in lower_s:
                # Timken bulletin notes misalignment typically maintains normal temperature (< 68°C)
                contradicts.append("pure_misalignment_with_high_temp")
            if "cavitation" in lower_s:
                supports.append("cavitation")

            web_evidence.append({
                "evidence_id": ev_id,
                "source_type": "web",
                "claim": claim,
                "source_reference": ref,
                "supports": supports,
                "contradicts": contradicts,
                "credibility": doc.get("credibility", "external_authoritative")
            })

        return {
            "web_evidence": web_evidence
        }
