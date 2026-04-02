from .gaze_tracker import GazeTracker
from .person_detector import PersonDetector

class AntiCheatMonitor:
    """
    Unified monitor to detect candidate cheating behaviors.
    Combines Eye Gaze (GazeTracker) and Face Detection (PersonDetector).
    """
    def __init__(self):
        # We'll use GazeTracker as the primary engine for now 
        # since it already handles multiple faces.
        self.gaze_tracker = GazeTracker()
        
    def analyze_frame(self, frame_bytes: bytes) -> dict:
        """
        Integrates various cheating detection signals.
        - face_count (from gaze_tracker or detect results)
        - gaze_direction
        - head pose alerts
        """
        result = self.gaze_tracker.analyze_frame(frame_bytes)
        
        # Add metadata
        result["timestamp_ms"] = 0 # Placeholder for frame timing
        result["cheat_detected"] = len(result.get("flags", [])) > 0
        
        return result

# Singleton-like global accessor
_monitor = None

def get_anti_cheat_monitor():
    global _monitor
    if _monitor is None:
        _monitor = AntiCheatMonitor()
    return _monitor
