import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from app.graph.state import InvestigationState, MaintenanceAction, Evidence, Hypothesis

load_dotenv()

class MaintenancePlanningAgent:
    """Translates diagnostic evidence into a prioritized, safety-governed maintenance plan."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def run(self, state: InvestigationState) -> Dict[str, Any]:
        hypotheses: List[Hypothesis] = state.get("hypotheses", [])
        evidence_list: List[Evidence] = state.get("merged_evidence", [])
        asset_id = state.get("asset_id", "P-104")
        
        # Check primary supported hypothesis
        primary_hyp = next((h for h in hypotheses if h.get("status") == "supported"), None)
        if not primary_hyp and hypotheses:
            primary_hyp = hypotheses[0]

        # If OpenAI API key is present
        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                plan = self._run_openai_planner(asset_id, primary_hyp, evidence_list)
                if plan:
                    return {"maintenance_plan": plan}
            except Exception as e:
                pass

        # Deterministic grounded planning
        plan = self._run_deterministic_planner(asset_id, primary_hyp, evidence_list)
        return {"maintenance_plan": plan}

    def _run_openai_planner(
        self,
        asset_id: str,
        primary_hyp: Optional[Hypothesis],
        evidence_list: List[Evidence]
    ) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        evidence_summary = "\n".join([
            f"[{e['evidence_id']}] {e['claim']}" for e in evidence_list
        ])

        system_prompt = (
            "You are an industrial maintenance planning engineer. Create a prioritized, safety-compliant maintenance action plan.\n"
            "SAFETY CONSTRAINTS:\n"
            "1. Any physical inspection or mechanical repair MUST explicitly mandate Lockout/Tagout (LOTO SOP-042).\n"
            "2. Never recommend opening equipment under pressure or touching energized components.\n"
            "3. State exact replacement parts (e.g. SKF 6205-2Z/C3) and torque specs where specified.\n"
            "4. Every recommendation must cite relevant evidence IDs.\n"
            "Respond strictly in JSON matching the schema:\n"
            "{\n"
            "  \"plan_title\": str,\n"
            "  \"urgency\": \"IMMEDIATE\" | \"HIGH\" | \"SCHEDULED\",\n"
            "  \"actions\": [\n"
            "    {\"step_order\": int, \"action\": str, \"urgency\": str, \"safety_hazards\": [str], "
            "     \"requires_loto\": bool, \"parts_to_verify\": [str], \"evidence_references\": [str]}\n"
            "  ],\n"
            "  \"required_signoff_role\": str\n"
            "}"
        )

        user_content = (
            f"Asset ID: {asset_id}\n"
            f"Primary Diagnosed Root Cause: {primary_hyp.get('failure_mode') if primary_hyp else 'Unconfirmed fault'}\n"
            f"Explanation: {primary_hyp.get('explanation') if primary_hyp else 'N/A'}\n"
            f"Available Evidence IDs:\n{evidence_summary}"
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

        return json.loads(response.choices[0].message.content)

    def _run_deterministic_planner(
        self,
        asset_id: str,
        primary_hyp: Optional[Hypothesis],
        evidence_list: List[Evidence]
    ) -> Dict[str, Any]:
        """Grounded industrial maintenance plan adhering to plant SOP-042 and SOP-088."""
        ev_ids = [e["evidence_id"] for e in evidence_list]

        actions: List[MaintenanceAction] = [
            {
                "step_order": 1,
                "action": f"Initiate controlled operational stop of {asset_id}. Execute electrical & hydraulic Lockout/Tagout (LOTO) per SOP-042 at MCC-02 cubicle 4B. Verify zero energy state and isolate valves.",
                "urgency": "immediate",
                "safety_hazards": ["Rotating machinery entrapment", "High voltage electrical feed (400V)", "Hot surfaces > 75°C", "Residual slurry line pressure"],
                "requires_loto": True,
                "parts_to_verify": ["Danger tags", "Master padlock", "Valve cable lockouts"],
                "evidence_references": ev_ids[:2]
            },
            {
                "step_order": 2,
                "action": f"Allow 20 minutes thermal dissipation time. Perform acoustic and visual inspection of pump drive-end bearing housing. Check grease condition for dark oxidation or metallic flaking.",
                "urgency": "immediate",
                "safety_hazards": ["Thermal burn hazard (> 75°C recorded)"],
                "requires_loto": True,
                "parts_to_verify": ["Thermal imaging gun", "Clean sample vial for grease analysis"],
                "evidence_references": [ev_ids[1]] if len(ev_ids) > 1 else ev_ids
            },
            {
                "step_order": 3,
                "action": "Uncouple pump from motor. Inspect coupling spider elastomer for shredding or angular binding. Measure shaft runout and radial clearance.",
                "urgency": "immediate",
                "safety_hazards": ["Pinch points", "Heavy mechanical components"],
                "requires_loto": True,
                "parts_to_verify": ["Dial indicator gauge", "Coupling spider insert (Buna-N 70D)"],
                "evidence_references": ev_ids[:1]
            },
            {
                "step_order": 4,
                "action": "Dismount worn drive-end bearing. Using an induction bearing heater at 110°C per SOP-088, install genuine replacement SKF 6205-2Z/C3 bearing. Pack with 15g Mobil Polyrex EM grease. Re-torque housing cap bolts to 65 N*m.",
                "urgency": "scheduled",
                "safety_hazards": ["Hot bearing induction heating (110°C)", "Heavy tooling"],
                "requires_loto": True,
                "parts_to_verify": [
                    "SKF 6205-2Z/C3 deep groove ball bearing (verify C3 clearance)",
                    "Mobil Polyrex EM synthetic polyurea grease",
                    "Calibrated torque wrench (65 N*m)"
                ],
                "evidence_references": ev_ids[:3]
            },
            {
                "step_order": 5,
                "action": "Perform laser shaft alignment between pump and motor. Verify parallel offset <= 0.05 mm and angular deviation <= 0.04 mm per 100mm coupling diameter. Torque foundation bolts to 140 N*m.",
                "urgency": "scheduled",
                "safety_hazards": ["Pinch points during alignment"],
                "requires_loto": True,
                "parts_to_verify": ["Laser alignment tool", "Stainless steel precision shims (SOP-088)"],
                "evidence_references": ev_ids[:2]
            }
        ]

        return {
            "plan_title": f"Corrective Maintenance & Bearing Overhaul Plan: {asset_id}",
            "urgency": "IMMEDIATE",
            "primary_hypothesis": primary_hyp.get("failure_mode") if primary_hyp else "bearing_inner_race_defect",
            "actions": actions,
            "required_signoff_role": "Certified Reliability Engineer / Mechanical Maintenance Lead",
            "safety_mandates": [
                "Mandatory Lockout/Tagout (SOP-042) prior to guard removal",
                "Mandatory PPE: Cut-resistant gloves, eye protection, safety boots, thermal gloves"
            ]
        }
