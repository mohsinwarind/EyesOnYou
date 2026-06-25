# app.py
import cv2
import time
import threading
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


# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Eyes On You",
    page_icon="👁️",
    layout="wide",
)

# ── Session state init ────────────────────────────────────────
def init_state():
    defaults = {
        "timer":        PomodoroTimer(),
        "events":       EventSystem(),
        "analytics":    None,
        "tracker":      None,
        "tts":          TTSEngine(),
        "music":        MusicPlayer(),
        "guardian_img": None,
        "guardian_name":"Your Guardian",
        "running":      False,
        "last_direction": HeadDirection.FORWARD,
        "distracted_since": None,
        "guardian_active": False,
        "guardian_message": "",
        "last_guardian_time": 0,
        "guardian_cooldown": 12,   # seconds between guardian triggers
        "ABSENCE_THRESHOLD": 5,    # seconds before "long absence" fires
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.title("👁️ Eyes On You")
    st.divider()

    # Pomodoro controls
    st.subheader("⏱ Pomodoro")
    col1, col2 = st.columns(2)
    with col1:
        work_min  = st.number_input("Work (min)",  min_value=1, max_value=60, value=25)
    with col2:
        break_min = st.number_input("Break (min)", min_value=1, max_value=30, value=5)

    timer: PomodoroTimer = st.session_state.timer

    if timer.state == PomodoroState.IDLE:
        if st.button("▶ Start Session", use_container_width=True):
            timer.config.work_minutes  = work_min
            timer.config.break_minutes = break_min
            timer.start()
            st.session_state.analytics  = SessionAnalytics(st.session_state.events)
            st.session_state.tracker    = FocusTracker()
            st.session_state.running    = True
            st.session_state.analytics.on_session_start()
    else:
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("⏸ Pause" if timer.is_running else "▶ Resume",
                         use_container_width=True):
                timer.pause() if timer.is_running else timer.resume()
        with bc2:
            if st.button("🔄 Reset", use_container_width=True):
                timer.reset()
                st.session_state.running = False
                st.session_state.music.stop()

    st.divider()

    # Timer display
    st.metric("Phase",      timer.phase_label())
    st.metric("Time Left",  timer.formatted_time())
    st.metric("Session #",  timer.session_count)
    st.progress(timer.progress)

    st.divider()

    # Guardian setup
    st.subheader("👤 Guardian")
    st.session_state.guardian_name = st.text_input(
        "Guardian Name", value=st.session_state.guardian_name
    )
    uploaded = st.file_uploader(
        "Upload Guardian Photo", type=["jpg", "jpeg", "png"]
    )
    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        st.session_state.guardian_img = cv2.cvtColor(
            np.array(img), cv2.COLOR_RGB2BGR
        )
        st.image(img, caption="Guardian", use_column_width=True)

    st.divider()
    st.caption("👁️ Stay focused. The Guardian is watching.")

# ── Main area ─────────────────────────────────────────────────
st.title("👁️ Eyes On You — Focus Coach")

cam_col, stat_col = st.columns([3, 1])

with cam_col:
    frame_placeholder = st.empty()

with stat_col:
    st.subheader("📊 Live Stats")
    stat_distractions = st.empty()
    stat_phase        = st.empty()
    stat_guardian_msg = st.empty()

# ── Main loop ─────────────────────────────────────────────────
GUARDIAN_COOLDOWN = st.session_state.guardian_cooldown
ABSENCE_THRESHOLD = st.session_state.ABSENCE_THRESHOLD


def trigger_guardian(
    event_type: FocusEventType,
    direction:  HeadDirection,
    phone:      bool,
):
    now = time.time()
    if now - st.session_state.last_guardian_time < GUARDIAN_COOLDOWN:
        return   # cooldown active

    timer   = st.session_state.timer
    events  = st.session_state.events
    d_count = events.get_distraction_count(timer.session_count)
    esc     = min(4, max(1, (d_count // 2) + 1))

    # Log event
    events.log(FocusEvent(
        event_type=event_type,
        head_direction=direction,
        phone_detected=phone,
        session_number=timer.session_count,
        distraction_count=d_count,
        time_remaining=timer.remaining_seconds,
        escalation_level=esc,
    ))

    # Analytics
    if event_type == FocusEventType.FOCUS_REGAINED:
        st.session_state.analytics.on_focus_regained()
    else:
        st.session_state.analytics.on_focus_lost()

    # Get guardian message
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

    st.session_state.guardian_message    = msg
    st.session_state.guardian_active     = True
    st.session_state.last_guardian_time  = now

    # TTS + Music
    st.session_state.music.play(volume=0.25)
    st.session_state.tts.speak(msg)

    # Schedule guardian deactivation after 8 seconds
    def deactivate():
        time.sleep(8)
        st.session_state.guardian_active = False
        st.session_state.music.stop()

    threading.Thread(target=deactivate, daemon=True).start()


if st.session_state.running and timer.state == PomodoroState.WORK:
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    tracker: FocusTracker = st.session_state.tracker

    while st.session_state.running and timer.state == PomodoroState.WORK:
        # Check if Pomodoro phase is done
        if timer.remaining_seconds == 0:
            timer.next_phase()
            if timer.state != PomodoroState.WORK:
                st.session_state.running = False
                break

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        result = tracker.process_frame(frame)

        direction     = result["head_direction"]
        phone         = result["phone_detected"]
        face_detected = result["face_detected"]
        display_frame = result["annotated_frame"]

        # ── Distraction logic ─────────────────────────────────
        is_distracted = (
            direction != HeadDirection.FORWARD
            or not face_detected
            or phone
        )

        if is_distracted:
            if st.session_state.distracted_since is None:
                st.session_state.distracted_since = time.time()

            absent_duration = time.time() - st.session_state.distracted_since

            # Map to event type
            if phone:
                etype = FocusEventType.PHONE_DETECTED
            elif not face_detected or absent_duration > ABSENCE_THRESHOLD:
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

        else:
            if st.session_state.distracted_since is not None:
                # User just returned
                trigger_guardian(
                    FocusEventType.FOCUS_REGAINED,
                    direction, phone
                )
                st.session_state.distracted_since = None

        st.session_state.last_direction = direction

        # ── Render guardian overlay if active ─────────────────
        if st.session_state.guardian_active:
            d_count = st.session_state.events.get_distraction_count(
                timer.session_count
            )
            esc = min(4, max(1, (d_count // 2) + 1))
            display_frame = render_guardian_overlay(
                display_frame,
                st.session_state.guardian_img,
                st.session_state.guardian_message,
                esc,
            )

        # ── Show frame ────────────────────────────────────────
        display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(display_rgb, channels="RGB", use_column_width=True)

        # ── Live stats ────────────────────────────────────────
        d_count = st.session_state.events.get_distraction_count(timer.session_count)
        stat_distractions.metric("Distractions", d_count)
        stat_phase.metric("Phase", timer.phase_label())
        if st.session_state.guardian_message:
            stat_guardian_msg.info(f"💬 {st.session_state.guardian_message}")

        time.sleep(0.033)   # ~30 fps

    cap.release()

    # ── Session summary ───────────────────────────────────────
    if st.session_state.analytics:
        summary = st.session_state.analytics.build_summary(
            timer.session_count,
            timer.config.work_minutes * 60,
        )
        st.success("✅ Pomodoro Session Complete!")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Focus Time",    f"{int(summary.total_focus_seconds // 60)}m")
        c2.metric("Distractions",  summary.distraction_count)
        c3.metric("Best Streak",   f"{int(summary.longest_focus_streak_seconds // 60)}m")
        c4.metric("Focus Score",   f"{summary.focus_score}/100")

else:
    frame_placeholder.info(
        "👆 Configure your Pomodoro in the sidebar and press **Start Session** to begin."
    )