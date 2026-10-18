import uuid
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from app.graph.state import InvestigationState, Evidence

ASSET_REGISTRY = {
    "P-104": {
        "model": "FlowMax P-100 Horizontal Centrifugal Slurry Pump",
        "driver": "ApexDrive M-201 75 kW Induction Motor",
        "de_bearing": "SKF 6205-2Z/C3",
        "nde_bearing": "SKF NU 205 ECP",
        "iso_class": "Class II (15-300 kW, Rigid Foundation)"
    },
    "P-102": {
        "model": "FlowMax P-100 Horizontal Centrifugal Slurry Pump",
        "driver": "ApexDrive M-201 75 kW Induction Motor",
        "de_bearing": "SKF 6205-2Z/C3",
        "nde_bearing": "SKF NU 205 ECP",
        "iso_class": "Class II (15-300 kW, Rigid Foundation)"
    },
    "M-201": {
        "model": "ApexDrive 75 kW Three-Phase Induction Motor",
        "driver": "400V 50Hz Direct On Line",
        "de_bearing": "6310-C3",
        "nde_bearing": "6210-C3",
        "iso_class": "Class II"
    }
}

class SupervisorAgent:
    """Coordinates multi-agent investigation lifecycle, routes workflow, and generates final report."""

    @staticmethod
    def initialize_investigation(
        user_question: str,
        asset_id: str = "P-104",
        telemetry_data: Any = None
    ) -> InvestigationState:
        inv_id = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        asset_info = ASSET_REGISTRY.get(asset_id, {
            "model": f"Generic Rotating Asset {asset_id}",
            "driver": "Electric Motor",
            "de_bearing": "Unknown",
            "iso_class": "Class II"
        })

        # Ensure telemetry_data is JSON/msgpack serializable for LangGraph checkpointer
        serializable_telemetry = None
        if telemetry_data is not None:
            if isinstance(telemetry_data, pd.DataFrame):
                serializable_telemetry = {"dataframe": telemetry_data.to_dict(orient="list")}
            elif isinstance(telemetry_data, dict) and "dataframe" in telemetry_data:
                df_val = telemetry_data["dataframe"]
                if isinstance(df_val, pd.DataFrame):
                    serializable_telemetry = {"dataframe": df_val.to_dict(orient="list")}
                else:
                    serializable_telemetry = telemetry_data
            else:
                serializable_telemetry = telemetry_data

        return {
            "investigation_id": inv_id,
            "asset_id": asset_id,
            "asset_model": asset_info["model"],
            "user_question": user_question,
            "telemetry_data": serializable_telemetry,
            "sensor_findings": {},
            "internal_evidence": [],
            "web_evidence": [],
            "merged_evidence": [],
            "hypotheses": [],
            "missing_evidence": [],
            "maintenance_plan": {},
            "verification_status": "PENDING",
            "verification_details": {},
            "approval_status": "PENDING",
            "engineer_notes": None,
            "final_report": "",
            "iteration_count": 0,
            "route_step": "init"
        }

    @staticmethod
    def evaluate_evidence_sufficiency(state: InvestigationState) -> Dict[str, Any]:
        """Evaluates whether gathered evidence is sufficient to proceed to root-cause synthesis."""
        evidence_list = state.get("merged_evidence", [])
        iter_count = state.get("iteration_count", 0)
        
        # Check if we have at least one numeric/sensor finding and one internal/external reference
        has_sensor = any(e.get("source_type") == "sensor" for e in evidence_list)
        has_doc = any(e.get("source_type") in ("internal", "web") for e in evidence_list)
        
        is_sufficient = (has_sensor and has_doc) or len(evidence_list) >= 3
        
        if not is_sufficient and iter_count < 2:
            return {
                "route_step": "additional_retrieval",
                "iteration_count": iter_count + 1
            }
        else:
            return {
                "route_step": "root_cause_analysis",
                "iteration_count": iter_count
            }

    @staticmethod
    def compile_final_report(state: InvestigationState) -> Dict[str, Any]:
        """Synthesize the executive engineering diagnostic report."""
        inv_id = state.get("investigation_id")
        asset_id = state.get("asset_id")
        asset_model = state.get("asset_model")
        user_q = state.get("user_question")
        findings = state.get("sensor_findings", {})
        evidence_list = state.get("merged_evidence", [])
        hypotheses = state.get("hypotheses", [])
        plan = state.get("maintenance_plan", {})
        verif = state.get("verification_details", {})
        
        iso_str = "N/A"
        if findings.get("iso_severity"):
            iso_str = f"{findings['iso_severity']['zone']} - {findings['iso_severity']['severity'].upper()} ({findings['iso_severity']['vibration_rms_mm_s']} mm/s RMS)"

        ml_str = "N/A"
        if findings.get("ml_classification"):
            ml_str = f"{findings['ml_classification']['predicted_class']} (Confidence: {findings['ml_classification']['confidence']*100:.1f}%)"

        # Hypotheses summary table
        hyp_md = "| Failure Mode | Status | Supporting Evidence | Contradicting Evidence |\n| :--- | :--- | :--- | :--- |\n"
        for h in hypotheses:
            sup_str = ", ".join(h.get("supporting_evidence_ids", [])) or "None"
            con_str = ", ".join(h.get("contradicting_evidence_ids", [])) or "None"
            hyp_md += f"| **{h.get('failure_mode')}** | `{h.get('status').upper()}` | {sup_str} | {con_str} |\n"

        # Evidence table
        ev_md = "| ID | Type | Source Reference | Claim |\n| :--- | :--- | :--- | :--- |\n"
        for e in evidence_list:
            ev_md += f"| `{e['evidence_id']}` | {e['source_type']} | {e['source_reference']} | {e['claim'][:120]}... |\n"

        # Maintenance actions list
        actions_md = ""
        for a in plan.get("actions", []):
            loto_badge = "🔒 **[MANDATORY LOTO]**" if a.get("requires_loto") else "ℹ️ Standard Caution"
            actions_md += (
                f"### Step {a.get('step_order')}: {a.get('action')}\n"
                f"- **Urgency**: `{a.get('urgency').upper()}` | **Safety**: {loto_badge}\n"
                f"- **Hazards**: {', '.join(a.get('safety_hazards', []))}\n"
                f"- **Parts / Tools**: {', '.join(a.get('parts_to_verify', []))}\n"
                f"- **Evidence Grounding**: {', '.join(a.get('evidence_references', []))}\n\n"
            )

        report = f"""# Industrial Diagnostic & Root-Cause Investigation Report
**Investigation ID**: `{inv_id}`  
**Asset**: `{asset_id}` ({asset_model})  
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Initial Technician Request**: *"{user_q}"*  

---

## 1. Executive Summary & Diagnostic Conclusion
- **ISO 10816-3 Vibration Severity**: `{iso_str}`
- **Machine Learning Diagnostic**: `{ml_str}`
- **Verification Interlock**: `{verif.get('status', 'PENDING')}` (Grounding: {'PASSED' if verif.get('citation_grounding_passed') else 'FAILED'}, Safety: {'PASSED' if verif.get('safety_interlock_passed') else 'FAILED'})

---

## 2. Competing Failure Hypotheses
{hyp_md}

---

## 3. Grounded Evidence Package
{ev_md}

---

## 4. Prioritized Maintenance & Safety Action Plan
**Plan Title**: {plan.get('plan_title', 'Action Plan')}  
**Required Engineering Sign-off**: `{plan.get('required_signoff_role', 'Reliability Engineer')}`  

{actions_md}

---

## 5. Engineer Review & Approval Sign-off
- **Current Status**: `{state.get('approval_status', 'PENDING')}`
- **Audited Engineer Comments**: {state.get('engineer_notes', 'Awaiting engineer review.')}
"""
        return {"final_report": report}
