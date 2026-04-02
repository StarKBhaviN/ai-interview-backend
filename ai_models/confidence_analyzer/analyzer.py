from .features import extract_audio_features
import os

class ConfidenceAnalyzer:
    """
    Analyzes audio features to determine speaker confidence.
    Follows a rule-based approach (V1) using acoustic properties:
    - Silence Ratio (Hesitation)
    - Energy (Energy/Volume)
    - Pitch (Tone variance)
    """

    def analyze(self, audio_path: str) -> dict:
        """
        Main entry point for audio confidence analysis.
        Returns a dict with scores and descriptive sentiment labels.
        """
        if not os.path.exists(audio_path):
            return {
                "confidence_score": 0.5,
                "sentiment": "Neutral (No Audio)",
                "details": "Audio file missing or unreadable"
            }

        features = extract_audio_features(audio_path)
        
        if not features:
            return {
                "confidence_score": 0.5,
                "sentiment": "Neutral (Processing Error)",
                "details": "Extraction failed"
            }

        # --- Rule-Based Scoring (v1) ---
        # Baseline score
        confidence = 0.5
        
        # 1. Silence/Hesitation (Weight: 40%)
        # Normal speech has silence ratio between 0.1 and 0.25
        # > 0.4 indicates significant hesitation
        if features["silence_ratio"] < 0.2:
            confidence += 0.20  # Very fluent
        elif features["silence_ratio"] < 0.35:
            confidence += 0.10  # Moderate fluency
        elif features["silence_ratio"] > 0.5:
            confidence -= 0.15  # Many pauses
            
        # 2. Energy/Volume (Weight: 30%)
        # 0.04+ is clear energy
        if features["energy_mean"] > 0.04:
            confidence += 0.15
        elif features["energy_mean"] < 0.01:
            confidence -= 0.20 # Very quiet/whispering
            
        # 3. Pitch Variance (Weight: 30%)
        # Not rule-based on mean pitch alone (everyone is different),
        # but very low pitch mean and very low duration can signal monotone/insecurity.
        if features["pitch_mean"] > 120:
            confidence += 0.10
        elif features["pitch_mean"] < 80 and features["pitch_mean"] > 0:
            confidence -= 0.05

        # Final Normalization (Keep within 0.0 - 1.0)
        final_score = round(min(1.0, max(0.0, confidence)), 3)

        # 4. Sentiment Labeling
        if final_score >= 0.75:
            sentiment = "Confident"
        elif final_score >= 0.5:
            sentiment = "Neutral"
        else:
            sentiment = "Hesitant / Nervous"

        return {
            "confidence_score": final_score,
            "sentiment": sentiment,
            "features_extracted": {
                "pitch": round(features["pitch_mean"], 1),
                "energy": round(features["energy_mean"], 4),
                "silence": f"{round(features['silence_ratio'] * 100, 1)}%",
                "duration": f"{round(features['duration'], 1)}s"
            }
        }

# Singleton accessor
_analyzer = None

def get_confidence_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = ConfidenceAnalyzer()
    return _analyzer
