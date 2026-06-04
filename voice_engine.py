"""
voice_engine.py — Jarvis voice pipeline
"""

from __future__ import annotations

import json
import queue
import threading
from pathlib import Path
from typing import Callable, Optional

# ── Optional heavy imports ─────────────────────────────────────────────────────
try:
    import sounddevice as sd
    _SD_OK = True
except ImportError:
    _SD_OK = False

try:
    from vosk import Model, KaldiRecognizer
    _VOSK_OK = True
except ImportError:
    _VOSK_OK = False

try:
    import pyttsx3
    _TTS_OK = True
except ImportError:
    _TTS_OK = False

# ── Configuration ──────────────────────────────────────────────────────────────
SAMPLE_RATE   = 16000
BLOCK_SIZE    = 8000
WAKE_WORDS    = {"hey jarvis", "jarvis", "hey jarvis wake up"}
MODEL_DIRS    = [
    "./vosk-model-small-en-us-0.15",
    "./vosk-model-en-us-0.22",
    "~/vosk-model-small-en-us-0.15",
    "~/vosk-model-en-us-0.22",
]

TTS_RATE    = 175
TTS_VOLUME  = 0.92


class VoiceEngine:
    def __init__(
        self,
        on_wake:       Optional[Callable[[], None]] = None,
        on_transcript: Optional[Callable[[str], None]] = None,
        on_status:     Optional[Callable[[str], None]] = None,
        model_path:    Optional[str] = None,
    ):
        self.on_wake       = on_wake       or (lambda: None)
        self.on_transcript = on_transcript or (lambda t: None)
        self.on_status     = on_status     or (lambda s: print(f"[Voice] {s}"))

        self.available   = _SD_OK and _VOSK_OK and _TTS_OK
        self._running    = False
        self._listening  = False
        self._thread: Optional[threading.Thread] = None
        self._tts_lock   = threading.Lock()
        self._audio_q: queue.Queue = queue.Queue()

        self._model:     Optional[Model]          = None
        self._rec:       Optional[KaldiRecognizer] = None
        self._tts_engine = None

        if not self.available:
            missing = []
            if not _SD_OK:   missing.append("sounddevice")
            if not _VOSK_OK: missing.append("vosk")
            if not _TTS_OK:  missing.append("pyttsx3")
            self.on_status(f"Voice disabled — missing packages: {', '.join(missing)}")
            return

        # Locate Vosk model
        mp = model_path or self._find_model()
        if mp is None:
            self.available = False
            self.on_status("Voice disabled — Vosk model not found.")
            return

        try:
            self._model = Model(mp)
            self._rec   = KaldiRecognizer(self._model, SAMPLE_RATE)
            self.on_status(f"Vosk model loaded: {mp}")
        except Exception as exc:
            self.available = False
            self.on_status(f"Vosk model error: {exc}")
            return

        try:
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate",   TTS_RATE)
            self._tts_engine.setProperty("volume", TTS_VOLUME)
            self.on_status("TTS engine ready.")
        except Exception as exc:
            self.on_status(f"TTS init warning: {exc}")

    def start(self) -> bool:
        if not self.available or self._running:
            return False
        self._running = True
        self._thread  = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        self.on_status("Listening for wake word …")
        return True

    def stop(self):
        self._running   = False
        self._listening = False
        if self._thread:
            self._thread.join(timeout=3)

    def speak(self, text: str):
        if not self.available or self._tts_engine is None:
            return

        def _do_speak():
            with self._tts_lock:
                try:
                    self._tts_engine.say(text)
                    self._tts_engine.runAndWait()
                except Exception as exc:
                    self.on_status(f"TTS error: {exc}")

        threading.Thread(target=_do_speak, daemon=True).start()

    def _find_model(self) -> Optional[str]:
        for mp in MODEL_DIRS:
            p = Path(mp).expand