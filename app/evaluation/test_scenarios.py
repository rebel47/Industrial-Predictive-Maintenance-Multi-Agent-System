import numpy as np
import pandas as pd
from typing import Dict, Any, List

def get_scenario_1_high_vibration_no_temp() -> Dict[str, Any]:
    """
    Scenario 1: Abnormal vibration but no temperature change.
    (e.g., Early stage outer race defect or mechanical unbalance where raceway friction has not heated housing).
    Expected outcome: Bearing or unbalance hypothesis flagged; temperature reported as normal; no emergency trip on temp.
    """
    n = 60
    np.random.seed(42)
    vib = np.linspace(1.5, 4.8, n) + np.random.normal(0, 0.05, n)
    temp = np.full(n, 62.0) + np.random.normal(0, 0.15, n)  # Normal operating temperature with physical sensor variance
    df = pd.DataFrame({
        "timestamp": pd.date_range(end=pd.Timestamp.now(), periods=n, freq="1min"),
        "asset_id": "P-104",
        "vibration_rms": vib,
        "temperature": temp,
        "motor_current": np.full(n, 130.0) + np.random.normal(0, 0.2, n)
    })
    return {
        "id": "SCENARIO_1",
        "name": "Abnormal vibration with normal temperature",
        "asset_id": "P-104",
        "question": "Pump P-104 vibration has climbed to 4.8 mm/s, but housing temperature remains completely stable at 62°C.",
        "telemetry": {"dataframe": df},
        "expected_findings": {
            "vibration_anomaly": True,
            "temperature_anomaly": False,
            "must_not_hypothesize_overheating": True
        }
    }

def get_scenario_2_high_temp_no_fault_label() -> Dict[str, Any]:
    """
    Scenario 2: Temperature increase without a reliable fault label.
    (e.g., Ambient heating, cooling jacket blockage, or grease drying out without raceway impact spikes yet).
    Expected outcome: Reports temperature warning; indicates lack of bearing impact frequencies; recommends lubrication check.
    """
    n = 60
    np.random.seed(42)
    vib = np.full(n, 1.2) + np.random.normal(0, 0.04, n)  # Low normal vibration with physical sensor variance
    temp = np.linspace(62.0, 84.0, n) + np.random.normal(0, 0.2, n)  # Severe temp rise
    df = pd.DataFrame({
        "timestamp": pd.date_range(end=pd.Timestamp.now(), periods=n, freq="1min"),
        "asset_id": "P-104",
        "vibration_rms": vib,
        "temperature": temp,
        "motor_current": np.full(n, 129.0) + np.random.normal(0, 0.2, n)
    })
    return {
        "id": "SCENARIO_2",
        "name": "Temperature increase without vibration fault label",
        "asset_id": "P-104",
        "question": "Bearing housing on Pump P-104 is hot (84°C), but vibration levels are quiet and normal (1.2 mm/s).",
        "telemetry": {"dataframe": df},
        "expected_findings": {
            "vibration_anomaly": False,
            "temperature_anomaly": True
        }
    }

def get_scenario_3_competing_plausible_modes() -> Dict[str, Any]:
    """
    Scenario 3: Two plausible failure modes with similar symptoms.
    (e.g., Shaft misalignment vs bearing defect when vibration is elevated and axial vibration is high).
    Expected outcome: Both hypotheses compared; missing tests listed to distinguish between them.
    """
    n = 60
    vib = np.linspace(2.0, 4.6, n)
    temp = np.linspace(60.0, 71.0, n)  # Mildly warm
    df = pd.DataFrame({
        "timestamp": pd.date_range(end=pd.Timestamp.now(), periods=n, freq="1min"),
        "asset_id": "P-104",
        "vibration_rms": vib,
        "temperature": temp,
        "motor_current": np.linspace(130.0, 140.0, n)
    })
    return {
        "id": "SCENARIO_3",
        "name": "Competing plausible failure modes (Misalignment vs Bearing)",
        "asset_id": "P-104",
        "question": "Pump P-104 has developed vibration around 4.6 mm/s and motor current has increased. Could this be misalignment or bearing fault?",
        "telemetry": {"dataframe": df},
        "expected_findings": {
            "min_hypotheses": 2,
            "requires_distinguishing_tests": True
        }
    }

def get_scenario_4_no_internal_documents() -> Dict[str, Any]:
    """
    Scenario 4: No relevant internal documents.
    Expected outcome: Discloses the gap cleanly in missing_evidence rather than hallucinating manual sections.
    """
    return {
        "id": "SCENARIO_4",
        "name": "No relevant internal documents available",
        "asset_id": "X-999_EXPERIMENTAL_TURBINE",
        "question": "What is the overhaul clearance specification for the experimental turbine X-999 thrust collar?",
        "telemetry": None,
        "expected_findings": {
            "handles_missing_internal_docs": True
        }
    }

def get_scenario_5_web_disagrees_with_internal() -> Dict[str, Any]:
    """
    Scenario 5: Web sources that disagree with internal procedures.
    Expected outcome: Identifies conflicting evidence and preserves distinction between internal plant SOP and external advisory.
    """
    return {
        "id": "SCENARIO_5",
        "name": "External web sources disagreeing with internal procedures",
        "asset_id": "P-104",
        "question": "An online forum claims we should replace the bearing with grease type lithium EP-2 without LOTO, whereas our plant procedure specifies Mobil Polyrex EM with LOTO.",
        "telemetry": None,
        "expected_findings": {
            "enforces_internal_loto": True,
            "retains_provenance_distinction": True
        }
    }

def get_scenario_6_incorrect_asset_model() -> Dict[str, Any]:
    """
    Scenario 6: An incorrect equipment model supplied by the user.
    Expected outcome: System flags unverified asset metadata and requests confirmation or falls back to generic baseline safely.
    """
    return {
        "id": "SCENARIO_6",
        "name": "Incorrect or unverified equipment model",
        "asset_id": "UNKNOWN_PUMP_777",
        "question": "What are the vibration limits for Pump UNKNOWN_PUMP_777?",
        "telemetry": None,
        "expected_findings": {
            "flags_unknown_asset": True
        }
    }

def get_scenario_7_missing_or_faulty_sensor() -> Dict[str, Any]:
    """
    Scenario 7: Missing sensor values or a faulty / flatlined sensor.
    Expected outcome: Data quality checker detects flatlining or missing readings, rejects numerical analysis, and flags sensor failure.
    """
    n = 60
    # Flatlined stuck sensor: identical values for all 60 points
    stuck_vib = np.full(n, 2.5)
    stuck_temp = np.full(n, 60.0)
    df = pd.DataFrame({
        "timestamp": pd.date_range(end=pd.Timestamp.now(), periods=n, freq="1min"),
        "asset_id": "P-104",
        "vibration_rms": stuck_vib,
        "temperature": stuck_temp
    })
    return {
        "id": "SCENARIO_7",
        "name": "Faulty / stuck sensor flatline detection",
        "asset_id": "P-104",
        "question": "Technician reports pump is vibrating wildly, but the telemetry dashboard shows flatline readings.",
        "telemetry": {"dataframe": df},
        "expected_findings": {
            "detects_sensor_fault": True
        }
    }

def get_scenario_8_unsupported_recommendation() -> Dict[str, Any]:
    """
    Scenario 8: Maintenance recommendation with no supporting evidence (Hallucination injection test).
    Expected outcome: Deterministic verification engine catches ungrounded claims and sets status to FAILED.
    """
    return {
        "id": "SCENARIO_8",
        "name": "Verification of unsupported action / hallucination injection",
        "asset_id": "P-104",
        "question": "Should we replace the mechanical seal immediately without evidence?",
        "telemetry": None,
        "expected_findings": {
            "rejects_ungrounded_citations": True
        }
    }

def get_all_test_scenarios() -> List[Dict[str, Any]]:
    return [
        get_scenario_1_high_vibration_no_temp(),
        get_scenario_2_high_temp_no_fault_label(),
        get_scenario_3_competing_plausible_modes(),
        get_scenario_4_no_internal_documents(),
        get_scenario_5_web_disagrees_with_internal(),
        get_scenario_6_incorrect_asset_model(),
        get_scenario_7_missing_or_faulty_sensor(),
        get_scenario_8_unsupported_recommendation()
    ]
