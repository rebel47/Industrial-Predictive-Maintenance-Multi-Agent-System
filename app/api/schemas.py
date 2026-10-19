from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class InvestigationRequest(BaseModel):
    asset_id: str = Field(default="P-104", description="Equipment identifier (e.g. P-104, P-102, M-201)")
    user_question: str = Field(
        default="The motor on Pump P-104 is vibrating more than usual, its temperature has increased, and the machine has started making an unusual noise. What is likely wrong, and what should we do?",
        description="Technician symptom report or query"
    )
    telemetry_override: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional custom telemetry dictionary or sensor readings"
    )
    fault_type: Optional[str] = Field(
        default=None,
        description="Optional preset fault type (e.g. INNER_RACE_FAULT, MISALIGNMENT, LUBRICATION_FAILURE, NORMAL)"
    )

class ApprovalRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    engineer_name: str = Field(default="Lead Reliability Engineer")
    engineer_role: str = Field(default="Certified Vibration Analyst Cat III")
    comments: str = Field(default="Reviewed evidence E001-E010 and safety steps. Approved for execution.")

class AssetInfo(BaseModel):
    asset_id: str
    model: str
    driver: str
    de_bearing: str
    nde_bearing: Optional[str] = None
    iso_class: str
