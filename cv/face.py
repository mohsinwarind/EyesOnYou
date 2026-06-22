import cv2
import mediapipe as mp


if hasattr(mp, "solutions"):
    mp_face = mp.solutions.face_mesh
    face_mesh = mp_face.FaceMesh(refine_landmarks=True)


    def get_face_landmarks(image):
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return None

        return results.multi_face_landmarks[0]

else:
    from pathlib import Path
    from urllib.request import urlretrieve

    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision import face_landmarker
    from mediapipe.tasks.python.vision.core import image as mp_image
    from mediapipe.tasks.python.vision.core import (
        vision_task_running_mode as running_mode_module,
    )

    _MODEL_URL = (
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
        "face_landmarker/float16/1/face_landmarker.task"
    )
    _MODEL_PATH = Path.home() / ".cache" / "eyes_on_you" / "face_landmarker.task"
    _FACE_LANDMARKER = None


    def _ensure_model_file():
        if _MODEL_PATH.exists():
            return _MODEL_PATH

        _MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

        try:
            urlretrieve(_MODEL_URL, _MODEL_PATH)
        except Exception as exc:
            raise RuntimeError(
                "MediaPipe FaceLandmarker model could not be downloaded. "
                "Check your network connection or place the model at "
                f"{_MODEL_PATH}."
            ) from exc

        return _MODEL_PATH


    def _get_face_landmarker():
        global _FACE_LANDMARKER

        if _FACE_LANDMARKER is None:
            model_path = _ensure_model_file()
            options = face_landmarker.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(model_path)),
                running_mode=running_mode_module.VisionTaskRunningMode.IMAGE,
                num_faces=1,
            )
            _FACE_LANDMARKER = face_landmarker.FaceLandmarker.create_from_options(
                options
            )

        return _FACE_LANDMARKER


    def get_face_landmarks(image):
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        media_image = mp_image.Image(mp_image.ImageFormat.SRGB, rgb)
        results = _get_face_landmarker().detect(media_image)

        if not results.face_landmarks:
            return None

        return results.face_landmarks[0]