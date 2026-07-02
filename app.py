# app.py
import cv2
import time
import numpy as np
import streamlit as st
from PIL import Image

from pomodoro import PomodoroTimer, PomodoroConfig, PomodoroState
from focus_tracker import FocusTracker
from event_system import EventSystem, FocusEvent, FocusEventType, HeadDirection
from session_analytics import SessionAnalytics
from guardian import get_guardian_message
from tts_engine import TTSEngine
from music_player import MusicPlayer
from overlay_renderer import render_guardian_overlay


st.set_page_config(
    page_title="Eyes On You",
    page_icon="👁",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background: #f5f5f5 !important;
    color: #1a1a1a;
    font-family: 'Inter', sans-serif;
}

/* Hide all streamlit chrome */
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }

/* Remove default padding */
.main .block-container {
    padding: 0rem !important;
    margin: 0rem !important;
    max-width: 100% !important;
}
[data-testid="stAppViewContainer"] { padding: 0 !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e0e0e0;
    padding: 0;
}
[data-testid="stSidebar"] > div { padding: 2rem 1.5rem; }

/* Inputs */
input, textarea, select {
    background: #ffffff !important;
    border: 1.5px solid #d0d0d0 !important;
    color: #1a1a1a !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.6rem 0.8rem !important;
}
input:focus { border-color: #666 !important; outline: none !important; box-shadow: 0 0 0 3px rgba(0,0,0,0.08) !important; }

/* Buttons */
.stButton > button {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border: 1.5px solid #d0d0d0 !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1.4rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}
.stButton > button:hover {
    background: #f0f0f0 !important;
    border-color: #999 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12) !important;
}
.stButton > button:active {
    background: #e8e8e8 !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1) !important;
    transform: translateY(1px) !important;
}

/* Start button — primary */
.start-btn > button {
    background: #1a1a1a !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.75rem 1.5rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
}
.start-btn > button:hover {
    background: #333333 !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
}

/* Slider */
[data-testid="stSlider"] > div > div > div {
    background: #d0d0d0 !important;
    height: 6px !important;
}
[data-testid="stSlider"] > div > div > div > div {
    background: #1a1a1a !important;
}
[data-testid="stSlider"] label {
    font-size: 0.95rem !important;
    color: #1a1a1a !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 1.5px dashed #d0d0d0 !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"] label {
    font-size: 0.95rem !important;
    color: #1a1a1a !important;
}

/* Labels and text */
label, .stMarkdown p { 
    color: #1a1a1a !important; 
    font-size: 0.95rem !important;
    font-weight: 500 !important;
}
h1 { font-size: 2.2rem !important; color: #1a1a1a !important; font-weight: 600 !important; }
h2 { font-size: 1.8rem !important; color: #1a1a1a !important; font-weight: 600 !important; }
h3 { font-size: 1.4rem !important; color: #1a1a1a !important; font-weight: 600 !important; }
.stMarkdown { color: #1a1a1a !important; }

/* Metrics */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1.5px solid #e0e0e0;
    border-radius: 10px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
[data-testid="stMetricValue"] { 
    color: #1a1a1a !important; 
    font-size: 1.6rem !important; 
    font-family: 'DM Mono', monospace !important;
    font-weight: 500 !important;
}
[data-testid="stMetricLabel"] { 
    color: #666 !important; 
    font-size: 0.8rem !important; 
    letter-spacing: 0.06em; 
    text-transform: uppercase;
    font-weight: 600 !important;
}

/* Progress */
[data-testid="stProgressBar"] > div {
    background: #e0e0e0 !important;
    border-radius: 6px !important;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
    height: 10px !important;
}
[data-testid="stProgressBar"] > div > div {
    background: #1a1a1a !important;
    border-radius: 6px !important;
}

/* Divider */
hr { border-color: #e0e0e0 !important; margin: 0.5rem 0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f5f5f5; }
::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }

/* Guardian card */
.guardian-card {
    background: #ffffff;
    border: 1.5px solid #e0e0e0;
    border-left: 4px solid #1a1a1a;
    border-radius: 10px;
    padding: 16px 20px;
    font-size: 1rem;
    color: #1a1a1a;
    font-style: italic;
    line-height: 1.6;
    margin-top: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* Clock face */
.clock-face {
    background: radial-gradient(ellipse at 30% 25%, #ffffff 0%, #f0f0f0 40%, #e8e8e8 100%);
    border: 2px solid #d0d0d0;
    border-radius: 50%;
    box-shadow:
        0 0 0 1px #e0e0e0,
        0 8px 32px rgba(0,0,0,0.1),
        inset 0 2px 4px rgba(255,255,255,0.8),
        inset 0 -2px 8px rgba(0,0,0,0.05);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    width: 320px;
    height: 320px;
    margin: 0 auto;
    max-width: 90%;
}

.clock-time {
    font-family: 'DM Mono', monospace;
    font-size: 4rem;
    font-weight: 500;
    color: #1a1a1a;
    letter-spacing: 0.02em;
    text-shadow: 0 0 20px rgba(0,0,0,0.05);
}

.clock-label {
    font-size: 0.8rem;
    color: #666;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-top: 8px;
    font-weight: 600;
}

.clock-session {
    font-size: 0.8rem;
    color: #888;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 4px;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
}

/* Status pill */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.status-focused   { background: #e8f5e9; color: #1b5e20; border: 1.5px solid #a5d6a7; }
.status-distracted{ background: #ffebee; color: #b71c1c; border: 1.5px solid #ef9a9a; }
.status-idle      { background: #f5f5f5; color: #666;    border: 1.5px solid #e0e0e0; }

/* Webcam box */
.webcam-label {
    font-size: 0.8rem;
    color: #666;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 8px;
    font-weight: 600;
}

/* Setup page */
.setup-title {
    font-size: 2.5rem;
    font-weight: 600;
    color: #1a1a1a;
    letter-spacing: -0.03em;
    margin-bottom: 8px;
}
.setup-sub {
    font-size: 1rem;
    color: #666;
    margin-bottom: 2.5rem;
    font-weight: 400;
}

/* Input labels on setup */
.field-label {
    font-size: 0.85rem;
    color: #1a1a1a;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 8px;
    font-weight: 600;
}

/* Number input */
[data-testid="stNumberInput"] {
    background: #ffffff !important;
    border-radius: 8px;
}
[data-testid="stNumberInput"] label {
    font-size: 0.95rem !important;
    color: #1a1a1a !important;
}
[data-testid="stNumberInput"] input {
    font-size: 1rem !important;
}

/* Caption text */
.caption-text {
    font-size: 0.85rem;
    color: #666;
    margin-top: 4px;
}

/* Responsive fixes */
@media (max-width: 768px) {
    .clock-face {
        width: 200px;
        height: 200px;
    }
    .clock-time {
        font-size: 2.8rem;
    }
    .setup-title {
        font-size: 1.8rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    .clock-label, .clock-session {
        font-size: 0.65rem;
    }
}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────
def init_state():
    defaults = {
        "page":           "setup",        # "setup" | "timer"
        "timer":          PomodoroTimer(),
        "events":         EventSystem(),
        "analytics":      None,
        "tracker":        None,
        "tts":            TTSEngine(),
        "music":          MusicPlayer(),
        "guardian_img":   None,
        "guardian_name":  "Guardian",
        "grace_period":   8,
        "running":        False,
        "distracted_since":   None,
        "focused_since":      None,
        "guardian_fired":     False,
        "guardian_active":    False,
        "guardian_active_until": 0,
        "guardian_message":   "",
        "last_guardian_time": 0,
        "current_status":     "idle",
        "session_history":    [],
        "frame":              None,
        "display_frame":      None,
        "direction":          HeadDirection.FORWARD,
        "phone":              False,
        "face_detected":      False,
        "cap":                None,
        "last_update":        0,
        "frame_count":        0,
        "skip_frames":        2,  # Process every 3rd frame
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

GUARDIAN_COOLDOWN     = 20.0
ABSENCE_THRESHOLD     = 10.0
FOCUS_CONFIRM         = 3.0
GUARDIAN_DISPLAY_SECS = 8
FRAME_INTERVAL        = 0.3  # ~3fps — plenty for grace-period-based
                              # distraction detection, far less flicker
                              # than 10fps


# ══════════════════════════════════════════════════════════════
# PAGE 1 — SETUP
# ══════════════════════════════════════════════════════════════
if st.session_state.page == "setup":

    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    
    # Centered narrow column with responsive width
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.empty()
    with col2:
        st.markdown('<div class="setup-title">👁 Eyes On You</div>', unsafe_allow_html=True)
        st.markdown('<div class="setup-sub">Configure your session, then lock in.</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ── Pomodoro ──────────────────────────────────────────
        st.markdown('<div class="field-label">⏱ Pomodoro Duration</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            work_min  = st.number_input("Work (min)",  min_value=1, max_value=90,  value=25, label_visibility="collapsed")
            st.markdown('<p class="caption-text">Work</p>', unsafe_allow_html=True)
        with c2:
            break_min = st.number_input("Break (min)", min_value=1, max_value=30,  value=5,  label_visibility="collapsed")
            st.markdown('<p class="caption-text">Break</p>', unsafe_allow_html=True)

        # ── Guardian ──────────────────────────────────────────
        st.markdown('<div class="field-label" style="margin-top:1.2rem">👁 Guardian</div>', unsafe_allow_html=True)
        guardian_name = st.text_input(
            "Name", value=st.session_state.guardian_name,
            placeholder="e.g. Coach, Drill Sergeant, Dad...",
            label_visibility="collapsed"
        )
        st.markdown('<p class="caption-text">Name</p>', unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Guardian photo (optional)",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed"
        )
        st.markdown('<p class="caption-text">Guardian photo — optional but terrifying</p>', unsafe_allow_html=True)

        if uploaded:
            img = Image.open(uploaded).convert("RGB")
            st.image(img, width=120)
            st.session_state.guardian_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # ── Sensitivity ───────────────────────────────────────
        st.markdown('<div class="field-label" style="margin-top:1rem">🎯 Distraction Sensitivity</div>', unsafe_allow_html=True)
        grace = st.slider(
            "Grace period", min_value=3, max_value=15, value=8,
            label_visibility="collapsed",
            help="Seconds you can look away before guardian activates"
        )
        st.markdown(f'<p class="caption-text">Guardian activates after <strong>{grace}s</strong> of distraction</p>', unsafe_allow_html=True)

        st.markdown("---")

        # ── Start ─────────────────────────────────────────────
        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        if st.button("🚀 Start Session →", use_container_width=True):
            timer = st.session_state.timer
            timer.config.work_minutes  = work_min
            timer.config.break_minutes = break_min
            timer.start()
            st.session_state.guardian_name  = guardian_name
            st.session_state.grace_period   = grace
            st.session_state.analytics      = SessionAnalytics(st.session_state.events)
            st.session_state.tracker        = FocusTracker()
            st.session_state.running        = True
            st.session_state.current_status = "focused"
            st.session_state.analytics.on_session_start()
            
            # Initialize webcam
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            st.session_state.cap = cap
            st.session_state.frame_count = 0
            
            st.session_state.page = "timer"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.empty()


# ══════════════════════════════════════════════════════════════
# PAGE 2 — TIMER
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "timer":

    st.markdown("""
    <style>
    /* Hide entire sidebar */
    section[data-testid="stSidebar"]{
        display:none !important;
    }
    [data-testid="collapsedControl"]{
        display:none !important;
    }
    [data-testid="stSidebarCollapsedControl"]{
        display:none !important;
    }
    /* Remove all Streamlit page padding */
    .main .block-container{
        padding-top:0rem !important;
        padding-bottom:0rem !important;
        padding-left:1rem !important;
        padding-right:1rem !important;
        max-width:100% !important;
    }
    /* Remove top spacing */
    [data-testid="stAppViewContainer"]{
        padding-top:0rem !important;
    }
    [data-testid="stHeader"]{
        height:0rem !important;
    }
    header{
        display:none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    timer: PomodoroTimer = st.session_state.timer
    GRACE = float(st.session_state.grace_period)

    # ────────────────────────────────────────────────────────────
    # STATIC SKELETON — built once per full page load, NOT inside
    # the fragment. Streamlit dims/fades a fragment's entire render
    # region on every rerun, so anything that doesn't need to change
    # every frame (buttons, column layout, labels) stays out here.
    # Only the placeholders themselves (st.empty()) are handed to
    # the fragment below, which writes new content INTO them without
    # rebuilding the surrounding buttons/columns.
    # ────────────────────────────────────────────────────────────
    top_l, top_r = st.columns([6, 1])
    with top_l:
        status_ph = st.empty()
    with top_r:
        if st.button("✕ End", use_container_width=True, key="end_session_btn"):
            st.session_state.running = False
            st.session_state.music.stop()
            st.session_state.guardian_active = False
            if st.session_state.cap is not None:
                st.session_state.cap.release()
                st.session_state.cap = None
            st.session_state.page = "setup"
            st.rerun()

    st.markdown("<hr style='margin:0.2rem 0 0'>", unsafe_allow_html=True)

    clock_col, cam_col = st.columns([3, 2], gap="large")

    with clock_col:
        phase_ph = st.empty()
        clock_ph = st.empty()
        prog_ph = st.empty()
        sess_ph = st.empty()

        ctrl_l, ctrl_m, ctrl_r = st.columns([1, 2, 1])
        with ctrl_m:
            label = "⏸  Pause" if timer.is_running else "▶  Resume"
            if st.button(label, key="pause_resume_btn", use_container_width=True):
                timer.pause() if timer.is_running else timer.resume()
                st.rerun()

        msg_ph = st.empty()

    with cam_col:
        st.markdown('<div class="webcam-label">📹 Live Monitor</div>', unsafe_allow_html=True)
        frame_ph = st.empty()

        s1, s2, s3 = st.columns(3)
        stat_d = s1.empty()
        stat_s = s2.empty()
        stat_f = s3.empty()

    # ────────────────────────────────────────────────────────────
    # DYNAMIC FRAGMENT — only this small function reruns every
    # FRAME_INTERVAL seconds. It just writes into the placeholders
    # created above; it never creates new buttons/columns, so the
    # dim/flash on rerun is confined to their content, not the
    # whole layout.
    # ────────────────────────────────────────────────────────────
    @st.fragment(run_every=FRAME_INTERVAL)
    def timer_fragment():
        now = time.time()

        # ── Process webcam frame (only if enough time has passed) ──
        if now - st.session_state.last_update >= FRAME_INTERVAL:
            cap = st.session_state.cap
            tracker: FocusTracker = st.session_state.tracker

            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    frame = cv2.flip(frame, 1)
                    result = tracker.process_frame(frame)
                    st.session_state.direction = result["head_direction"]
                    st.session_state.phone = result["phone_detected"]
                    st.session_state.face_detected = result["face_detected"]
                    st.session_state.display_frame = result["annotated_frame"]
                    st.session_state.frame = frame
                    st.session_state.last_update = now
                    st.session_state.frame_count += 1

        # ── Status pill ─────────────────────────────────────────
        status = st.session_state.current_status
        pill = {
            "focused":    '<span class="status-pill status-focused">● Focused</span>',
            "distracted": '<span class="status-pill status-distracted">● Distracted</span>',
            "idle":       '<span class="status-pill status-idle">● Idle</span>',
        }.get(status, "")
        status_ph.markdown(
            f'<div style="padding:0.8rem 1.5rem 0">'
            f'<span style="font-size:0.85rem;color:#666;letter-spacing:0.1em;text-transform:uppercase;font-weight:600">Eyes On You</span>'
            f'&nbsp;&nbsp;&nbsp;{pill}</div>',
            unsafe_allow_html=True
        )

        # ── Guardian trigger ──────────────────────────────────────
        def trigger_guardian(event_type, direction, phone):
            now = time.time()
            if now - st.session_state.last_guardian_time < GUARDIAN_COOLDOWN:
                return

            events = st.session_state.events
            d_count = events.get_distraction_count(timer.session_count)
            esc = min(4, max(1, (d_count // 2) + 1))

            events.log(FocusEvent(
                event_type=event_type,
                head_direction=direction,
                phone_detected=phone,
                session_number=timer.session_count,
                distraction_count=d_count,
                time_remaining=timer.remaining_seconds,
                escalation_level=esc,
            ))

            if event_type == FocusEventType.FOCUS_REGAINED:
                st.session_state.analytics.on_focus_regained()
            else:
                st.session_state.analytics.on_focus_lost()

            msg = get_guardian_message(
                event_type=event_type,
                head_direction=direction,
                phone_detected=phone,
                distraction_count=d_count,
                session_number=timer.session_count,
                time_remaining_seconds=timer.remaining_seconds,
                escalation_level=esc,
                guardian_name=st.session_state.guardian_name,
            )

            st.session_state.guardian_message = msg
            st.session_state.guardian_active = True
            st.session_state.guardian_active_until = now + GUARDIAN_DISPLAY_SECS
            st.session_state.last_guardian_time = now

            st.session_state.music.play(volume=0.2)
            st.session_state.tts.speak(msg)

        # ── Update timer and state ──────────────────────────────
        # Phase transition
        if timer.remaining_seconds == 0:
            timer.next_phase()
            if timer.state == PomodoroState.BREAK:
                st.session_state.current_status = "idle"
                st.session_state.music.stop()
                st.session_state.guardian_active = False

        # Distraction logic (only during WORK)
        if timer.state == PomodoroState.WORK:
            direction = st.session_state.direction
            phone = st.session_state.phone
            face_detected = st.session_state.face_detected

            is_distracted = (
                direction != HeadDirection.FORWARD
                or not face_detected
                or phone
            )

            if is_distracted:
                st.session_state.focused_since = None
                st.session_state.current_status = "distracted"

                if st.session_state.distracted_since is None:
                    st.session_state.distracted_since = now
                    st.session_state.guardian_fired = False
                else:
                    dur = now - st.session_state.distracted_since
                    cooldown_ok = (now - st.session_state.last_guardian_time) > GUARDIAN_COOLDOWN

                    if dur >= GRACE and not st.session_state.guardian_fired and cooldown_ok:
                        if phone:
                            etype = FocusEventType.PHONE_DETECTED
                        elif not face_detected or dur > ABSENCE_THRESHOLD:
                            etype = FocusEventType.LONG_ABSENCE
                        elif direction == HeadDirection.LEFT:
                            etype = FocusEventType.FOCUS_LOST_LEFT
                        elif direction == HeadDirection.RIGHT:
                            etype = FocusEventType.FOCUS_LOST_RIGHT
                        elif direction == HeadDirection.DOWN:
                            etype = FocusEventType.FOCUS_LOST_DOWN
                        else:
                            etype = FocusEventType.FOCUS_LOST_UP

                        trigger_guardian(etype, direction, phone)
                        st.session_state.guardian_fired = True

            else:
                st.session_state.current_status = "focused"

                if st.session_state.distracted_since is not None:
                    if st.session_state.focused_since is None:
                        st.session_state.focused_since = now
                    elif (now - st.session_state.focused_since) >= FOCUS_CONFIRM:
                        if st.session_state.guardian_fired:
                            cooldown_ok = (now - st.session_state.last_guardian_time) > GUARDIAN_COOLDOWN
                            if cooldown_ok:
                                trigger_guardian(FocusEventType.FOCUS_REGAINED, direction, phone)
                        st.session_state.distracted_since = None
                        st.session_state.focused_since = None
                        st.session_state.guardian_fired = False
                else:
                    st.session_state.focused_since = None

        # Clear guardian overlay by timestamp
        if st.session_state.guardian_active and now >= st.session_state.guardian_active_until:
            st.session_state.guardian_active = False
            st.session_state.music.stop()

        # ── Guardian overlay on webcam frame ──────────────────
        display_frame = st.session_state.display_frame
        if st.session_state.guardian_active and display_frame is not None:
            d_count = st.session_state.events.get_distraction_count(timer.session_count)
            esc = min(4, max(1, (d_count // 2) + 1))
            display_frame = render_guardian_overlay(
                display_frame,
                st.session_state.guardian_img,
                st.session_state.guardian_message,
                esc,
            )

        # ── Render clock face ─────────────────────────────────
        phase_label = timer.phase_label().upper()
        phase_ph.markdown(
            f'<div style="text-align:center;font-size:0.8rem;color:#666;'
            f'letter-spacing:0.2em;text-transform:uppercase;font-family:Inter,sans-serif;font-weight:600">'
            f'{phase_label}</div>',
            unsafe_allow_html=True
        )

        clock_ph.markdown(
            f'<div class="clock-face">'
            f'<div class="clock-time">{timer.formatted_time()}</div>'
            f'<div class="clock-label">{timer.phase_label()}</div>'
            f'<div class="clock-session">Session {timer.session_count}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        prog_ph.progress(timer.progress)

        # Session dots (max 8)
        dots = ""
        for i in range(1, min(timer.session_count + 1, 9)):
            filled = i <= timer.session_count
            dots += f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;' \
                    f'background:{"#1a1a1a" if filled else "#e0e0e0"};margin:0 4px;' \
                    f'box-shadow:{"0 0 6px rgba(0,0,0,0.2)" if filled else "none"}"></span>'
        sess_ph.markdown(
            f'<div style="text-align:center;margin-top:10px">{dots}</div>',
            unsafe_allow_html=True
        )

        # Guardian message
        if st.session_state.guardian_message:
            msg_ph.markdown(
                f'<div class="guardian-card">'
                f'<span style="font-size:0.75rem;color:#666;letter-spacing:0.1em;text-transform:uppercase;font-weight:600">'
                f'{st.session_state.guardian_name}</span><br>'
                f'{st.session_state.guardian_message}'
                f'</div>',
                unsafe_allow_html=True
            )

        # Webcam - responsive
        if display_frame is not None:
            display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            frame_ph.image(display_rgb, channels="RGB", use_container_width=True)

        # Mini stats
        d_count = st.session_state.events.get_distraction_count(timer.session_count)
        stat_d.metric("Distractions", d_count)
        stat_s.metric("Session", timer.session_count)
        stat_f.metric("Phase", timer.phase_label())

    # Only run the live-updating fragment while a session is active.
    if st.session_state.running:
        timer_fragment()

    # ── Session summary (shown when running becomes False) ──
    if not st.session_state.running and st.session_state.analytics:
        # Clean up webcam
        if st.session_state.cap is not None:
            st.session_state.cap.release()
            st.session_state.cap = None
            
        summary = st.session_state.analytics.build_summary(
            timer.session_count,
            timer.config.work_minutes * 60,
        )
        st.session_state.session_history.append(summary)

        st.markdown(
            '<div style="font-size:0.8rem;color:#666;letter-spacing:0.15em;'
            'text-transform:uppercase;margin-bottom:1rem;font-weight:600">✅ Session Complete</div>',
            unsafe_allow_html=True
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Focus Time",   f"{int(summary.total_focus_seconds // 60)}m")
        c2.metric("Distractions", summary.distraction_count)
        c3.metric("Best Streak",  f"{int(summary.longest_focus_streak_seconds // 60)}m")
        c4.metric("Focus Score",  f"{summary.focus_score}/100")

        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        if st.button("← Back to Setup", use_container_width=False):
            st.session_state.page = "setup"
            st.session_state.timer = PomodoroTimer()
            st.session_state.events = EventSystem()
            st.session_state.running = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)