import numpy as np
from scipy import stats, signal
from typing import Dict, Any, List, Tuple, Optional

# Standard characteristic defect multipliers for SKF 6205 deep-groove ball bearing
BEARING_COEFFICIENTS = {
    "SKF 6205": {
        "BPFO": 3.585,  # Ball Pass Frequency Outer Race multiplier
        "BPFI": 5.415,  # Ball Pass Frequency Inner Race multiplier
        "BSF": 2.322,   # Ball Spin Frequency multiplier
        "FTF": 0.398    # Fundamental Train / Cage Frequency multiplier
    }
}

def compute_time_domain_features(time_series: np.ndarray) -> Dict[str, float]:
    """
    Extract standard industrial time-domain statistical features.
    
    Args:
        time_series: 1D array of vibration or sensor signal values.
        
    Returns:
        Dictionary of statistical metrics.
    """
    if len(time_series) == 0:
        return {
            "mean": 0.0, "std": 0.0, "rms": 0.0, "peak_to_peak": 0.0,
            "crest_factor": 0.0, "kurtosis": 0.0, "skewness": 0.0, "shape_factor": 0.0
        }
    
    arr = np.asarray(time_series, dtype=np.float64)
    # Remove NaN / Inf if any
    valid_mask = np.isfinite(arr)
    if not np.any(valid_mask):
        return {
            "mean": 0.0, "std": 0.0, "rms": 0.0, "peak_to_peak": 0.0,
            "crest_factor": 0.0, "kurtosis": 0.0, "skewness": 0.0, "shape_factor": 0.0
        }
    arr = arr[valid_mask]

    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    rms_val = float(np.sqrt(np.mean(arr ** 2)))
    peak_val = float(np.max(np.abs(arr)))
    peak_to_peak = float(np.ptp(arr))
    crest_factor = float(peak_val / (rms_val + 1e-9))
    kurtosis_val = float(stats.kurtosis(arr, fisher=False))  # Pearson kurtosis (Normal = 3.0)
    skewness_val = float(stats.skew(arr))
    mean_abs = float(np.mean(np.abs(arr)))
    shape_factor = float(rms_val / (mean_abs + 1e-9))

    return {
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "rms": round(rms_val, 4),
        "peak": round(peak_val, 4),
        "peak_to_peak": round(peak_to_peak, 4),
        "crest_factor": round(crest_factor, 4),
        "kurtosis": round(kurtosis_val, 4),
        "skewness": round(skewness_val, 4),
        "shape_factor": round(shape_factor, 4)
    }

def compute_frequency_domain_features(
    time_series: np.ndarray,
    sampling_rate_hz: float = 12000.0,
    shaft_rpm: float = 1750.0,
    bearing_model: str = "SKF 6205"
) -> Dict[str, Any]:
    """
    Extract frequency-domain spectrum features, shaft harmonics, and bearing fault indicators.
    
    Args:
        time_series: 1D vibration array.
        sampling_rate_hz: Sampling frequency in Hertz (default 12 kHz for CWRU).
        shaft_rpm: Machine rotating speed in revolutions per minute.
        bearing_model: Key into BEARING_COEFFICIENTS table.
        
    Returns:
        Dictionary containing spectral peaks, shaft harmonics (1X, 2X), and fault frequencies.
    """
    arr = np.asarray(time_series, dtype=np.float64)
    n = len(arr)
    if n < 64:
        return {
            "dominant_frequency_hz": 0.0,
            "dominant_amplitude": 0.0,
            "shaft_running_hz": round(shaft_rpm / 60.0, 2),
            "spectral_peaks": []
        }
    
    # Detrend and apply Hanning window
    detrended = signal.detrend(arr)
    window = np.hanning(n)
    windowed_signal = detrended * window
    
    # Compute single-sided FFT amplitude spectrum
    fft_vals = np.fft.rfft(windowed_signal)
    fft_freqs = np.fft.rfftfreq(n, d=1.0 / sampling_rate_hz)
    amplitudes = (2.0 / np.sum(window)) * np.abs(fft_vals)
    
    # Find top 5 dominant peaks
    peak_indices, _ = signal.find_peaks(amplitudes, height=np.max(amplitudes) * 0.1, distance=10)
    sorted_peak_indices = sorted(peak_indices, key=lambda idx: amplitudes[idx], reverse=True)[:5]
    
    top_peaks = [
        {"frequency_hz": round(float(fft_freqs[idx]), 2), "amplitude": round(float(amplitudes[idx]), 4)}
        for idx in sorted_peak_indices
    ]
    
    dom_freq = top_peaks[0]["frequency_hz"] if top_peaks else 0.0
    dom_amp = top_peaks[0]["amplitude"] if top_peaks else 0.0

    # Calculate characteristic shaft and bearing frequencies
    fr = shaft_rpm / 60.0  # 1X shaft frequency (e.g. 29.17 Hz for 1750 RPM)
    harmonics = {
        "1X_shaft_hz": round(fr, 2),
        "2X_misalignment_hz": round(2.0 * fr, 2),
        "3X_shaft_hz": round(3.0 * fr, 2)
    }
    
    coeffs = BEARING_COEFFICIENTS.get(bearing_model, BEARING_COEFFICIENTS["SKF 6205"])
    fault_frequencies = {
        "BPFO_outer_race_hz": round(coeffs["BPFO"] * fr, 2),
        "BPFI_inner_race_hz": round(coeffs["BPFI"] * fr, 2),
        "BSF_ball_spin_hz": round(coeffs["BSF"] * fr, 2),
        "FTF_cage_hz": round(coeffs["FTF"] * fr, 2)
    }
    
    # Check if dominant frequency matches any characteristic fault frequency (within 3% tolerance)
    matched_characteristic = "Broadband / Unclassified"
    for name, freq in {**harmonics, **fault_frequencies}.items():
        if abs(dom_freq - freq) <= max(2.5, 0.035 * freq):
            matched_characteristic = name
            break
            
    return {
        "dominant_frequency_hz": dom_freq,
        "dominant_amplitude": dom_amp,
        "matched_characteristic": matched_characteristic,
        "shaft_running_hz": round(fr, 2),
        "bearing_fault_frequencies": fault_frequencies,
        "harmonics": harmonics,
        "top_peaks": top_peaks
    }

def classify_iso_10816_severity(vibration_rms_velocity: float, machine_class: str = "Class II") -> Dict[str, Any]:
    """
    Classify vibration severity according to ISO 10816-3 standard.
    
    Machine Class II: Medium-sized machines (15 kW to 300 kW electric motors or pumps on rigid foundations).
    
    Zones:
      Zone A: < 1.4 mm/s  (Good / New machine)
      Zone B: 1.4 - 2.8 mm/s (Acceptable for long-term continuous operation)
      Zone C: 2.8 - 4.5 mm/s (Unsatisfactory / Maintenance alert)
      Zone D: > 4.5 mm/s  (Unacceptable / Danger / Immediate shutdown)
    """
    rms = float(vibration_rms_velocity)
    if rms < 1.4:
        zone = "Zone A"
        severity = "good"
        description = "Vibration within newly commissioned or good operating limits."
        action_required = False
    elif rms <= 2.8:
        zone = "Zone B"
        severity = "acceptable"
        description = "Vibration acceptable for unrestricted long-term operation."
        action_required = False
    elif rms <= 4.5:
        zone = "Zone C"
        severity = "unsatisfactory"
        description = "Unsatisfactory vibration. Warning threshold exceeded; plan remedial maintenance."
        action_required = True
    else:
        zone = "Zone D"
        severity = "unacceptable"
        description = "Unacceptable vibration severity. Critical threshold exceeded; immediate inspection or shutdown mandated."
        action_required = True

    return {
        "standard": "ISO 10816-3",
        "machine_class": machine_class,
        "vibration_rms_mm_s": round(rms, 3),
        "zone": zone,
        "severity": severity,
        "description": description,
        "action_required": action_required
    }
