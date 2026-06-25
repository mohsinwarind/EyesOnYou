# music_player.py
import os
import pygame
# import urllib.request



MUSIC_PATH = "assets/dramatic.mp3"


class MusicPlayer:
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        # self._ensure_music()
        self._playing = False

    # def _ensure_music(self):
    #     os.makedirs("assets", exist_ok=True)
    #     if not os.path.exists(MUSIC_PATH):
    #         print("[Music] Downloading background music...")
    #         urllib.request.urlretrieve(DRAMATIC_MUSIC_URL, MUSIC_PATH)
    #         print("[Music] Downloaded.")

    def play(self, volume: float = 0.3):
        """Start looping background music at low volume."""
        if self._playing:
            return
        try:
            pygame.mixer.music.load(MUSIC_PATH)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=-1)
            self._playing = True
        except Exception as e:
            print(f"[Music] Error: {e}")

    def stop(self):
        if self._playing:
            pygame.mixer.music.stop()
            self._playing = False

    def is_playing(self) -> bool:
        return self._playing