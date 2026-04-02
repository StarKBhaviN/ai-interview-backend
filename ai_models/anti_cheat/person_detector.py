import mediapipe as mp
import cv2
import numpy as np

mp_face_detection = mp.solutions.face_detection

class PersonDetector:
    def __init__(self):
        # Model selection 1 is for faces within ~2 meters (standard webcam)
        self.face_detection = mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
    
    def analyze_frame(self, frame_bytes: bytes) -> dict:
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return {"face_count": 0, "flags": []}
            
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb)
        
        face_count = 0
        if results.detections:
            face_count = len(results.detections)
            
        flags = []
        if face_count > 1:
            flags.append(f"Multiple persons detected: {face_count}")
        elif face_count == 0:
            flags.append("No face detected")
            
        return {
            "face_count": face_count,
            "flags": flags,
            "cheat_detected": len(flags) > 0
        }
