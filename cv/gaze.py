def estimate_gaze(landmarks, w, h):
    """
    Simple gaze approximation using eye landmarks
    """

    points = getattr(landmarks, "landmark", landmarks)

    # left eye (rough indices)
    left_eye_x = points[33].x * w
    right_eye_x = points[263].x * w

    center_x = (left_eye_x + right_eye_x) / 2

    screen_center = w / 2

    diff = center_x - screen_center

    if abs(diff) < w * 0.05:
        return "CENTER"
    elif diff < 0:
        return "LEFT"
    else:
        return "RIGHT"