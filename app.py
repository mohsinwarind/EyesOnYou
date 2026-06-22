import streamlit as st
import cv2
import numpy as np

from cv.face import get_face_landmarks
from cv.gaze import estimate_gaze
from engine.focus import FocusEngine

st.set_page_config(page_title="Eyes On You", layout="centered")
st.title("👁️ EYES ON YOU")

run = st.checkbox("Start Monitoring")

# Keep engine and capture alive across reruns
if "engine" not in st.session_state:
    st.session_state.engine = FocusEngine()

if "cap" not in st.session_state:
    st.session_state.cap = None

engine = st.session_state.engine

if run:
    # Open camera only once
    if st.session_state.cap is None or not st.session_state.cap.isOpened():
        st.session_state.cap = cv2.VideoCapture(0)

    cap = st.session_state.cap
    frame_placeholder = st.empty()
    score_placeholder = st.empty()
    state_placeholder = st.empty()

    while run:
        ret, frame = cap.read()
        if not ret:
            st.error("Camera error — could not read frame.")
            break

        h, w, _ = frame.shape
        landmarks = get_face_landmarks(frame)

        if landmarks:
            gaze = estimate_gaze(landmarks, w, h)
            face_detected = True
        else:
            gaze = "NO_FACE"
            face_detected = False

        score, state = engine.update(gaze, face_detected)

        cv2.putText(frame, f"Focus: {score}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Gaze: {gaze}", (30, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Convert BGR → RGB for Streamlit
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(frame_rgb)

        score_placeholder.markdown(f"### Focus Score: {score}")
        state_placeholder.markdown(f"### State: {state}")

else:
    # Release camera when checkbox is unchecked
    if st.session_state.cap is not None and st.session_state.cap.isOpened():
        st.session_state.cap.release()
        st.session_state.cap = None