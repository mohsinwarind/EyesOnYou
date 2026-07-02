# overlay_renderer.py
import cv2
import numpy as np


def render_guardian_overlay(
    frame: np.ndarray,
    guardian_img: np.ndarray,
    message: str,
    escalation_level: int = 1,
) -> np.ndarray:
    output = frame.copy()
    h, w   = output.shape[:2]

    # ── 1. Dark vignette ─────────────────────────────────────
    dark = np.zeros_like(output)
    cv2.addWeighted(dark, 0.60, output, 0.40, 0, output)

    # ── 2. Escalation accent color ───────────────────────────
    colors = {
        1: (100, 200, 100),
        2: (30,  165, 255),
        3: (30,   30, 220),
        4: (180,  30, 220),
    }
    accent = colors.get(escalation_level, colors[4])

    # ── 3. Guardian photo — large, centered ──────────────────
    if guardian_img is not None:
        # Target size: 40% of frame height, maintain aspect ratio
        target_h = int(h * 0.40)
        g_h, g_w = guardian_img.shape[:2]
        scale    = target_h / g_h
        target_w = int(g_w * scale)

        g_resized = cv2.resize(guardian_img, (target_w, target_h))

        # Center horizontally, place in upper portion
        x1 = (w - target_w) // 2
        y1 = int(h * 0.05)
        x2 = x1 + target_w
        y2 = y1 + target_h

        # Glow border around photo
        border = 4
        cv2.rectangle(output,
                      (x1 - border, y1 - border),
                      (x2 + border, y2 + border),
                      accent, border)

        # Place photo
        output[y1:y2, x1:x2] = g_resized

        # Guardian name tag below photo
        name_y = y2 + 28
    else:
        name_y = int(h * 0.12)

    # ── 4. Alert badge at top ─────────────────────────────────
    badges = {1: "ALERT", 2: "WARNING", 3: "DANGER", 4: "⚠ MAXIMUM ALERT"}
    badge  = badges.get(escalation_level, "ALERT")
    cv2.rectangle(output, (0, 0), (w, 38), accent, -1)
    cv2.putText(output, f"  {badge}  —  GUARDIAN ACTIVATED",
                (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                (255, 255, 255), 2, cv2.LINE_AA)

    # ── 5. Message text — centered below photo ────────────────
    lines      = _wrap_text(message, max_chars=42)
    font       = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 0.72
    thickness  = 2
    line_h     = 36

    # Semi-transparent message background
    msg_block_h = len(lines) * line_h + 20
    msg_y1      = name_y
    msg_y2      = msg_y1 + msg_block_h
    overlay     = output.copy()
    cv2.rectangle(overlay, (0, msg_y1 - 10), (w, msg_y2 + 10), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, output, 0.45, 0, output)

    for i, line in enumerate(lines):
        text_size = cv2.getTextSize(line, font, font_scale, thickness)[0]
        text_x    = (w - text_size[0]) // 2
        text_y    = msg_y1 + i * line_h + line_h

        # Shadow
        cv2.putText(output, line, (text_x + 2, text_y + 2),
                    font, font_scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
        # Main
        cv2.putText(output, line, (text_x, text_y),
                    font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    return output


def _wrap_text(text: str, max_chars: int) -> list:
    words, lines, current = text.split(), [], ""
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