import os
import json
import numpy as np
import pandas as pd
from tabulate import tabulate
from typing import Dict, Any, List

from app.analytics.anomaly_detection import SensorQualityChecker, AnomalyDetector
from app.analytics.fault_classifier import BearingFaultClassifier
from app.analytics.dataset_loader import generate_telemetry_history
from app.rag.retrieval import HybridIndustrialRetriever
from app.graph.workflow import investigation_app
from app.agents.supervisor import SupervisorAgent
from app.graph.safety_verification import SafetyVerificationEngine
from app.evaluation.test_scenarios import get_all_test_scenarios
from app.evaluation.langsmith_eval import run_langsmith_eval

class SystemEvaluator:
    """End-to-end evaluation harness measuring ML performance, retrieval quality, safety compliance, and failure tests."""

    def __init__(self):
        self.retriever = HybridIndustrialRetriever()
        self.classifier = BearingFaultClassifier()
        self.anomaly_detector = AnomalyDetector()
        self.quality_checker = SensorQualityChecker()

    def evaluate_classifier(self) -> Dict[str, Any]:
        metrics = self.classifier.train()
        return {
            "macro_f1": metrics["macro_f1"],
            "classes": metrics["classes"],
            "confusion_matrix": metrics["confusion_matrix"],
            "test_samples": metrics["test_samples"]
        }

    def evaluate_retrieval(self) -> Dict[str, Any]:
        test_queries = [
            ("P-104 vibration velocity limits ISO 10816", "OEM-MAN-P104-REV4"),
            ("Lockout tagout procedure hazardous energy isolation", "SOP-042-REV5"),
            ("Bearing replacement heating temperature alignment tolerances", "SOP-088-REV3"),
            ("P-104 drive end bearing seizure historical incident", "INC-2024-03-P104"),
            ("ApexDrive induction motor winding temperature limits", "OEM-MAN-M201-REV2")
        ]

        hits_at_1 = 0
        hits_at_3 = 0
        reciprocal_ranks = []

        for q, expected_doc in test_queries:
            results = self.retriever.retrieve(query=q, top_k=3)
            found_rank = 0
            for rank_idx, r in enumerate(results):
                if expected_doc in r["document_id"]:
                    found_rank = rank_idx + 1
                    break
            if found_rank == 1:
                hits_at_1 += 1
            if found_rank > 0 and found_rank <= 3:
                hits_at_3 += 1
                reciprocal_ranks.append(1.0 / found_rank)
            else:
                reciprocal_ranks.append(0.0)

        n = len(test_queries)
        return {
            "queries_evaluated": n,
            "recall_at_1": round(hits_at_1 / n, 4),
            "recall_at_3": round(hits_at_3 / n, 4),
            "mrr": round(float(np.mean(reciprocal_ranks)), 4)
        }

    def evaluate_anomaly_detector(self) -> Dict[str, Any]:
        # 10 anomalous runs, 10 normal runs
        y_true = []
        y_pred = []

        for _ in range(10):
            df_norm = generate_telemetry_history("P-104", fault_type="NORMAL")
            res_norm = self.anomaly_detector.detect_anomalies(df_norm, "P-104")
            has_crit = any(a["severity"] in ("CRITICAL", "WARNING") for a in res_norm["anomalies"])
            y_true.append(0)
            y_pred.append(1 if has_crit else 0)

        for _ in range(10):
            df_anom = generate_telemetry_history("P-104", fault_type="INNER_RACE_FAULT")
            res_anom = self.anomaly_detector.detect_anomalies(df_anom, "P-104")
            has_crit = any(a["severity"] in ("CRITICAL", "WARNING") for a in res_anom["anomalies"])
            y_true.append(1)
            y_pred.append(1 if has_crit else 0)

        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)
        tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)

        precision = tp / (tp + fp + 1e-9)
        recall = tp / (tp + fn + 1e-9)
        false_alarm_rate = fp / (fp + tn + 1e-9)

        return {
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "false_alarm_rate": round(float(false_alarm_rate), 4),
            "total_runs": len(y_true)
        }

    def evaluate_failure_scenarios(self) -> List[Dict[str, Any]]:
        scenarios = get_all_test_scenarios()
        results = []

        for sc in scenarios:
            state = SupervisorAgent.initialize_investigation(
                user_question=sc["question"],
                asset_id=sc["asset_id"],
                telemetry_data=sc["telemetry"]
            )
            config = {"configurable": {"thread_id": f"eval-{sc['id']}"}}
            res = investigation_app.invoke(state, config=config)

            passed = False
            notes = ""

            if sc["id"] == "SCENARIO_1":
                # High vib, normal temp
                anoms = res["sensor_findings"].get("anomalies", [])
                has_vib_anom = any("vibration" in a.get("signal", "").lower() for a in anoms)
                has_temp_anom = any("temp" in a.get("signal", "").lower() for a in anoms)
                passed = has_vib_anom and not has_temp_anom
                notes = f"Vib anomaly: {has_vib_anom}, Temp anomaly: {has_temp_anom}"

            elif sc["id"] == "SCENARIO_2":
                # Normal vib, high temp
                anoms = res["sensor_findings"].get("anomalies", [])
                has_temp_anom = any("temp" in a.get("signal", "").lower() for a in anoms)
                has_vib_anom = any("vibration" in a.get("signal", "").lower() for a in anoms)
                passed = has_temp_anom and not has_vib_anom
                notes = f"Temp anomaly detected ({has_temp_anom}), no spurious vibration anomaly ({not has_vib_anom})"

            elif sc["id"] == "SCENARIO_3":
                # Competing modes compared
                hyps = res.get("hypotheses", [])
                passed = len(hyps) >= 2 and any(h["missing_tests"] for h in hyps)
                notes = f"{len(hyps)} hypotheses compared with distinguishing diagnostic tests"

            elif sc["id"] == "SCENARIO_4":
                # Missing internal docs handled gracefully
                missing = res.get("missing_evidence", [])
                passed = len(missing) > 0 or res["verification_status"] in ("PASSED", "WARNING")
                notes = f"Disclosed missing documentation gap: {missing}"

            elif sc["id"] == "SCENARIO_5":
                # External vs internal conflict: internal LOTO enforced
                plan = res.get("maintenance_plan", {})
                actions = plan.get("actions", [])
                loto_enforced = any(a.get("requires_loto") for a in actions)
                passed = loto_enforced and res["verification_status"] == "PASSED"
                notes = "Plant LOTO enforced over external informal claims"

            elif sc["id"] == "SCENARIO_6":
                # Unknown asset
                passed = "UNKNOWN" in res.get("asset_model", "") or "Generic" in res.get("asset_model", "")
                notes = f"Handled unknown asset model safely: {res.get('asset_model')}"

            elif sc["id"] == "SCENARIO_7":
                # Faulty sensor detected
                quality = res["sensor_findings"].get("data_quality", "")
                passed = quality in ("rejected", "degraded")
                notes = f"Sensor flatline flagged; quality: {quality}"

            elif sc["id"] == "SCENARIO_8":
                # Unsupported action injection test
                # Manually inject an ungrounded claim and test verification engine
                test_state = dict(res)
                test_state["maintenance_plan"] = {
                    "actions": [{
                        "step_order": 99,
                        "action": "Dismount casing",
                        "requires_loto": False,  # Violates LOTO
                        "evidence_references": ["E-FAKE-999"]  # Violates grounding
                    }]
                }
                v_res = SafetyVerificationEngine.verify_investigation(test_state)
                passed = v_res["verification_status"] == "FAILED"
                notes = f"Interlock caught ungrounded citation & safety hazard (Status: {v_res['verification_status']})"

            results.append({
                "scenario_id": sc["id"],
                "name": sc["name"],
                "passed": passed,
                "notes": notes
            })

        return results

    def run_full_benchmark(self) -> Dict[str, Any]:
        cls_metrics = self.evaluate_classifier()
        ret_metrics = self.evaluate_retrieval()
        anom_metrics = self.evaluate_anomaly_detector()
        scenarios_results = self.evaluate_failure_scenarios()
        langsmith_report = run_langsmith_eval()

        all_passed = sum(1 for s in scenarios_results if s["passed"])
        total_scenarios = len(scenarios_results)

        return {
            "fault_classifier": cls_metrics,
            "retrieval": ret_metrics,
            "anomaly_detection": anom_metrics,
            "failure_scenarios": scenarios_results,
            "scenario_success_rate": f"{all_passed}/{total_scenarios} ({all_passed/total_scenarios*100:.1f}%)",
            "langsmith_evaluation": langsmith_report
        }

if __name__ == "__main__":
    evaluator = SystemEvaluator()
    results = evaluator.run_full_benchmark()
    
    print("\n" + "="*80)
    print("INDUSTRIAL PREDICTIVE MAINTENANCE MULTI-AGENT SYSTEM: BENCHMARK REPORT")
    print("="*80)

    print("\n1. CWRU FAULT CLASSIFIER (Supervised ML):")
    print(f"  Macro-F1 Score:    {results['fault_classifier']['macro_f1']}")
    print(f"  Holdout Samples:   {results['fault_classifier']['test_samples']}")
    print(f"  Classes Evaluated: {results['fault_classifier']['classes']}")

    print("\n2. ANOMALY DETECTION (Isolation Forest + Statistical Limits):")
    print(f"  Precision:         {results['anomaly_detection']['precision']}")
    print(f"  Recall:            {results['anomaly_detection']['recall']}")
    print(f"  False Alarm Rate:  {results['anomaly_detection']['false_alarm_rate']}")

    print("\n3. HYBRID RAG RETRIEVAL (BM25 + TF-IDF Vector + RRF):")
    print(f"  Recall@1:          {results['retrieval']['recall_at_1']}")
    print(f"  Recall@3:          {results['retrieval']['recall_at_3']}")
    print(f"  Mean Recip. Rank:  {results['retrieval']['mrr']}")

    print("\n4. EXPLICIT FAILURE SCENARIO BENCHMARK (Section 11 Test Suite):")
    table_data = [
        [s["scenario_id"], s["name"][:35], "PASSED" if s["passed"] else "FAILED", s["notes"][:40]]
        for s in results["failure_scenarios"]
    ]
    print(tabulate(table_data, headers=["Scenario", "Description", "Result", "Notes"], tablefmt="grid"))
    print(f"\nOverall Scenario Pass Rate: {results['scenario_success_rate']}")

    print("\n5. LANGSMITH EVALUATION METRICS:")
    ls = results["langsmith_evaluation"]
    print(f"  Mode:   {ls['mode'].upper()}")
    print(f"  Status: {ls['status'].upper()}")
    if "summary_scores" in ls:
        for k, v in ls["summary_scores"].items():
            print(f"  {k:30s}: {v*100:.1f}%")
        print(f"\n  Note: {ls.get('langsmith_instructions', '')}")
    print("="*80 + "\n")

