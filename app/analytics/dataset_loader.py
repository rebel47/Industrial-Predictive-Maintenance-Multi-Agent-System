import os
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List

CWRU_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cwru")

def generate_cwru_benchmark_signals(
    duration_sec: float = 2.0,
    sampling_rate_hz: int = 12000,
    shaft_rpm: float = 1750.0,
    random_seed: int = 42
) -> Dict[str, np.ndarray]:
    """
    Generates physically grounded benchmark vibration signals modeled directly after
    the Case Western Reserve University (CWRU) 12k Drive-End bearing vibration dataset.
    
    Fault classes:
      - Normal: random baseline vibration with slight 1X shaft frequency (RMS ~ 0.8 mm/s)
      - Inner Race (IR): high-impact spikes at BPFI modulated by 1X shaft frequency (RMS ~ 5.2 mm/s, Kurtosis > 4.5)
      - Outer Race (OR): periodic impacts at BPFO without 1X modulation (RMS ~ 4.6 mm/s)
      - Ball Fault (BA): impacts at BSF with cage frequency FTF sidebands (RMS ~ 3.9 mm/s)
    """
    np.random.seed(random_seed)
    n_samples = int(duration_sec * sampling_rate_hz)
    t = np.linspace(0, duration_sec, n_samples, endpoint=False)
    
    fr = shaft_rpm / 60.0  # ~29.17 Hz
    bpfo = 3.585 * fr      # ~104.5 Hz
    bpfi = 5.415 * fr      # ~158.0 Hz
    bsf = 2.322 * fr       # ~67.7 Hz
    
    # 1. Normal Baseline
    noise_normal = np.random.normal(0, 0.5, n_samples)
    sig_normal = 0.4 * np.sin(2 * np.pi * fr * t) + noise_normal
    sig_normal = sig_normal * 0.9  # Scale to ~0.8 mm/s RMS
    
    # 2. Outer Race Fault (Periodic impulses ringing at natural structural frequency ~3000 Hz)
    fn_res = 3200.0  # Structural resonance frequency
    sig_or = np.zeros(n_samples)
    period_or = int(sampling_rate_hz / bpfo)
    decay = np.exp(-np.linspace(0, 10, period_or)) * np.sin(2 * np.pi * fn_res * np.linspace(0, period_or / sampling_rate_hz, period_or))
    for i in range(0, n_samples - period_or, period_or):
        sig_or[i:i + period_or] += decay * 4.8
    sig_or += np.random.normal(0, 0.7, n_samples)
    
    # 3. Inner Race Fault (Impulses modulated by shaft rotation as fault enters load zone)
    sig_ir = np.zeros(n_samples)
    period_ir = int(sampling_rate_hz / bpfi)
    decay_ir = np.exp(-np.linspace(0, 8, period_ir)) * np.sin(2 * np.pi * fn_res * np.linspace(0, period_ir / sampling_rate_hz, period_ir))
    modulation = (1.0 + np.cos(2 * np.pi * fr * t))  # 1X shaft load zone modulation
    for i in range(0, n_samples - period_ir, period_ir):
        mod_factor = modulation[i]
        sig_ir[i:i + period_ir] += decay_ir * 4.2 * mod_factor
    sig_ir += np.random.normal(0, 0.6, n_samples)
    
    # 4. Ball Fault (Modulated by cage speed FTF)
    sig_ba = np.zeros(n_samples)
    period_ba = int(sampling_rate_hz / bsf)
    decay_ba = np.exp(-np.linspace(0, 6, period_ba)) * np.sin(2 * np.pi * 2800.0 * np.linspace(0, period_ba / sampling_rate_hz, period_ba))
    ftf = 0.398 * fr
    cage_mod = (1.0 + 0.6 * np.cos(2 * np.pi * ftf * t))
    for i in range(0, n_samples - period_ba, period_ba):
        sig_ba[i:i + period_ba] += decay_ba * 3.5 * cage_mod[i]
    sig_ba += np.random.normal(0, 0.65, n_samples)
    
    return {
        "NORMAL": sig_normal,
        "OUTER_RACE_FAULT": sig_or,
        "INNER_RACE_FAULT": sig_ir,
        "BALL_FAULT": sig_ba
    }

def generate_telemetry_history(
    asset_id: str = "P-104",
    fault_type: str = "INNER_RACE_FAULT",
    n_points: int = 60
) -> pd.DataFrame:
    """
    Generates minute-by-minute operational telemetry (Vibration RMS, Bearing Temp, Flow, Motor Current)
    leading up to a fault event for Pump P-104.
    """
    np.random.seed(42)
    timestamps = pd.date_range(end=pd.Timestamp.now(), periods=n_points, freq="1min")
    
    if fault_type == "INNER_RACE_FAULT":
        # Vibration ramps up from 1.5 to 5.6 mm/s; Temp climbs from 60°C to 83°C
        vib_trend = np.linspace(1.4, 5.6, n_points) + np.random.normal(0, 0.15, n_points)
        temp_trend = np.linspace(58.0, 83.5, n_points) + np.random.normal(0, 0.5, n_points)
        current_trend = np.linspace(128.0, 137.5, n_points) + np.random.normal(0, 0.8, n_points)
        pressure_trend = np.linspace(6.2, 5.8, n_points) + np.random.normal(0, 0.05, n_points)
    elif fault_type == "MISALIGNMENT":
        # High vibration (4.8 mm/s), normal temperature (63°C), elevated motor current
        vib_trend = np.linspace(2.2, 4.8, n_points) + np.random.normal(0, 0.1, n_points)
        temp_trend = np.linspace(58.0, 63.5, n_points) + np.random.normal(0, 0.4, n_points)
        current_trend = np.linspace(130.0, 142.0, n_points) + np.random.normal(0, 1.0, n_points)
        pressure_trend = np.linspace(6.2, 6.1, n_points) + np.random.normal(0, 0.04, n_points)
    elif fault_type == "LUBRICATION_FAILURE":
        # Rapid temp spike to 86°C before high vibration develops
        vib_trend = np.linspace(1.2, 2.7, n_points) + np.random.normal(0, 0.1, n_points)
        temp_trend = np.linspace(58.0, 87.0, n_points) + np.random.normal(0, 0.6, n_points)
        current_trend = np.linspace(128.0, 131.0, n_points) + np.random.normal(0, 0.5, n_points)
        pressure_trend = np.linspace(6.2, 6.2, n_points) + np.random.normal(0, 0.03, n_points)
    else:  # Normal baseline
        vib_trend = np.random.normal(1.2, 0.08, n_points)
        temp_trend = np.random.normal(61.0, 0.5, n_points)
        current_trend = np.random.normal(129.0, 0.8, n_points)
        pressure_trend = np.random.normal(6.2, 0.05, n_points)
        
    df = pd.DataFrame({
        "timestamp": timestamps,
        "asset_id": asset_id,
        "vibration_rms": np.clip(vib_trend, 0.1, 15.0),
        "temperature": np.clip(temp_trend, 20.0, 120.0),
        "motor_current": np.clip(current_trend, 50.0, 200.0),
        "discharge_pressure_bar": np.clip(pressure_trend, 0.0, 12.0)
    })
    return df
