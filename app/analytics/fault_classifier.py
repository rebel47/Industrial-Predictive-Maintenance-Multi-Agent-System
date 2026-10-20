import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, confusion_matrix
import joblib
import os

from app.analytics.signal_features import (
    compute_time_domain_features,
    compute_frequency_domain_features
)
from app.analytics.dataset_loader import generate_cwru_benchmark_signals

MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_cwru_classifier.joblib")

class BearingFaultClassifier:
    """Supervised fault classification model trained on CWRU bearing vibration feature representations."""
    
    FEATURE_NAMES = [
        "rms", "kurtosis", "crest_factor", "skewness", "peak_to_peak", "shape_factor",
        "dominant_freq", "dominant_amp"
    ]
    
    CLASSES = ["NORMAL", "INNER_RACE_FAULT", "OUTER_RACE_FAULT", "BALL_FAULT"]

    def __init__(self):
        self.clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        self.is_trained = False
        
    def extract_features_from_window(
        self,
        signal_window: np.ndarray,
        sampling_rate_hz: float = 12000.0,
        shaft_rpm: float = 1750.0
    ) -> List[float]:
        """Extract combined time & frequency feature vector."""
        t_feats = compute_time_domain_features(signal_window)
        f_feats = compute_frequency_domain_features(signal_window, sampling_rate_hz, shaft_rpm)
        
        return [
            t_feats["rms"],
            t_feats["kurtosis"],
            t_feats["crest_factor"],
            t_feats["skewness"],
            t_feats["peak_to_peak"],
            t_feats["shape_factor"],
            f_feats["dominant_frequency_hz"],
            f_feats["dominant_amplitude"]
        ]

    def build_dataset_from_signals(
        self,
        signals_dict: Dict[str, np.ndarray],
        window_size: int = 2048,
        step_size: int = 2048,
        sampling_rate_hz: int = 12000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Slice vibration signals into non-overlapping windows to extract feature dataset."""
        X_list = []
        y_list = []
        
        for label_idx, cls_name in enumerate(self.CLASSES):
            sig = signals_dict[cls_name]
            # Strictly non-overlapping windows (step_size == window_size) to prevent window leakage
            for start in range(0, len(sig) - window_size + 1, step_size):
                window = sig[start:start + window_size]
                feats = self.extract_features_from_window(window, sampling_rate_hz=sampling_rate_hz)
                X_list.append(feats)
                y_list.append(label_idx)
                
        return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.int32)

    def build_training_dataset(
        self,
        window_size: int = 2048,
        step_size: int = 2048,
        sampling_rate_hz: int = 12000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convenience method returning training signals feature matrix."""
        train_signals = generate_cwru_benchmark_signals(duration_sec=3.0, sampling_rate_hz=sampling_rate_hz, random_seed=42)
        return self.build_dataset_from_signals(train_signals, window_size, step_size, sampling_rate_hz)

    def train(self) -> Dict[str, Any]:
        """
        Train classifier on training signal runs and evaluate on genuinely held-out,
        independent test recording runs with zero window overlap.
        """
        # Independent training run (duration 3.0s, seed 42)
        train_signals = generate_cwru_benchmark_signals(duration_sec=3.0, sampling_rate_hz=12000, random_seed=42)
        X_train, y_train = self.build_dataset_from_signals(train_signals, window_size=2048, step_size=2048)

        # Genuinely held-out independent test recording run (duration 2.0s, seed 999)
        test_signals = generate_cwru_benchmark_signals(duration_sec=2.0, sampling_rate_hz=12000, random_seed=999)
        X_test, y_test = self.build_dataset_from_signals(test_signals, window_size=2048, step_size=2048)
        
        self.clf.fit(X_train, y_train)
        self.is_trained = True
        
        preds = self.clf.predict(X_test)
        macro_f1 = float(f1_score(y_test, preds, average="macro"))
        cm = confusion_matrix(y_test, preds).tolist()
        
        # Save model checkpoint
        joblib.dump(self.clf, MODEL_PATH)
        
        return {
            "macro_f1": round(macro_f1, 4),
            "train_samples": len(y_train),
            "test_samples": len(y_test),
            "classes": self.CLASSES,
            "confusion_matrix": cm,
            "evaluation_protocol": "independent_held_out_recordings_non_overlapping_windows",
            "feature_importances": {
                name: round(float(imp), 4)
                for name, imp in zip(self.FEATURE_NAMES, self.clf.feature_importances_)
            }
        }

    def predict(
        self,
        signal_data: np.ndarray,
        sampling_rate_hz: float = 12000.0,
        shaft_rpm: float = 1750.0
    ) -> Dict[str, Any]:
        """Classify a given vibration signal segment."""
        if not self.is_trained:
            if os.path.exists(MODEL_PATH):
                self.clf = joblib.load(MODEL_PATH)
                self.is_trained = True
            else:
                self.train()

        feats = self.extract_features_from_window(signal_data, sampling_rate_hz, shaft_rpm)
        probs = self.clf.predict_proba([feats])[0]
        best_idx = int(np.argmax(probs))
        
        return {
            "predicted_class": self.CLASSES[best_idx],
            "confidence": round(float(probs[best_idx]), 4),
            "class_probabilities": {
                cls_name: round(float(p), 4)
                for cls_name, p in zip(self.CLASSES, probs)
            },
            "extracted_features": {
                name: round(float(val), 4)
                for name, val in zip(self.FEATURE_NAMES, feats)
            }
        }
