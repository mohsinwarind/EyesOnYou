# guardian.py
# import anthropic
from email.mime import message

from event_system import HeadDirection, FocusEventType
from dotenv import load_dotenv
import os
from huggingface_hub import InferenceClient
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

def _get_client():
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN or HUGGINGFACEHUB_API_TOKEN must be set in .env")
    
    return InferenceClient(model=HF_MODEL, token=HF_TOKEN)


ESCALATION_TONE = {
    1: "firm and authoritative, like a strict mentor",
    2: "annoyed and disappointed, like a coach who expected better",
    3: "angry and harsh, like someone who is losing patience",
    4: "absolute intimidation — cold, merciless, no sympathy at all",
}


def build_guardian_prompt(
    event_type: FocusEventType,
    head_direction: HeadDirection,
    phone_detected: bool,
    distraction_count: int,
    session_number: int,
    time_remaining_seconds: int,
    escalation_level: int,
    guardian_name: str = "Your Guardian",
) -> str:
    minutes_left = time_remaining_seconds // 60
    seconds_left = time_remaining_seconds % 60
    tone = ESCALATION_TONE.get(escalation_level, ESCALATION_TONE[4])

    if event_type == FocusEventType.FOCUS_REGAINED:
        return f"""
You are {guardian_name}, a powerful and intense accountability guardian.
The user just returned to focus after being distracted.
This is distraction #{distraction_count} this session (session {session_number}).
There are {minutes_left}m {seconds_left}s remaining.

Acknowledge their return to focus briefly. Be {tone}. 
If escalation level is 1-2, give a small genuine acknowledgment.
If escalation level is 3-4, acknowledge but remind them sharply not to slip again.

Keep it under 2 sentences. Speak directly to them. No fluff.
"""

    direction_context = {
        HeadDirection.LEFT:   "looking to the LEFT — distracted by something on their left side",
        HeadDirection.RIGHT:  "looking to the RIGHT — distracted by something on their right side",
        HeadDirection.DOWN:   "looking DOWN — likely at their phone or desk",
        HeadDirection.UP:     "looking UP — daydreaming or zoning out",
        HeadDirection.ABSENT: "not even at their desk — completely absent",
    }.get(head_direction, "distracted")

    phone_context = " A PHONE was also detected in the frame." if phone_detected else ""

    return f"""
You are {guardian_name}, a powerful and intense accountability guardian watching this person work.
They are currently {direction_context}.{phone_context}

Context:
- This is distraction #{distraction_count} during Pomodoro session #{session_number}
- Time remaining in this session: {minutes_left}m {seconds_left}s
- Your tone should be: {tone}

Generate ONE short, punchy, intimidating message (2 sentences max) to snap them back to focus.
Make it specific to what they're doing wrong (direction, phone, absent).
Speak directly to them. Do not use quotation marks. No preamble.
"""


def get_guardian_message(
    event_type: FocusEventType,
    head_direction: HeadDirection,
    phone_detected: bool,
    distraction_count: int,
    session_number: int,
    time_remaining_seconds: int,
    escalation_level: int,
    guardian_name: str = "Your Guardian",
) -> str:
    client = _get_client()

    prompt = build_guardian_prompt(
        event_type=event_type,
        head_direction=head_direction,
        phone_detected=phone_detected,
        distraction_count=distraction_count,
        session_number=session_number,
        time_remaining_seconds=time_remaining_seconds,
        escalation_level=escalation_level,
        guardian_name=guardian_name,
    )

    message = client.chat_completion(
        model=HF_MODEL,
        max_tokens=120,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.choices[0].message.content.strip()
