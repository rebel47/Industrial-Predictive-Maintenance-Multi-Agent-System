from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List

from app.api.schemas import InvestigationRequest, ApprovalRequest, AssetInfo
from app.graph.workflow import investigation_app
from app.agents.supervisor import SupervisorAgent, ASSET_REGISTRY

app = FastAPI(
    title="Industrial Predictive Maintenance & Root-Cause Analysis Multi-Agent API",
    version="1.0.0",
    description="Agentic engineering assistant orchestrating time-series analytics, hybrid RAG, web intelligence, and safety interlocks."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for investigation sessions
INVESTIGATION_STORE: Dict[str, Dict[str, Any]] = {}

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "industrial-maintenance-ai",
        "registered_assets": len(ASSET_REGISTRY)
    }

@app.get("/api/v1/assets", response_model=List[AssetInfo])
def list_assets():
    results = []
    for asset_id, info in ASSET_REGISTRY.items():
        results.append(AssetInfo(
            asset_id=asset_id,
            model=info["model"],
            driver=info["driver"],
            de_bearing=info["de_bearing"],
            nde_bearing=info.get("nde_bearing"),
            iso_class=info["iso_class"]
        ))
    return results

@app.post("/api/v1/investigate")
def run_investigation(req: InvestigationRequest):
    """Initiates an end-to-end multi-agent root-cause investigation."""
    try:
        initial_state = SupervisorAgent.initialize_investigation(
            user_question=req.user_question,
            asset_id=req.asset_id,
            telemetry_data=req.telemetry_override
        )
        inv_id = initial_state["investigation_id"]
        
        config = {"configurable": {"thread_id": inv_id}}
        final_state = investigation_app.invoke(initial_state, config=config)
        
        INVESTIGATION_STORE[inv_id] = final_state
        return {
            "investigation_id": inv_id,
            "asset_id": final_state["asset_id"],
            "verification_status": final_state["verification_status"],
            "approval_status": final_state["approval_status"],
            "primary_hypothesis": final_state["hypotheses"][0] if final_state["hypotheses"] else None,
            "evidence_count": len(final_state["merged_evidence"]),
            "final_report": final_state["final_report"],
            "state": final_state
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation workflow error: {str(e)}"
        )

@app.get("/api/v1/investigate/{inv_id}")
def get_investigation(inv_id: str):
    if inv_id not in INVESTIGATION_STORE:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found.")
    return INVESTIGATION_STORE[inv_id]

@app.post("/api/v1/investigate/{inv_id}/approve")
def approve_investigation(inv_id: str, req: ApprovalRequest):
    """Submits human engineering review and formal sign-off."""
    if inv_id not in INVESTIGATION_STORE:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found.")
    
    state = INVESTIGATION_STORE[inv_id]
    state["approval_status"] = req.decision
    audit_entry = f"[{req.decision}] by {req.engineer_name} ({req.engineer_role}): {req.comments}"
    state["engineer_notes"] = audit_entry
    
    # Update final report with signed status
    state["final_report"] += f"\n\n### Audit Log\n- **Signed By**: {req.engineer_name} ({req.engineer_role})\n- **Decision**: `{req.decision}`\n- **Notes**: {req.comments}\n"
    INVESTIGATION_STORE[inv_id] = state
    
    return {
        "investigation_id": inv_id,
        "approval_status": state["approval_status"],
        "audit_entry": audit_entry
    }
