import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import IsolationForest

class SensorQualityChecker:
    """Validates industrial sensor data integrity and checks for sensor faults."""
    
    @staticmethod
    def check_telemetry_quality(
        df: pd.DataFrame,
        value_columns: List[str],
        max_missing_ratio: float = 0.20,
        flatline_window: int = 15
    ) -> Dict[str, Any]:
        """
        Check for missing values, flatlining (stuck sensor), and out-of-range sensor drift.
        """
        issues = []
        is_acceptable = True
        
        if df.empty:
            return {
                "status": "rejected",
                "is_acceptable": False,
                "issues": ["Empty telemetry dataset received."],
                "missing_ratios": {}
            }
            
        missing_ratios = {}
        for col in value_columns:
            if col not in df.columns:
                issues.append(f"Missing required sensor column '{col}'.")
                is_acceptable = False
                continue
                
            series = df[col]
            missing_cnt = series.isna().sum()
            ratio = float(missing_cnt / len(df))
            missing_ratios[col] = round(ratio, 4)
            
            if ratio > max_missing_ratio:
                issues.append(f"Sensor '{col}' has {ratio*100:.1f}% missing readings (threshold: {max_missing_ratio*100}%).")
                is_acceptable = False
                
            # Check for flatline (frozen sensor)
            valid_vals = series.dropna().values
            if len(valid_vals) >= flatline_window:
                # Rolling difference
                diffs = np.diff(valid_vals)
                zero_diff_streak = 0
                max_streak = 0
                for d in diffs:
                    if abs(d) < 1e-7:
                        zero_diff_streak += 1
                        max_streak = max(max_streak, zero_diff_streak)
                    else:
                        zero_diff_streak = 0
                        
                if max_streak >= flatline_window:
                    issues.append(f"Sensor '{col}' exhibits stuck signal / flatline for {max_streak} consecutive readings.")
                    is_acceptable = False

        status = "acceptable" if is_acceptable and not issues else ("degraded" if is_acceptable else "unacceptable")
        return {
            "status": status,
            "is_acceptable": is_acceptable,
            "issues": issues,
            "missing_ratios": missing_ratios
        }

class AnomalyDetector:
    """Combines statistical baseline and Isolation Forest for industrial anomaly detection."""
    
    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.contamination = contamination
        self.iso_forest = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        self.is_fitted = False
        
    def fit_baseline(self, baseline_df: pd.DataFrame, feature_cols: List[str]):
        """Fit Isolation Forest on historical healthy operating telemetry."""
        clean_data = baseline_df[feature_cols].dropna().values
        if len(clean_data) > 50:
            self.iso_forest.fit(clean_data)
            self.is_fitted = True

    def detect_anomalies(
        self,
        df: pd.DataFrame,
        asset_id: str,
        feature_cols: List[str] = ["vibration_rms", "temperature", "motor_current"]
    ) -> Dict[str, Any]:
        """
        Evaluate recent time-series telemetry against statistical bounds and trained models.
        """
        available_cols = [c for c in feature_cols if c in df.columns]
        if not available_cols:
            return {
                "asset_id": asset_id,
                "analysis_window": "unknown",
                "anomalies": [],
                "data_quality": "unacceptable",
                "limitations": ["No valid telemetry columns found for anomaly detection."]
            }

        anomalies = []
        limitations = []
        
        # 1. Statistical Threshold & Rate-of-Change Checks
        for col in available_cols:
            series = df[col].dropna()
            if len(series) < 5:
                limitations.append(f"Insufficient samples for '{col}' ({len(series)} readings).")
                continue
                
            mean = series.mean()
            std = series.std(ddof=1) if len(series) > 1 else 0.0
            latest = series.iloc[-1]
            z_score = float((latest - mean) / (std + 1e-6))
            
            # Rate of change between first half and second half of window
            half = len(series) // 2
            mean_first = series.iloc[:half].mean()
            mean_recent = series.iloc[half:].mean()
            pct_change = float(((mean_recent - mean_first) / (abs(mean_first) + 1e-6)) * 100)
            
            # Vibration-specific rule
            if "vibration" in col.lower():
                if latest > 4.5:
                    anomalies.append({
                        "signal": col,
                        "severity": "CRITICAL",
                        "current_value": round(float(latest), 3),
                        "unit": "mm/s RMS",
                        "z_score": round(z_score, 2),
                        "evidence": f"Vibration velocity of {latest:.2f} mm/s exceeds ISO 10816 Zone D trip limit (4.5 mm/s)."
                    })
                elif latest > 2.8:
                    anomalies.append({
                        "signal": col,
                        "severity": "WARNING",
                        "current_value": round(float(latest), 3),
                        "unit": "mm/s RMS",
                        "z_score": round(z_score, 2),
                        "evidence": f"Vibration velocity of {latest:.2f} mm/s exceeds ISO 10816 Zone C alert limit (2.8 mm/s)."
                    })
                    
            # Temperature-specific rule
            elif "temp" in col.lower():
                if latest > 85.0:
                    anomalies.append({
                        "signal": col,
                        "severity": "CRITICAL",
                        "current_value": round(float(latest), 2),
                        "unit": "°C",
                        "z_score": round(z_score, 2),
                        "evidence": f"Bearing temperature of {latest:.1f}°C exceeds emergency trip threshold (85.0°C)."
                    })
                elif latest > 75.0 or pct_change > 15.0:
                    anomalies.append({
                        "signal": col,
                        "severity": "WARNING",
                        "current_value": round(float(latest), 2),
                        "unit": "°C",
                        "z_score": round(z_score, 2),
                        "evidence": f"Bearing temperature of {latest:.1f}°C is elevated (up {pct_change:.1f}% over observation window)."
                    })
                    
            # Generic statistical outlier
            elif abs(z_score) > 3.0:
                anomalies.append({
                    "signal": col,
                    "severity": "WARNING",
                    "current_value": round(float(latest), 2),
                    "unit": "units",
                    "z_score": round(z_score, 2),
                    "evidence": f"Statistical outlier detected on '{col}' (Z-score: {z_score:.2f})."
                })

        # 2. Multidimensional Isolation Forest Anomaly Detection
        iso_flag = False
        iso_score = 0.0
        feature_data = df[available_cols].dropna().values
        if len(feature_data) >= 20:
            if not self.is_fitted:
                # Fit on initial segment as representative baseline
                self.iso_forest.fit(feature_data)
                self.is_fitted = True
            scores = self.iso_forest.decision_function(feature_data)
            preds = self.iso_forest.predict(feature_data)
            # Latest observation anomaly
            if preds[-1] == -1:
                iso_flag = True
                iso_score = round(float(scores[-1]), 4)
                anomalies.append({
                    "signal": "multivariate_telemetry",
                    "severity": "HIGH",
                    "current_value": iso_score,
                    "unit": "isolation_score",
                    "z_score": 0.0,
                    "evidence": f"Isolation Forest identified abnormal multivariate operating pattern (score: {iso_score})."
                })
        else:
            limitations.append("Insufficient telemetry length to compute multi-variable Isolation Forest.")

        return {
            "asset_id": asset_id,
            "analysis_window": f"{len(df)} samples ({len(df)} min equivalent)",
            "anomalies": anomalies,
            "multivariate_anomaly_detected": iso_flag,
            "data_quality": "acceptable" if not limitations else "acceptable_with_limitations",
            "limitations": limitations
        }
