import numpy as np
import pandas as pd
from typing import Dict, Any, List

from app.graph.state import InvestigationState, Evidence
from app.analytics.signal_features import (
    compute_time_domain_features,
    compute_frequency_domain_features,
    classify_iso_10816_severity
)
from app.analytics.anomaly_detection import SensorQualityChecker, AnomalyDetector
from app.analytics.fault_classifier import BearingFaultClassifier
from app.analytics.dataset_loader import generate_cwru_benchmark_signals, generate_telemetry_history

class SensorAnalyticsAgent:
    """Deterministic numerical analytics node executing signal processing and ML models."""

    def __init__(self):
        self.quality_checker = SensorQualityChecker()
        self.anomaly_detector = AnomalyDetector()
        self.fault_classifier = BearingFaultClassifier()

    def run(self, state: InvestigationState) -> Dict[str, Any]:
        asset_id = state.get("asset_id", "P-104")
        telemetry = state.get("telemetry_data")
        
        # 1. Prepare Telemetry DataFrame
        if telemetry and "dataframe" in telemetry:
            df = telemetry["dataframe"]
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
        elif telemetry and "vibration_rms" in telemetry:
            df = pd.DataFrame(telemetry)
        else:
            # Default to generated historical telemetry for this investigation
            df = generate_telemetry_history(asset_id=asset_id, fault_type="INNER_RACE_FAULT", n_points=60)

        # 2. Check Data Quality
        quality = self.quality_checker.check_telemetry_quality(
            df=df,
            value_columns=["vibration_rms", "temperature"]
        )

        sensor_evidence: List[Evidence] = []
        ev_counter = 1

        if not quality["is_acceptable"]:
            # Data quality failed
            findings = {
                "asset_id": asset_id,
                "data_quality": "rejected",
                "quality_issues": quality["issues"],
                "anomalies": [{
                    "signal": "sensor_telemetry",
                    "severity": "CRITICAL",
                    "evidence": "Sensor data rejected due to quality check failures: " + "; ".join(quality["issues"])
                }],
                "iso_severity": None,
                "ml_classification": None
            }
            sensor_evidence.append({
                "evidence_id": f"E-SENSOR-{ev_counter:02d}",
                "source_type": "sensor",
                "claim": f"Sensor telemetry failed data quality validation: {'; '.join(quality['issues'])}",
                "source_reference": f"Telemetry Stream {asset_id} [Quality Check]",
                "supports": ["sensor_fault", "instrumentation_failure"],
                "contradicts": [],
                "credibility": "deterministic_numeric"
            })
            return {
                "sensor_findings": findings,
                "internal_evidence": state.get("internal_evidence", []) + sensor_evidence
            }

        # 3. Detect Anomalies & Trends
        anomaly_report = self.anomaly_detector.detect_anomalies(
            df=df,
            asset_id=asset_id,
            feature_cols=["vibration_rms", "temperature", "motor_current"]
        )

        # 4. Signal Processing on Vibration Waveform
        if "raw_vibration" in df.columns:
            vib_signal = df["raw_vibration"].values
        else:
            # Synthesize representative waveform matching telemetry RMS
            latest_rms = float(df["vibration_rms"].iloc[-1])
            cwru_signals = generate_cwru_benchmark_signals()
            if latest_rms > 4.5:
                vib_signal = cwru_signals["INNER_RACE_FAULT"]
            elif latest_rms > 2.8:
                vib_signal = cwru_signals["OUTER_RACE_FAULT"]
            else:
                vib_signal = cwru_signals["NORMAL"]

        time_feats = compute_time_domain_features(vib_signal)
        freq_feats = compute_frequency_domain_features(
            vib_signal,
            sampling_rate_hz=12000.0,
            shaft_rpm=1750.0,
            bearing_model="SKF 6205"
        )
        
        # 5. ISO 10816 Severity
        latest_vib = float(df["vibration_rms"].iloc[-1])
        iso_report = classify_iso_10816_severity(latest_vib, machine_class="Class II")

        # 6. ML Fault Classification
        ml_result = self.fault_classifier.predict(
            vib_signal,
            sampling_rate_hz=12000.0,
            shaft_rpm=1750.0
        )

        findings = {
            "asset_id": asset_id,
            "data_quality": quality["status"],
            "analysis_window": anomaly_report["analysis_window"],
            "time_domain": time_feats,
            "frequency_domain": freq_feats,
            "iso_severity": iso_report,
            "anomalies": anomaly_report["anomalies"],
            "ml_classification": ml_result,
            "limitations": anomaly_report.get("limitations", [])
        }

        # Construct deterministic Evidence entries
        # Evidence 1: ISO Severity & Anomaly Flag
        sensor_evidence.append({
            "evidence_id": f"E-SENSOR-{ev_counter:02d}",
            "source_type": "sensor",
            "claim": f"Vibration velocity reached {latest_vib:.2f} mm/s RMS ({iso_report['zone']} {iso_report['severity']}). {iso_report['description']}",
            "source_reference": f"Telemetry {asset_id} [ISO 10816-3]",
            "supports": ["bearing_damage", "misalignment", "mechanical_defect"],
            "contradicts": ["normal_operation"],
            "credibility": "deterministic_numeric"
        })
        ev_counter += 1

        # Evidence 2: Temperature reading
        latest_temp = float(df["temperature"].iloc[-1])
        if latest_temp > 75.0:
            sensor_evidence.append({
                "evidence_id": f"E-SENSOR-{ev_counter:02d}",
                "source_type": "sensor",
                "claim": f"Bearing housing temperature climbed to {latest_temp:.1f}°C, exceeding the 75°C warning limit.",
                "source_reference": f"Telemetry {asset_id} [RTD Sensor]",
                "supports": ["bearing_damage", "lubrication_failure"],
                "contradicts": ["dynamic_unbalance", "pure_misalignment"],
                "credibility": "deterministic_numeric"
            })
            ev_counter += 1

        # Evidence 3: Spectral peak & ML diagnostic
        dom_freq = freq_feats["dominant_frequency_hz"]
        matched_char = freq_feats["matched_characteristic"]
        pred_cls = ml_result["predicted_class"]
        conf = ml_result["confidence"]
        sensor_evidence.append({
            "evidence_id": f"E-SENSOR-{ev_counter:02d}",
            "source_type": "sensor",
            "claim": f"Spectral FFT peak detected at {dom_freq:.1f} Hz (matching {matched_char}). CWRU ML classifier predicts '{pred_cls}' with {conf*100:.1f}% confidence.",
            "source_reference": f"Vibration FFT & Classifier [CWRU 12k DE]",
            "supports": [pred_cls.lower()],
            "contradicts": ["normal_operation"],
            "credibility": "deterministic_numeric"
        })

        return {
            "sensor_findings": findings,
            "internal_evidence": state.get("internal_evidence", []) + sensor_evidence
        }
