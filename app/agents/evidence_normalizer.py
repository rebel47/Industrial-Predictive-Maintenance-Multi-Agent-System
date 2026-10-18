from typing import Dict, Any, List
from app.graph.state import InvestigationState, Evidence

class EvidenceNormalizer:
    """Consolidates sensor, internal RAG, and external web evidence into a unified evidence index."""

    @staticmethod
    def merge_evidence(state: InvestigationState) -> Dict[str, Any]:
        raw_internal = state.get("internal_evidence", [])
        raw_web = state.get("web_evidence", [])

        merged: List[Evidence] = []
        counter = 1

        for ev in raw_internal + raw_web:
            norm_ev: Evidence = {
                "evidence_id": f"E{counter:03d}",
                "source_type": ev.get("source_type", "internal"),
                "claim": ev.get("claim", ""),
                "source_reference": ev.get("source_reference", ""),
                "supports": ev.get("supports", []),
                "contradicts": ev.get("contradicts", []),
                "credibility": ev.get("credibility", "unspecified")
            }
            merged.append(norm_ev)
            counter += 1

        return {
            "merged_evidence": merged
        }
