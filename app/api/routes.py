from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import numpy as np

from app.api.schemas import InvestigationRequest, ApprovalRequest, AssetInfo
from app.graph.workflow import investigation_app
from app.agents.supervisor import SupervisorAgent, ASSET_REGISTRY
from app.analytics.dataset_loader import generate_telemetry_history, generate_cwru_benchmark_signals
from app.rag.ingestion import load_all_industrial_documents, DOCS_DIR

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

PRESET_SCENARIOS = [
    {
        "id": "scenario_1",
        "title": "Scenario 1: High Vibration & Overheating (Inner Race Defect)",
        "fault_type": "INNER_RACE_FAULT",
        "asset_id": "P-104",
        "question": "The motor on Pump P-104 is vibrating more than usual, its temperature has increased, and the machine has started making an unusual noise. What is likely wrong, and what should we do?"
    },
    {
        "id": "scenario_2",
        "title": "Scenario 2: Dynamic Coupling Misalignment (2X Harmonic)",
        "fault_type": "MISALIGNMENT",
        "asset_id": "P-102",
        "question": "Pump P-102 is vibrating heavily with a deep humming sound. Temperature is within normal limits but vibration has doubled."
    },
    {
        "id": "scenario_3",
        "title": "Scenario 3: Lubrication Starvation (Rapid Thermal Spike)",
        "fault_type": "LUBRICATION_FAILURE",
        "asset_id": "P-104",
        "question": "Bearing temperature on P-104 has spiked past 85°C within 30 minutes, but vibration RMS is only moderately elevated."
    },
    {
        "id": "scenario_4",
        "title": "Scenario 4: Normal Operational Baseline",
        "fault_type": "NORMAL",
        "asset_id": "P-104",
        "question": "Routine shift health check for Pump P-104. Are all vibration and temperature levels within ISO normal limits?"
    }
]

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "industrial-maintenance-ai",
        "registered_assets": len(ASSET_REGISTRY)
    }

@app.get("/api/v1/scenarios")
def list_scenarios():
    return PRESET_SCENARIOS

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

@app.get("/api/v1/telemetry")
def get_telemetry(asset_id: str = "P-104", fault_type: str = "INNER_RACE_FAULT"):
    df = generate_telemetry_history(asset_id=asset_id, fault_type=fault_type, n_points=60)
    
    points = []
    for idx, row in df.iterrows():
        points.append({
            "time_idx": int(idx),
            "timestamp": row["timestamp"].strftime("%H:%M") if hasattr(row["timestamp"], "strftime") else str(row["timestamp"]),
            "vibration_rms": round(float(row["vibration_rms"]), 3),
            "temperature": round(float(row["temperature"]), 2),
            "motor_current": round(float(row["motor_current"]), 2),
            "discharge_pressure_bar": round(float(row["discharge_pressure_bar"]), 3)
        })

    cwru_signals = generate_cwru_benchmark_signals()
    active_key = fault_type if fault_type in cwru_signals else "INNER_RACE_FAULT"
    active_waveform = cwru_signals.get(active_key, list(cwru_signals.values())[0])

    fs = 12000
    n = len(active_waveform)
    fft_y = np.abs(np.fft.rfft(active_waveform * np.hanning(n))) * (2.0 / n)
    fft_x = np.fft.rfftfreq(n, 1.0 / fs)
    mask = (fft_x <= 500)
    step = max(1, int(np.sum(mask) / 250))
    spectrum = [
        {"freq": round(float(fx), 2), "amp": round(float(fy), 4)}
        for fx, fy in zip(fft_x[mask][::step], fft_y[mask][::step])
    ]

    fr = 1750.0 / 60.0
    markers = [
        {"label": "1X Shaft", "frequency": round(fr, 2), "color": "#10b981"},
        {"label": "2X Misalignment", "frequency": round(2 * fr, 2), "color": "#8b5cf6"},
        {"label": "BPFI Inner Race", "frequency": round(5.415 * fr, 2), "color": "#ef4444"},
        {"label": "BPFO Outer Race", "frequency": round(3.585 * fr, 2), "color": "#f97316"}
    ]

    return {
        "asset_id": asset_id,
        "fault_type": fault_type,
        "telemetry": points,
        "spectrum": spectrum,
        "characteristic_frequencies": markers,
        "thresholds": {
            "vibration_alert": 2.8,
            "vibration_trip": 4.5,
            "temp_warning": 75.0,
            "temp_trip": 85.0
        }
    }

@app.get("/api/v1/documents")
def get_documents():
    all_chunks = load_all_industrial_documents(DOCS_DIR)
    docs_map = {}
    for c in all_chunks:
        if c.title not in docs_map:
            docs_map[c.title] = {
                "document_id": c.document_id,
                "title": c.title,
                "equipment_model": c.equipment_model,
                "document_type": c.document_type,
                "revision_date": c.revision_date,
                "sections": []
            }
        docs_map[c.title]["sections"].append({
            "chunk_id": c.chunk_id,
            "section": c.section,
            "content": c.content
        })
    return list(docs_map.values())

@app.post("/api/v1/investigate")
def run_investigation(req: InvestigationRequest):
    """Initiates an end-to-end multi-agent root-cause investigation."""
    try:
        telemetry_data = req.telemetry_override
        if telemetry_data is None and req.fault_type:
            df_hist = generate_telemetry_history(asset_id=req.asset_id, fault_type=req.fault_type, n_points=60)
            telemetry_data = {"dataframe": df_hist}

        initial_state = SupervisorAgent.initialize_investigation(
            user_question=req.user_question,
            asset_id=req.asset_id,
            telemetry_data=telemetry_data
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
