# overlay_renderer.py
import cv2
import numpy as np
from PIL import Image


def render_guardian_overlay(
    frame: np.ndarray,
    guardian_img: np.ndarray,
    message: str,
    escalation_level: int = 1,
) -> np.ndarray:
    """
    Renders a cinematic guardian overlay on the webcam frame:
    - Dark vignette over the frame
    - Guardian photo in bottom-right corner
    - Dramatic message text with colored border based on escalation
    """
    output = frame.copy()
    h, w = output.shape[:2]

    # ── 1. Dark overlay (vignette) ───────────────────────────
    dark = np.zeros_like(output)
    alpha = 0.55
    cv2.addWeighted(dark, alpha, output, 1 - alpha, 0, output)

    # ── 2. Escalation color ──────────────────────────────────
    colors = {
        1: (100, 200, 100),   # green-ish: firm
        2: (30, 165, 255),    # orange: annoyed
        3: (30,  30, 220),    # red: angry
        4: (180,  30, 220),   # purple: full intimidation
    }
    accent = colors.get(escalation_level, colors[4])

    # ── 3. Guardian photo (bottom-right) ────────────────────
    if guardian_img is not None:
        ph, pw = 180, 140
        g_resized = cv2.resize(guardian_img, (pw, ph))

        # Border around guardian photo
        border = 3
        x1 = w - pw - 20 - border
        y1 = h - ph - 20 - border
        cv2.rectangle(output,
                      (x1 - border, y1 - border),
                      (x1 + pw + border, y1 + ph + border),
                      accent, border)

        output[y1:y1 + ph, x1:x1 + pw] = g_resized

    # ── 4. Message text ──────────────────────────────────────
    lines = _wrap_text(message, max_chars=45)
    font       = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 0.72
    thickness  = 2
    line_h     = 34

    text_y_start = h // 3

    for i, line in enumerate(lines):
        y = text_y_start + i * line_h
        # Shadow
        cv2.putText(output, line, (22, y + 2), font, font_scale,
                    (0, 0, 0), thickness + 2, cv2.LINE_AA)
        # Main text (white)
        cv2.putText(output, line, (20, y), font, font_scale,
                    (255, 255, 255), thickness, cv2.LINE_AA)

    # ── 5. Escalation level badge ────────────────────────────
    badges = {1: "ALERT", 2: "WARNING", 3: "DANGER", 4: "MAXIMUM ALERT"}
    badge_text = badges.get(escalation_level, "ALERT")
    cv2.rectangle(output, (0, 0), (w, 36), accent, -1)
    cv2.putText(output, f"You Triggered {badge_text}  tag for Guardian dude ! ",
                (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                (255, 255, 255), 2, cv2.LINE_AA)

    return output


def _wrap_text(text: str, max_chars: int) -> list[str]:
    words  = text.split()
    lines  = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines