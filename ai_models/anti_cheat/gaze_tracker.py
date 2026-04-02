import mediapipe as mp
import cv2
import numpy as np

mp_face_mesh = mp.solutions.face_mesh

class GazeTracker:
    def __init__(self):
        # Refine landmarks = True is essential for iris detection (468-477)
        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=2,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def analyze_frame(self, frame_bytes: bytes) -> dict:
        # Decode frame
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return {"error": "Invalid frame data", "face_detected": False}
            
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        
        flags = []
        face_count = 0
        status = "center"
        
        if results.multi_face_landmarks:
            face_count = len(results.multi_face_landmarks)
            
            if face_count > 1:
                flags.append("Multiple persons detected")
            
            if face_count >= 1:
                landmarks = results.multi_face_landmarks[0]
                # Check gaze direction using iris landmarks (468-477)
                status = self._calculate_gaze(landmarks, frame.shape)
                if status == "away":
                    flags.append("Looking away from screen")
                    
                # Basic head pose tilt check (Bonus)
                # Nose vs Eye centers
                nose = landmarks.landmark[1]
                if abs(nose.x - 0.5) > 0.15: # Nose significantly off center
                    flags.append("Head posture anomaly (Side view)")
        else:
            flags.append("No face detected")
        
        return {
            "cheat_detected": len(flags) > 0,
            "flags": flags,
            "face_count": face_count,
            "gaze_direction": status
        }
    
    def _calculate_gaze(self, landmarks, shape):
        """
        Calculates if the pupil is centered between eye corners.
        Iris landmarks are 468 (L) and 473 (R).
        """
        h, w = shape[:2]
        
        # Left iris center (468)
        left_iris = landmarks.landmark[468]
        # Left eye inner (133) and outer (33) corners
        left_inner = landmarks.landmark[133]
        left_outer = landmarks.landmark[33]
        
        iris_x = left_iris.x * w
        inner_x = left_inner.x * w
        outer_x = left_outer.x * w
        
        eye_width = abs(inner_x - outer_x)
        if eye_width == 0: return "unknown"
        
        # Relative position (0.0 to 1.0)
        iris_position = (iris_x - min(inner_x, outer_x)) / eye_width
        
        # Threshold: 0.35 to 0.65 is "central"
        if iris_position < 0.3 or iris_position > 0.7:
            return "away"
        return "center"
