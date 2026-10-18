import pytest
from app.graph.safety_verification import SafetyVerificationEngine

def test_safety_interlock_rejection_of_ungrounded_citations():
    fake_state = {
        "merged_evidence": [
            {"evidence_id": "E001", "claim": "Known fact", "source_reference": "Ref1"}
        ],
        "hypotheses": [
            {
                "failure_mode": "test_failure",
                "status": "supported",
                "supporting_evidence_ids": ["E999_NON_EXISTENT"],
                "contradicting_evidence_ids": []
            }
        ],
        "maintenance_plan": {
            "actions": [
                {
                    "step_order": 1,
                    "action": "Uncouple pump from motor",
                    "requires_loto": True,
                    "evidence_references": ["E001"],
                    "safety_hazards": ["Pinch points"]
                }
            ]
        }
    }
    
    res = SafetyVerificationEngine.verify_investigation(fake_state)
    assert res["verification_status"] == "FAILED"
    assert not res["verification_details"]["citation_grounding_passed"]
    assert any("E999_NON_EXISTENT" in v for v in res["verification_details"]["violations"])

def test_safety_interlock_rejection_of_missing_loto():
    hazardous_state = {
        "merged_evidence": [
            {"evidence_id": "E001", "claim": "Known fact", "source_reference": "Ref1"}
        ],
        "hypotheses": [],
        "maintenance_plan": {
            "actions": [
                {
                    "step_order": 1,
                    "action": "Disassemble bearing housing while running",
                    "requires_loto": False,  # Missing mandatory LOTO!
                    "evidence_references": ["E001"],
                    "safety_hazards": ["Entrapment"]
                }
            ]
        }
    }
    
    res = SafetyVerificationEngine.verify_investigation(hazardous_state)
    assert res["verification_status"] == "FAILED"
    assert not res["verification_details"]["safety_interlock_passed"]
    assert any("SAFETY VIOLATION" in v for v in res["verification_details"]["violations"])
