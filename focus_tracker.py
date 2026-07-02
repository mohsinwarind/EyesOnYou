import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from ultralytics import YOLO
from event_system import HeadDirection

YAW_THRESHOLD   = 25
PITCH_THRESHOLD = 20

NOSE_TIP    = 1
CHIN        = 152
LEFT_EYE    = 263
RIGHT_EYE   = 33
LEFT_MOUTH  = 287
RIGHT_MOUTH = 57

LANDMARK_IDS = [NOSE_TIP, CHIN, LEFT_EYE, RIGHT_EYE, LEFT_MOUTH, RIGHT_MOUTH]

MODEL_POINTS = np.array([
    (0.0,    0.0,    0.0),
    (0.0,  -330.0, -65.0),
    (-225.0, 170.0, -135.0),
    (225.0,  170.0, -135.0),
    (-150.0, -150.0, -125.0),
    (150.0,  -150.0, -125.0),
], dtype=np.float64)


class FocusTracker:
    def __init__(self):
        base_options = mp_python.BaseOptions(
            model_asset_path='face_landmarker.task'
        )
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=1,
            min_face_detection_confidence=0.6,
            min_face_presence_confidence=0.6,
            min_tracking_confidence=0.6,
            running_mode=mp_vision.RunningMode.VIDEO,  # needed for per-frame tracking
        )
        self.face_landmarker = mp_vision.FaceLandmarker.create_from_options(options)
        self._frame_timestamp_ms = 0

        self.yolo           = YOLO("yolov8n.pt")
        self.phone_class_id = 67

        self._yaw_buf   = []
        self._pitch_buf = []
        self._buf_size  = 8

        self._camera_matrix = None
        self._dist_coeffs   = np.zeros((4, 1))

    def _get_camera_matrix(self, w, h):
        if self._camera_matrix is None:
            focal = w
            self._camera_matrix = np.array([
                [focal, 0,     w / 2],
                [0,     focal, h / 2],
                [0,     0,     1    ],
            ], dtype=np.float64)
        return self._camera_matrix

    def _smooth(self, buf, value):
        buf.append(value)
        if len(buf) > self._buf_size:
            buf.pop(0)
        return sum(buf) / len(buf)

    def _get_direction(self, yaw, pitch):
        if abs(yaw) > YAW_THRESHOLD:
            return HeadDirection.LEFT if yaw < 0 else HeadDirection.RIGHT
        if pitch < -PITCH_THRESHOLD:
            return HeadDirection.DOWN
        if pitch > PITCH_THRESHOLD:
            return HeadDirection.UP
        return HeadDirection.FORWARD

    def _estimate_pose(self, landmarks, w, h):
        image_points = np.array([
            (landmarks[i].x * w, landmarks[i].y * h)
            for i in LANDMARK_IDS
        ], dtype=np.float64)

        cam = self._get_camera_matrix(w, h)
        success, rvec, tvec = cv2.solvePnP(
            MODEL_POINTS, image_points, cam, self._dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        if not success:
            return 0.0, 0.0

        rmat, _ = cv2.Rodrigues(rvec)
        proj     = np.hstack([rmat, tvec])
        _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(proj)

        euler = euler.flatten()

        return float(euler[1]), float(euler[0])  # yaw, pitch

    def detect_phone(self, frame):
        results = self.yolo(frame, verbose=False, conf=0.45)
        for r in results:
            for cls in r.boxes.cls.tolist():
                if int(cls) == self.phone_class_id:
                    return True
        return False

    def process_frame(self, frame):
        h, w = frame.shape[:2]

        # New API: wrap in mp.Image and use detect_for_video
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        )
        self._frame_timestamp_ms += 33  # ~30fps; adjust if needed
        results = self.face_landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)

        face_detected  = False
        head_direction = HeadDirection.ABSENT
        annotated      = frame.copy()

        if results.face_landmarks:
            face_detected = True
            lms = results.face_landmarks[0]  # list of NormalizedLandmark

            yaw, pitch = self._estimate_pose(lms, w, h)
            yaw   = self._smooth(self._yaw_buf,   yaw)
            pitch = self._smooth(self._pitch_buf, pitch)

            head_direction = self._get_direction(yaw, pitch)

            nose   = lms[NOSE_TIP]
            nx, ny = int(nose.x * w), int(nose.y * h)
            color  = (0, 255, 0) if head_direction == HeadDirection.FORWARD else (0, 60, 255)
            cv2.circle(annotated, (nx, ny), 6, color, -1)
            cv2.putText(annotated,
                        f"Gaze: {head_direction.value.upper()}  Y:{yaw:.1f} P:{pitch:.1f}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
        else:
            cv2.putText(annotated, "No Face Detected",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

        phone_detected = self.detect_phone(frame)
        if phone_detected:
            cv2.putText(annotated, "PHONE DETECTED",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

        return {
            "face_detected":   face_detected,
            "head_direction":  head_direction,
            "phone_detected":  phone_detected,
            "annotated_frame": annotated,
        }