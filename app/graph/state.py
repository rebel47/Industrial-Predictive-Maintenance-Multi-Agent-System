from typing import TypedDict, Literal, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Evidence(TypedDict):
    evidence_id: str
    source_type: Literal["sensor", "internal", "web"]
    claim: str
    source_reference: str
    supports: List[str]
    contradicts: List[str]
    credibility: str

class Hypothesis(TypedDict):
    failure_mode: str
    status: Literal["supported", "plausible", "unlikely", "inconclusive"]
    supporting_evidence_ids: List[str]
    contradicting_evidence_ids: List[str]
    missing_tests: List[str]
    explanation: str

class MaintenanceAction(TypedDict):
    step_order: int
    action: str
    urgency: Literal["immediate", "scheduled", "conditional"]
    safety_hazards: List[str]
    requires_loto: bool
    parts_to_verify: List[str]
    evidence_references: List[str]

class InvestigationState(TypedDict):
    investigation_id: str
    asset_id: str
    asset_model: str
    user_question: str
    telemetry_data: Optional[Dict[str, Any]]
    sensor_findings: Dict[str, Any]
    internal_evidence: List[Evidence]
    web_evidence: List[Evidence]
    merged_evidence: List[Evidence]
    hypotheses: List[Hypothesis]
    missing_evidence: List[str]
    maintenance_plan: Dict[str, Any]
    verification_status: Literal["PASSED", "WARNING", "FAILED", "PENDING"]
    verification_details: Dict[str, Any]
    approval_status: Literal["PENDING", "APPROVED", "REJECTED"]
    engineer_notes: Optional[str]
    final_report: str
    iteration_count: int
    route_step: str
