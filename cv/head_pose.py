def estimate_head_pose(landmarks):

    nose = landmarks.landmark[1]

    left_eye = landmarks.landmark[33]
    right_eye = landmarks.landmark[263]

    eye_center_x = (left_eye.x + right_eye.x) / 2

    diff = nose.x - eye_center_x

    if diff > 0.03:
        return "RIGHT"

    elif diff < -0.03:
        return "LEFT"

    return "CENTER"