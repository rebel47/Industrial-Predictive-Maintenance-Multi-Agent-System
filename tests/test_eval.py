import pytest
from app.evaluation.langsmith_eval import (
    run_langsmith_eval,
    citation_grounding_evaluator,
    safety_loto_evaluator,
    hypothesis_rigor_evaluator
)

def test_langsmith_evaluators_logic():
    class MockRun:
        def __init__(self, outs):
            self.outputs = outs
            
    class MockExample:
        def __init__(self, ins, outs):
            self.inputs = ins
            self.outputs = outs

    sample_output = {
        "verification_details": {
            "citation_grounding_passed": True,
            "safety_interlock_passed": True
        },
        "hypotheses": [
            {"failure_mode": "bearing_damage", "missing_tests": ["Grease check"]},
            {"failure_mode": "misalignment", "missing_tests": ["Laser check"]}
        ]
    }

    mock_run = MockRun(sample_output)
    mock_example = MockExample({"question": "Test fault"}, {})

    g_res = citation_grounding_evaluator(mock_run, mock_example)
    assert g_res["score"] == 1.0

    s_res = safety_loto_evaluator(mock_run, mock_example)
    assert s_res["score"] == 1.0

    h_res = hypothesis_rigor_evaluator(mock_run, mock_example)
    assert h_res["score"] == 1.0

def test_langsmith_evaluation_execution():
    res = run_langsmith_eval()
    assert res["status"] == "success"
    if "summary_scores" in res:
        assert res["summary_scores"]["citation_grounding_score"] >= 0.9
        assert res["summary_scores"]["safety_loto_compliance_score"] >= 0.9
        assert res["summary_scores"]["hypothesis_rigor_score"] >= 0.9
