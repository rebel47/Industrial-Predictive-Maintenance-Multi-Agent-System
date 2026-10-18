import pytest
import numpy as np
import pandas as pd

from app.analytics.signal_features import (
    compute_time_domain_features,
    compute_frequency_domain_features,
    classify_iso_10816_severity
)
from app.analytics.anomaly_detection import SensorQualityChecker, AnomalyDetector
from app.analytics.fault_classifier import BearingFaultClassifier
from app.analytics.dataset_loader import generate_cwru_benchmark_signals, generate_telemetry_history

def test_time_domain_features():
    sig = np.array([1.0, -1.0, 2.0, -2.0, 0.0], dtype=np.float64)
    feats = compute_time_domain_features(sig)
    assert "rms" in feats
    assert "kurtosis" in feats
    assert "crest_factor" in feats
    assert feats["rms"] > 0

def test_frequency_domain_features():
    fs = 12000.0
    t = np.linspace(0, 1.0, int(fs), endpoint=False)
    # 158 Hz sine wave (BPFI)
    sig = np.sin(2 * np.pi * 158.0 * t)
    f_feats = compute_frequency_domain_features(sig, sampling_rate_hz=fs, shaft_rpm=1750.0)
    assert abs(f_feats["dominant_frequency_hz"] - 158.0) <= 2.0
    assert "BPFI" in f_feats["matched_characteristic"]

def test_iso_10816_severity():
    res_good = classify_iso_10816_severity(1.1)
    assert res_good["zone"] == "Zone A"
    assert res_good["severity"] == "good"
    assert not res_good["action_required"]

    res_danger = classify_iso_10816_severity(5.8)
    assert res_danger["zone"] == "Zone D"
    assert res_danger["severity"] == "unacceptable"
    assert res_danger["action_required"]

def test_sensor_quality_flatline_detection():
    n = 30
    df_stuck = pd.DataFrame({
        "vibration_rms": np.full(n, 2.0),
        "temperature": np.full(n, 60.0)
    })
    quality = SensorQualityChecker.check_telemetry_quality(df_stuck, ["vibration_rms", "temperature"])
    assert not quality["is_acceptable"]
    assert quality["status"] == "unacceptable"
    assert any("flatline" in issue.lower() or "stuck" in issue.lower() for issue in quality["issues"])

def test_bearing_fault_classifier():
    clf = BearingFaultClassifier()
    res = clf.train()
    assert res["macro_f1"] >= 0.85
    
    # Test prediction on outer race signal
    signals = generate_cwru_benchmark_signals()
    pred = clf.predict(signals["OUTER_RACE_FAULT"])
    assert pred["predicted_class"] in clf.CLASSES
    assert pred["confidence"] > 0.5
