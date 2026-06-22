class FocusEngine:
    def __init__(self):
        self.score = 100
        self.history = []

    def update(self, gaze, face_detected):
        if not face_detected:
            self.score -= 5
            state = "NO_FACE"

        elif gaze == "CENTER":
            self.score += 1
            state = "FOCUSED"

        else:
            self.score -= 3
            state = "DISTRACTED"

        # clamp
        self.score = max(0, min(100, self.score))

        self.history.append(self.score)

        return self.score, state