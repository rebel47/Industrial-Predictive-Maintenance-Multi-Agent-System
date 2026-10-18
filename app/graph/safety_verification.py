from typing import Dict, Any, List
from app.graph.state import InvestigationState, Evidence, Hypothesis, MaintenanceAction

class SafetyVerificationEngine:
    """Deterministic validation engine verifying citation grounding and industrial safety rules."""

    @staticmethod
    def verify_investigation(state: InvestigationState) -> Dict[str, Any]:
        merged_evidence: List[Evidence] = state.get("merged_evidence", [])
        hypotheses: List[Hypothesis] = state.get("hypotheses", [])
        maintenance_plan: Dict[str, Any] = state.get("maintenance_plan", {})
        
        valid_ev_ids = {e["evidence_id"] for e in merged_evidence}
        violations = []
        warnings = []
        
        # 1. Check Citation Grounding in Hypotheses
        for hyp in hypotheses:
            mode = hyp.get("failure_mode", "unknown")
            for ref_id in hyp.get("supporting_evidence_ids", []):
                if ref_id not in valid_ev_ids:
                    violations.append(f"Hypothesis '{mode}' references non-existent supporting evidence ID '{ref_id}'.")
            for ref_id in hyp.get("contradicting_evidence_ids", []):
                if ref_id not in valid_ev_ids:
                    violations.append(f"Hypothesis '{mode}' references non-existent contradicting evidence ID '{ref_id}'.")

        # 2. Check Citation Grounding in Maintenance Plan
        actions = maintenance_plan.get("actions", [])
        for act in actions:
            step = act.get("step_order", 0)
            for ref_id in act.get("evidence_references", []):
                if ref_id not in valid_ev_ids:
                    violations.append(f"Maintenance action Step {step} cites invalid evidence ID '{ref_id}'.")

        # 3. Check Safety Interlock & LOTO Requirements
        for act in actions:
            step = act.get("step_order", 0)
            text = act.get("action", "").lower()
            requires_loto = act.get("requires_loto", False)
            
            # Words indicating physical contact or disassembly
            physical_work_keywords = ["disassemble", "uncouple", "replace", "dismount", "open bearing", "loosen", "torque", "stop"]
            involves_physical_work = any(kw in text for kw in physical_work_keywords)
            
            if involves_physical_work and not requires_loto:
                violations.append(f"SAFETY VIOLATION: Action Step {step} involves mechanical intervention without mandatory Lockout/Tagout (LOTO).")
                
            if not act.get("safety_hazards"):
                warnings.append(f"Safety review: Step {step} has no specific hazards listed.")

        # 4. Check for Sufficient Evidence
        if not merged_evidence:
            violations.append("Investigation has zero merged evidence records.")
        elif len(merged_evidence) < 2:
            warnings.append("Low evidence count: Fewer than 2 distinct evidence sources retrieved.")

        # Determine overall verification status
        if violations:
            status = "FAILED"
        elif warnings:
            status = "WARNING"
        else:
            status = "PASSED"

        return {
            "verification_status": status,
            "verification_details": {
                "status": status,
                "citation_grounding_passed": not any("evidence ID" in v for v in violations),
                "safety_interlock_passed": not any("SAFETY VIOLATION" in v for v in violations),
                "violations": violations,
                "warnings": warnings,
                "total_evidence_validated": len(valid_ev_ids),
                "total_actions_validated": len(actions)
            }
        }
