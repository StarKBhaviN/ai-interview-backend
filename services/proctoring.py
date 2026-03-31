import cv2
import mediapipe as mp
import numpy as np
import io
from PIL import Image

class ProctoringEngine:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=5,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )

    async def analyze_frame(self, image_bytes):
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {"cheat_detected": False, "flags": ["Invalid image"]}

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 1. Person Count
        detect_results = self.face_detection.process(rgb_img)
        face_count = 0
        if detect_results.detections:
            face_count = len(detect_results.detections)
        
        flags = []
        if face_count == 0:
            flags.append("Face not detected")
        elif face_count > 1:
            flags.append(f"Multiple persons detected: {face_count}")

        # 2. Advanced Analysis (if exactly one person)
        if face_count == 1:
            mesh_results = self.face_mesh.process(rgb_img)
            if mesh_results.multi_face_landmarks:
                landmarks = mesh_results.multi_face_landmarks[0].landmark
                h, w, _ = img.shape
                
                # --- HEAD POSE ESTIMATION ---
                # Key landmarks for 3D pose: Nose(1), Chin(152), LeftEyeLeft(33), RightEyeRight(263), LeftMouth(61), RightMouth(291)
                image_points = np.array([
                    (landmarks[1].x * w, landmarks[1].y * h),     # Nose tip
                    (landmarks[152].x * w, landmarks[152].y * h), # Chin
                    (landmarks[33].x * w, landmarks[33].y * h),   # Left eye left corner
                    (landmarks[263].x * w, landmarks[263].y * h), # Right eye right corner
                    (landmarks[61].x * w, landmarks[61].y * h),   # Left mouth corner
                    (landmarks[291].x * w, landmarks[291].y * h)  # Right mouth corner
                ], dtype="double")

                # 3D model points (stereotypical face)
                model_points = np.array([
                    (0.0, 0.0, 0.0),             # Nose tip
                    (0.0, -330.0, -65.0),        # Chin
                    (-225.0, 170.0, -135.0),     # Left eye left corner
                    (225.0, 170.0, -135.0),      # Right eye right corner
                    (-150.0, -150.0, -125.0),    # Left mouth corner
                    (150.0, -150.0, -125.0)      # Right mouth corner
                ])

                # Camera internals
                focal_length = w
                center = (w/2, h/2)
                camera_matrix = np.array(
                    [[focal_length, 0, center[0]],
                     [0, focal_length, center[1]],
                     [0, 0, 1]], dtype="double"
                )

                dist_coeffs = np.zeros((4,1)) # Assuming no lens distortion
                (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)

                if success:
                    # Convert rotation vector to euler angles
                    rmat, _ = cv2.Rodrigues(rotation_vector)
                    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
                    pitch, yaw, roll = angles[0], angles[1], angles[2]
                    
                    print(f"DEBUG PROCTORING: Pitch={pitch:.1f}, Yaw={yaw:.1f}, Roll={roll:.1f}")
                    
                    # Thresholds for anomalies
                    if abs(yaw) > 8: # Significant head turn left/right
                        flags.append(f"Looking away (Yaw: {yaw:.1f} deg)")
                    if abs(pitch) > 8: # Significant head posture anomaly
                        flags.append(f"Head posture anomaly (Pitch: {pitch:.1f} deg)")
                    if abs(roll) > 8: # Significant head tilt
                        flags.append(f"Head tilt detected (Roll: {roll:.1f} deg)")

                # --- REFINED GAZE TRACKING ---
                def get_gaze_ratio(eye_points, iris_point):
                    iris = landmarks[iris_point]
                    left = landmarks[eye_points[0]]
                    right = landmarks[eye_points[1]]
                    
                    # Horizontal ratio
                    ratio = (iris.x - left.x) / (right.x - left.x) if (right.x - left.x) != 0 else 0.5
                    return ratio

                left_gaze = get_gaze_ratio([33, 133], 468)
                right_gaze = get_gaze_ratio([362, 263], 473)
                avg_gaze = (left_gaze + right_gaze) / 2
                
                # Refined threshold: only flag if not already flagged by head pose
                if (avg_gaze < 0.35 or avg_gaze > 0.65) and not any("Yaw" in f for f in flags):
                    flags.append("Eyes looking away from screen")

        return {
            "cheat_detected": len(flags) > 0,
            "flags": flags,
            "timestamp": np.datetime64('now').astype(str)
        }

engine = ProctoringEngine()
