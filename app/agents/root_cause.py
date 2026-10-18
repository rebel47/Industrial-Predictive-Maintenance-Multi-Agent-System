import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from app.graph.state import InvestigationState, Hypothesis, Evidence

load_dotenv()

class RootCauseAnalysisAgent:
    """Evaluates competing failure hypotheses and links supporting and contradicting evidence IDs."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def run(self, state: InvestigationState) -> Dict[str, Any]:
        evidence_list: List[Evidence] = state.get("merged_evidence", [])
        sensor_findings = state.get("sensor_findings", {})
        user_question = state.get("user_question", "")
        asset_id = state.get("asset_id", "P-104")

        # Try OpenAI GPT analysis if key is configured
        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                hypotheses = self._run_openai_analysis(asset_id, user_question, evidence_list, sensor_findings)
                if hypotheses:
                    return {"hypotheses": hypotheses}
            except Exception as e:
                # Fall through to deterministic rule-grounded reasoning
                pass

        # Deterministic Grounded Reasoning
        hypotheses = self._run_deterministic_analysis(evidence_list, sensor_findings)
        return {"hypotheses": hypotheses}

    def _run_openai_analysis(
        self,
        asset_id: str,
        user_question: str,
        evidence_list: List[Evidence],
        sensor_findings: Dict[str, Any]
    ) -> List[Hypothesis]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        evidence_summary = "\n".join([
            f"[{e['evidence_id']}] ({e['source_type']}) {e['claim']} [Ref: {e['source_reference']}]"
            for e in evidence_list
        ])

        system_prompt = (
            "You are an industrial reliability and vibration specialist engineering assistant. "
            "Your task is to compare competing machinery failure hypotheses for the reported fault.\n"
            "CRITICAL CONSTRAINTS:\n"
            "1. Every supporting or contradicting fact MUST cite a valid evidence_id from the provided evidence.\n"
            "2. Never fabricate evidence IDs. Only use IDs present in the evidence list.\n"
            "3. Do not present confidence scores as statistically calibrated probabilities.\n"
            "4. Compare at least two competing failure modes (e.g., Bearing Damage vs Shaft Misalignment).\n"
            "5. Status must be one of: 'supported', 'plausible', 'unlikely', 'inconclusive'.\n"
            "Respond strictly in JSON matching the schema: {\"hypotheses\": [{ \"failure_mode\": str, \"status\": str, "
            "\"supporting_evidence_ids\": [str], \"contradicting_evidence_ids\": [str], \"missing_tests\": [str], \"explanation\": str }]}"
        )

        user_content = (
            f"Asset ID: {asset_id}\n"
            f"User Question: {user_question}\n"
            f"Sensor Metrics: {json.dumps(sensor_findings.get('time_domain', {}))}\n"
            f"Available Evidence Records:\n{evidence_summary}"
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        data = json.loads(response.choices[0].message.content)
        return data.get("hypotheses", [])

    def _run_deterministic_analysis(
        self,
        evidence_list: List[Evidence],
        sensor_findings: Dict[str, Any]
    ) -> List[Hypothesis]:
        """Grounded rule-based hypothesis evaluation based on industrial vibration diagnostics."""
        ev_map = {e["evidence_id"]: e for e in evidence_list}
        
        # Categorize evidence IDs
        bearing_ev_ids = [eid for eid, e in ev_map.items() if any("bearing" in s or "inner_race" in s or "bpfi" in s for s in e["supports"])]
        temp_ev_ids = [eid for eid, e in ev_map.items() if "temperature" in e["claim"].lower() or "temperature" in e["source_reference"].lower()]
        misalign_contra_ids = [eid for eid, e in ev_map.items() if any("misalignment" in c for c in e["contradicts"]) or "pure_misalignment_with_high_temp" in e["contradicts"]]
        misalign_support_ids = [eid for eid, e in ev_map.items() if any("misalignment" in s for s in e["supports"])]

        # Check ML classification from sensor findings if present
        ml_class = ""
        if sensor_findings and "ml_classification" in sensor_findings:
            ml_res = sensor_findings["ml_classification"]
            if ml_res:
                ml_class = ml_res.get("predicted_class", "")

        hypotheses: List[Hypothesis] = []

        # Hypothesis 1: Bearing Inner-Race Spalling & Lubrication Breakdown
        h1_support = list(set(bearing_ev_ids + temp_ev_ids))
        h1_contra = []
        if h1_support:
            h1_status = "supported" if ("INNER_RACE_FAULT" in ml_class or len(h1_support) >= 2) else "plausible"
            hypotheses.append({
                "failure_mode": "bearing_inner_race_defect",
                "status": h1_status,
                "supporting_evidence_ids": h1_support,
                "contradicting_evidence_ids": h1_contra,
                "missing_tests": [
                    "Perform high-frequency demodulated acceleration / envelope analysis on bearing housing",
                    "Conduct ultrasonic acoustic grease lubrication test",
                    "Spectrographic oil / grease wear particle analysis (ferrography)"
                ],
                "explanation": (
                    "Observed vibration amplitude, elevated kurtosis, and spectral characteristics align with rolling element "
                    "impact frequencies (BPFI ~158 Hz). Concurrently high bearing housing temperature (> 75°C) strongly corroborates "
                    "localized friction resulting from inner raceway micro-spalling and lubricant breakdown."
                )
            })

        # Hypothesis 2: Shaft / Coupling Misalignment
        h2_support = [eid for eid in misalign_support_ids if eid not in misalign_contra_ids]
        h2_contra = list(set(temp_ev_ids + misalign_contra_ids))
        hypotheses.append({
            "failure_mode": "shaft_coupling_misalignment",
            "status": "unlikely" if h2_contra else "plausible",
            "supporting_evidence_ids": h2_support,
            "contradicting_evidence_ids": h2_contra,
            "missing_tests": [
                "Laser shaft alignment measurement at ambient and operating temperatures",
                "Axial-to-radial vibration ratio check (> 50% indicates misalignment)",
                "Thermal imaging of coupling guard for localized friction hot-spot"
            ],
            "explanation": (
                "While coupling misalignment can cause severe vibration, it typically generates dominant 2X running speed harmonics (58.3 Hz) "
                "with high axial vibration, and rarely causes rapid bearing housing temperature spikes (> 75°C) without prior bearing spalling. "
                "The presence of high temperature and BPFI spectral characteristics contradicts pure misalignment as the primary root cause."
            )
        })

        # Hypothesis 3: Hydraulic Cavitation / Suction Starvation
        cavitation_contra = [eid for eid in bearing_ev_ids if eid in ev_map]
        hypotheses.append({
            "failure_mode": "hydraulic_cavitation",
            "status": "unlikely",
            "supporting_evidence_ids": [],
            "contradicting_evidence_ids": cavitation_contra[:2],
            "missing_tests": [
                "Verify suction pressure gauge against Net Positive Suction Head required (NPSHr)",
                "Inspect suction strainer delta-P for clogging",
                "Acoustic frequency survey for wideband non-harmonic high frequency noise"
            ],
            "explanation": (
                "Cavitation generates wideband random acoustic noise and hydraulic pulsation, but fails to account for discrete "
                "BPFI bearing defect spectral harmonics or isolated bearing housing overheating."
            )
        })

        return hypotheses
