# # tts_engine.py
# import os
# import threading
# import tempfile
# from gtts import gTTS
# import pygame


# class TTSEngine:
#     def __init__(self):
#         pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
#         if not pygame.mixer.get_init():
#             pygame.mixer.init()
#         self._lock = threading.Lock()

#     def speak(self, text: str, lang: str = "en", blocking: bool = False):
#         """Convert text to speech and play it. Non-blocking by default."""
#         if blocking:
#             self._play(text, lang)
#         else:
#             t = threading.Thread(target=self._play, args=(text, lang), daemon=True)
#             t.start()

#     def _play(self, text: str, lang: str):
#         with self._lock:
#             try:
#                 tts = gTTS(text=text, lang=lang, slow=False)
#                 with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
#                     tmp_path = f.name
#                 tts.save(tmp_path)

#                 # Use channel 1 for voice (channel 0 = music)
#                 sound = pygame.mixer.Sound(tmp_path)
#                 channel = pygame.mixer.Channel(1)
#                 channel.play(sound)

#                 # Wait for playback to finish
#                 while channel.get_busy():
#                     pygame.time.wait(50)

#                 os.unlink(tmp_path)
#             except Exception as e:
#                 print(f"[TTS] Error: {e}")

#     def stop(self):
#         pygame.mixer.Channel(1).stop()


# tts_engine.py
import io
import base64
import streamlit as st
from gtts import gTTS


class TTSEngine:
    def speak(self, text: str, lang: str = "en"):
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode()
            st.markdown(
                f'<audio autoplay style="display:none">'
                f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3">'
                f'</audio>',
                unsafe_allow_html=True
            )
        except Exception as e:
            print(f"[TTS] Error: {e}")

    def stop(self):
        pass