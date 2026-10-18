import pytest
from app.graph.workflow import investigation_app
from app.agents.supervisor import SupervisorAgent

def test_full_investigation_workflow():
    question = "Pump P-104 is vibrating above 5 mm/s and temperature reached 82°C. What is the diagnosis?"
    state = SupervisorAgent.initialize_investigation(
        user_question=question,
        asset_id="P-104"
    )
    
    config = {"configurable": {"thread_id": "test-workflow-01"}}
    final_state = investigation_app.invoke(state, config=config)
    
    assert final_state["verification_status"] in ("PASSED", "WARNING")
    assert len(final_state["hypotheses"]) >= 2
    assert len(final_state["merged_evidence"]) >= 3
    assert final_state["maintenance_plan"]["actions"]
    assert "bearing" in final_state["final_report"].lower()
