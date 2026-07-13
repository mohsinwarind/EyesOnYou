# Eyes On You — v1.0

**An AI-powered Pomodoro focus coach that watches you work.**

---

## What is Eyes On You?
I was having random conversation with one of my friend where she shared her need to do group study because self-accountability isn't everyone's cup of tea, so, it triggered me the idea to code **Eyes On You** which
is a real-time focus monitoring application built on top of the Pomodoro technique. Instead of just being a timer, it actively watches you through your webcam and intervenes when you get distracted or pick up your phone using a Guardian AI that generates personalized, context-aware messages to snap you back to focus and the user specified guardian gets progressively angrier the more you slip up.

---

## How It Works

You configure a Pomodoro session and upload a photo of someone you're intimidated by which could  a professor, a coach, a parent, anyone. When you get distracted during a work session, the Guardian activates: their photo appears on screen, an AI-generated message calls you out based on exactly what you were doing wrong, and a voice reads it out loud.

```
Start Session
      ↓
Webcam monitors your attention in real time
      ↓
Distraction detected (looking away, phone, absent)
      ↓
Grace period countdown begins
      ↓
Guardian activates — photo + AI message + voice
      ↓
You refocus — Guardian acknowledges it
      ↓
Session ends with analytics report
```

---

## Features

**Focus Tracking**
- MediaPipe Face Mesh with 468 landmarks for stable, accurate head pose estimation
- Detects gaze direction: left, right, up, down, absent
- YOLOv8n phone detection which catches you scrolling
- Smoothing buffer eliminates jitter from natural head movement
- Configurable grace period (3–15 seconds) before guardian activates

**Guardian AI**
- Upload any photo as your guardian
- Claude-compatible LLM via HuggingFace Inference API generates context-aware messages
- Messages are specific to what you're doing wrong , for instance , looking left gets a different response than looking at your phone
- Four escalation levels based on distraction count: firm → annoyed → angry → full intimidation
- Guardian appreciates you when you return to focus
- 20-second cooldown between interventions so it doesn't nag constantly

**Pomodoro Engine**
- Configurable work and break durations
- Pause and resume support
- Session counter with visual dots
- Skeuomorphic clock face as the main UI element
- Automatic phase transitions

**Session Analytics**
- Total focus time vs distracted time
- Distraction count and type breakdown
- Longest focus streak
- Focus score out of 100
- Session history across multiple Pomodoros

**Browser-based TTS**
- Guardian messages are spoken aloud via gTTS
- Audio plays directly in the browser — works on cloud deployments

---

## Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| Webcam (cloud) | streamlit-webrtc + WebRTC |
| Face tracking | MediaPipe Face Mesh |
| Head pose | OpenCV solvePnP |
| Phone detection | YOLOv8n (Ultralytics) |
| Guardian LLM | HuggingFace Inference API |
| Voice | gTTS (browser audio) |
| Deployment | Streamlit Community Cloud |

---

## Project Structure

```
eyes_on_you/
│
├── app.py                  # Main Streamlit app, UI, session loop
├── pomodoro.py             # Pomodoro timer state machine
├── focus_tracker.py        # MediaPipe + YOLO attention detection
├── event_system.py         # Focus event types and logging
├── guardian.py             # LLM message generation via HuggingFace
├── tts_engine.py           # Browser-based text to speech
├── music_player.py         # Background audio (local only)
├── session_analytics.py    # Focus score and session summary
├── overlay_renderer.py     # Guardian photo overlay on webcam feed
├── requirements.txt
└── packages.txt
```

---

## Setup

**Local:**

```bash
git clone https://github.com/mohsinwarind/EyesOnYou
cd eyesonyou
pip install -r requirements.txt
cp .env.example .env
# Add your HF_TOKEN to .env
streamlit run app.py
```

**.env:**

```
HF_TOKEN=hf_your_token_here
HF_MODEL=meta-llama/Llama-3.2-3B-Instruct
```

**Streamlit Cloud:**

Add secrets under Settings → Secrets:

```toml
HF_TOKEN = "hf_your_token_here"
HF_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
```

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| Work duration | 25 min | Length of each focus session |
| Break duration | 5 min | Length of each break |
| Grace period | 8 sec | How long you can look away before guardian fires |
| Guardian cooldown | 20 sec | Minimum time between guardian interventions |

---

## Distraction Detection Logic

```
Frame captured
      ↓
Head direction checked (MediaPipe solvePnP)
Phone checked (YOLOv8n)
Face presence checked
      ↓
Any distraction? → Start grace period timer
Still distracted after grace period? → Fire guardian (once per distraction event)
Back to focus for 3+ seconds? → Reset + appreciation message
```

---

## Limitations in v1.0

- Background music disabled on cloud deployments (no server audio device)
- Guardian photo is static — no animation or video
- TTS voice is generic (gTTS) with no character customization
- WebRTC requires a TURN server on cloud platforms

---

## Roadmap — v2.0 (Hoping to implement soon)

- **Video generation** — animate the guardian photo into short reaction clips using generative video models
- **Premium TTS** — character voices via ElevenLabs or similar, matching the guardian's personality
- **Persistent sessions** — save focus history across days with trend graphs
- **Mobile support** — responsive layout optimized for phone browsers
- **Custom escalation scripts** — let users define what the guardian says at each level

---

## Built with love by
Mohsin Ramzan
---

