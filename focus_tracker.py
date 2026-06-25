# focus_tracker.py
import cv2
import numpy as np
from ultralytics import YOLO
from event_system import HeadDirection

# ── 3D face model landmarks (generic) ────────────────────────
MODEL_POINTS = np.array([
    (0.0,    0.0,    0.0),    # nose tip
    (0.0,  -330.0, -65.0),    # chin
    (-225.0, 170.0, -135.0),  # left eye corner
    (225.0,  170.0, -135.0),  # right eye corner
    (-150.0, -150.0, -125.0), # left mouth
    (150.0,  -150.0, -125.0), # right mouth
], dtype=np.float64)

# Landmark indices (MediaPipe-style mapped to dlib 68-pt equivalent via OpenCV)
LANDMARK_IDS = [30, 8, 36, 45, 48, 54]   # nose, chin, l-eye, r-eye, l-mouth, r-mouth

# Thresholds
YAW_THRESHOLD   = 20    # degrees left/right
PITCH_THRESHOLD = 15    # degrees up/down
ABSENT_AREA_MIN = 0.001 # face bounding box area fraction of frame


class FocusTracker:
    def __init__(self):
        # Face detector + landmark predictor via OpenCV DNN
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        # YOLO for phone detection
        self.yolo = YOLO("yolov8n.pt")   # auto-downloads on first run
        self.phone_class_id = 67          # COCO class: cell phone

        self._camera_matrix = None
        self._dist_coeffs   = np.zeros((4, 1))

    def _get_camera_matrix(self, frame_w: int, frame_h: int) -> np.ndarray:
        if self._camera_matrix is None:
            focal = frame_w
            cx, cy = frame_w / 2, frame_h / 2
            self._camera_matrix = np.array([
                [focal, 0,  cx],
                [0, focal,  cy],
                [0,     0,   1],
            ], dtype=np.float64)
        return self._camera_matrix

    def _get_head_direction(self, yaw: float, pitch: float) -> HeadDirection:
        if abs(yaw) > YAW_THRESHOLD:
            return HeadDirection.LEFT if yaw < 0 else HeadDirection.RIGHT
        if pitch < -PITCH_THRESHOLD:
            return HeadDirection.DOWN
        if pitch > PITCH_THRESHOLD:
            return HeadDirection.UP
        return HeadDirection.FORWARD

    def _estimate_head_pose(self, face_rect, gray_frame, frame_shape) -> HeadDirection:
        """solvePnP-based head pose using eye/mouth region heuristics."""
        x, y, w, h = face_rect
        fh, fw = frame_shape[:2]

        # Approximate 2D landmark positions from face bounding box
        image_points = np.array([
            (x + w * 0.50, y + h * 0.37),  # nose tip
            (x + w * 0.50, y + h * 0.90),  # chin
            (x + w * 0.22, y + h * 0.35),  # left eye outer
            (x + w * 0.78, y + h * 0.35),  # right eye outer
            (x + w * 0.35, y + h * 0.70),  # left mouth
            (x + w * 0.65, y + h * 0.70),  # right mouth
        ], dtype=np.float64)

        cam = self._get_camera_matrix(fw, fh)
        success, rvec, tvec = cv2.solvePnP(
            MODEL_POINTS, image_points, cam, self._dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        if not success:
            return HeadDirection.FORWARD

        rmat, _ = cv2.Rodrigues(rvec)
        proj = np.hstack([rmat, tvec])
        _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(proj)
        pitch = euler[0, 0]
        yaw   = euler[1, 0]

        return self._get_head_direction(yaw, pitch)

    def detect_phone(self, frame: np.ndarray) -> bool:
        results = self.yolo(frame, verbose=False, conf=0.4)
        for r in results:
            for cls in r.boxes.cls.tolist():
                if int(cls) == self.phone_class_id:
                    return True
        return False

    def process_frame(self, frame: np.ndarray) -> dict:
        """
        Returns:
            face_detected   : bool
            head_direction  : HeadDirection
            phone_detected  : bool
            annotated_frame : np.ndarray   (frame with debug drawings)
        """
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        face_detected  = len(faces) > 0
        head_direction = HeadDirection.ABSENT
        annotated      = frame.copy()

        if face_detected:
            # Use largest face
            face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = face
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 100), 2)
            head_direction = self._estimate_head_pose(face, gray, frame.shape)

        phone_detected = self.detect_phone(frame)

        # Draw direction label
        label_color = (0, 255, 0) if head_direction == HeadDirection.FORWARD else (0, 60, 255)
        cv2.putText(annotated, f"Gaze: {head_direction.value.upper()}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, label_color, 2)
        if phone_detected:
            cv2.putText(annotated, "PHONE DETECTED",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        return {
            "face_detected":  face_detected,
            "head_direction": head_direction,
            "phone_detected": phone_detected,
            "annotated_frame": annotated,
        }