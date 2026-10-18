import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from langsmith import Client, evaluate
from langsmith.schemas import Run, Example

from app.graph.workflow import investigation_app
from app.agents.supervisor import SupervisorAgent
from app.evaluation.test_scenarios import get_all_test_scenarios

load_dotenv()

DATASET_NAME = "industrial-predictive-maintenance-benchmarks"

def get_langsmith_client() -> Optional[Client]:
    """Returns a LangSmith Client if API key is configured."""
    api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
    if api_key and api_key.strip() != "your_langsmith_api_key_here":
        try:
            return Client(api_key=api_key.strip())
        except Exception:
            return None
    return None

def sync_benchmark_dataset_to_langsmith(client: Client) -> str:
    """
    Syncs the 8 failure benchmark scenarios to a LangSmith evaluation dataset.
    """
    scenarios = get_all_test_scenarios()
    
    # Check if dataset already exists
    datasets = list(client.list_datasets(dataset_name=DATASET_NAME))
    if datasets:
        dataset = datasets[0]
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Industrial rotating equipment failure scenarios and edge-case benchmark suite."
        )
        
        for sc in scenarios:
            inputs = {
                "question": sc["question"],
                "asset_id": sc["asset_id"],
                "has_telemetry": sc["telemetry"] is not None
            }
            outputs = sc["expected_findings"]
            metadata = {
                "scenario_id": sc["id"],
                "scenario_name": sc["name"]
            }
            client.create_example(
                inputs=inputs,
                outputs=outputs,
                metadata=metadata,
                dataset_id=dataset.id
            )
            
    return dataset.name

# ----------------- Custom LangSmith Evaluators -----------------

def citation_grounding_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluates whether all citations in hypotheses and maintenance plan are grounded."""
    outputs = run.outputs or {}
    verif = outputs.get("verification_details", {})
    grounding_passed = verif.get("citation_grounding_passed", False)
    return {
        "key": "citation_grounding_score",
        "score": 1.0 if grounding_passed else 0.0,
        "comment": "All citations grounded in merged evidence" if grounding_passed else "Ungrounded citations detected"
    }

def safety_loto_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluates whether hazardous physical interventions enforce Lockout/Tagout (SOP-042)."""
    outputs = run.outputs or {}
    verif = outputs.get("verification_details", {})
    safety_passed = verif.get("safety_interlock_passed", False)
    return {
        "key": "safety_loto_compliance_score",
        "score": 1.0 if safety_passed else 0.0,
        "comment": "Mandatory LOTO interlock verified" if safety_passed else "Safety violation: missing LOTO"
    }

def hypothesis_rigor_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """Evaluates whether at least two competing hypotheses were compared with distinguishing tests."""
    outputs = run.outputs or {}
    hyps = outputs.get("hypotheses", [])
    has_competing = len(hyps) >= 2
    has_tests = any(h.get("missing_tests") for h in hyps)
    score = 1.0 if (has_competing and has_tests) else 0.5 if has_competing else 0.0
    return {
        "key": "hypothesis_rigor_score",
        "score": score,
        "comment": f"Evaluated {len(hyps)} hypotheses with diagnostic verification tests."
    }

def target_investigation_runner(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Target function invoked during evaluation runs."""
    question = inputs.get("question", "")
    asset_id = inputs.get("asset_id", "P-104")
    
    state = SupervisorAgent.initialize_investigation(
        user_question=question,
        asset_id=asset_id
    )
    config = {"configurable": {"thread_id": f"ls-eval-{state['investigation_id']}"}}
    result = investigation_app.invoke(state, config=config)
    return result

def run_langsmith_eval(experiment_prefix: str = "industrial-maint-eval") -> Dict[str, Any]:
    """
    Executes benchmark evaluation with LangSmith tracing and logging.
    If LangSmith API key is present, uploads to LangSmith.
    Otherwise, executes the evaluators locally and formats results.
    """
    client = get_langsmith_client()
    
    if client:
        # Cloud LangSmith Evaluation
        try:
            dataset_name = sync_benchmark_dataset_to_langsmith(client)
            eval_results = evaluate(
                target_investigation_runner,
                data=dataset_name,
                evaluators=[
                    citation_grounding_evaluator,
                    safety_loto_evaluator,
                    hypothesis_rigor_evaluator
                ],
                experiment_prefix=experiment_prefix
            )
            return {
                "mode": "langsmith_cloud",
                "status": "success",
                "dataset_name": dataset_name,
                "project": os.getenv("LANGCHAIN_PROJECT", "industrial-predictive-maintenance"),
                "results": eval_results
            }
        except Exception as e:
            pass

    # Local Evaluator Fallback (executes identical LangSmith evaluator logic locally)
    scenarios = get_all_test_scenarios()
    eval_records = []
    
    for sc in scenarios:
        inputs = {"question": sc["question"], "asset_id": sc["asset_id"]}
        outputs = target_investigation_runner(inputs)
        
        # Mock Run and Example objects for evaluators
        class MockRun:
            def __init__(self, outs): self.outputs = outs
        class MockExample:
            def __init__(self, ins, outs): self.inputs = ins; self.outputs = outs
            
        mock_run = MockRun(outputs)
        mock_example = MockExample(inputs, sc["expected_findings"])
        
        g_res = citation_grounding_evaluator(mock_run, mock_example)
        s_res = safety_loto_evaluator(mock_run, mock_example)
        h_res = hypothesis_rigor_evaluator(mock_run, mock_example)
        
        eval_records.append({
            "scenario_id": sc["id"],
            "name": sc["name"],
            "citation_grounding": g_res["score"],
            "safety_loto": s_res["score"],
            "hypothesis_rigor": h_res["score"]
        })

    avg_grounding = float(sum(r["citation_grounding"] for r in eval_records) / len(eval_records))
    avg_safety = float(sum(r["safety_loto"] for r in eval_records) / len(eval_records))
    avg_rigor = float(sum(r["hypothesis_rigor"] for r in eval_records) / len(eval_records))

    return {
        "mode": "langsmith_local",
        "status": "success",
        "eval_records": eval_records,
        "summary_scores": {
            "citation_grounding_score": round(avg_grounding, 4),
            "safety_loto_compliance_score": round(avg_safety, 4),
            "hypothesis_rigor_score": round(avg_rigor, 4)
        },
        "langsmith_instructions": "To stream results to LangSmith cloud dashboard, set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY in .env"
    }

if __name__ == "__main__":
    res = run_langsmith_eval()
    print("\n" + "="*80)
    print("LANGSMITH EVALUATION BENCHMARK REPORT")
    print("="*80)
    print(f"Mode:   {res['mode'].upper()}")
    print(f"Status: {res['status'].upper()}")
    if "summary_scores" in res:
        print("\nSummary Scores:")
        for k, v in res["summary_scores"].items():
            print(f"  {k:32s}: {v*100:.1f}%")
        print(f"\n{res.get('langsmith_instructions', '')}")
    print("="*80 + "\n")
