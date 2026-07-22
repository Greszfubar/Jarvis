"""
Voice listener — two separate systems:

  LAUNCH TRIGGER (handled in main.py / app startup):
    Double clap + "wake up jarvis" → opens the JARVIS window.
    This file does NOT handle that.  It handles the always-on listener
    that runs once the app is already open.

  ALWAYS-ON LISTENER (this file):
    Pipeline once the app is running:
      1. Continuously monitor mic with VAD (cheap, low CPU).
      2. When speech energy detected → record utterance.
      3. Transcribe with Whisper.
      4. If "jarvis" appears anywhere in the transcription:
           → call on_wake()  (speaks "Yes sir" etc.)
           → if command was bundled in the same utterance, send it directly
           → otherwise record the follow-up utterance and send that
      5. No claps needed — just say "Jarvis" (or "Hey Jarvis", etc.)
"""
import logging
import re
import struct
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Callable

import pyaudio

log = logging.getLogger("jarvis.listener")

RATE     = 16000
CHUNK    = 512
FORMAT   = pyaudio.paInt16
CHANNELS = 1

# ── VAD thresholds ────────────────────────────────────────────────────────────
SPEECH_THRESH   = 0.006   # RMS to count as speech (lowered — macOS mic can be quiet)
SILENCE_SECS    = 1.0     # silence gap that ends an utterance
PRE_ROLL_CHUNKS = 6       # chunks kept before speech starts (capture leading consonants)
MAX_SECS        = 15      # hard cap per utterance
COMMAND_TIMEOUT = 8       # seconds to wait for follow-up command after "Yes sir"
DEBUG_RMS       = True    # prints RMS every 2s — set False once mic is confirmed working


class Listener:
    def __init__(self, on_wake: Callable, on_command: Callable):
        self._on_wake    = on_wake
        self._on_command = on_command
        self._model      = None
        self._running    = False
        self._active     = False   # True while processing a command (gate re-trigger)
        self._pa         = pyaudio.PyAudio()

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        log.info("Loading faster-whisper (base.en)…")
        from faster_whisper import WhisperModel
        self._model = WhisperModel("base.en", device="cpu", compute_type="int8")
        log.info("Whisper ready")
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True, name="vad-listener")
        t.start()
        log.info("Voice listener active — just say 'Jarvis' to activate")

    def stop(self):
        self._running = False

    # ── Main loop — always-on VAD ─────────────────────────────────────────────

    def _loop(self):
        stream = self._pa.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            input=True, frames_per_buffer=CHUNK,
        )
        log.info(f"Microphone open — speech threshold RMS={SPEECH_THRESH}")
        pre_roll   = []
        recording  = []
        in_speech  = False
        silence_ct = 0
        _last_rms_log = 0.0

        try:
            while self._running:
                raw = stream.read(CHUNK, exception_on_overflow=False)
                rms = self._rms(raw)

                # Optional: log RMS every 2s to help calibrate threshold
                import time as _t
                now = _t.time()
                if DEBUG_RMS and now - _last_rms_log > 2.0:
                    log.info(f"[VAD] RMS={rms:.4f}  threshold={SPEECH_THRESH}")
                    _last_rms_log = now

                if self._active:
                    in_speech  = False
                    recording  = []
                    pre_roll   = []
                    silence_ct = 0
                    continue

                if not in_speech:
                    pre_roll.append(raw)
                    if len(pre_roll) > PRE_ROLL_CHUNKS:
                        pre_roll.pop(0)

                    if rms > SPEECH_THRESH:
                        in_speech  = True
                        silence_ct = 0
                        recording  = list(pre_roll)
                        log.info(f"Speech detected (RMS={rms:.4f}) — recording…")
                else:
                    recording.append(raw)

                    if rms < SPEECH_THRESH:
                        silence_ct += 1
                        if silence_ct * CHUNK / RATE >= SILENCE_SECS:
                            # Utterance ended — transcribe and check
                            stream.stop_stream()
                            self._handle_utterance(recording[:], stream)
                            stream.start_stream()
                            in_speech  = False
                            recording  = []
                            pre_roll   = []
                            silence_ct = 0
                    else:
                        silence_ct = 0

                    # Hard cap
                    if len(recording) * CHUNK / RATE >= MAX_SECS:
                        stream.stop_stream()
                        self._handle_utterance(recording[:], stream)
                        stream.start_stream()
                        in_speech  = False
                        recording  = []
                        pre_roll   = []
                        silence_ct = 0

        finally:
            stream.stop_stream()
            stream.close()

    # ── Utterance handler ─────────────────────────────────────────────────────

    def _handle_utterance(self, frames: list, stream):
        """Transcribe a captured utterance and act if 'jarvis' is in it."""
        text = self._transcribe(frames).strip()
        if not text:
            return
        log.debug(f"Heard: '{text}'")

        if not self._mentions_jarvis(text):
            return

        # Jarvis was called
        self._active = True
        log.info(f"Jarvis mentioned: '{text}'")

        # Extract any command that was bundled in the same utterance
        command = self._extract_command(text)

        # Acknowledge
        self._on_wake()

        if command:
            log.info(f"Bundled command: '{command}'")
            self._on_command(command)
        else:
            # Listen for the follow-up
            stream.start_stream()
            cmd_frames = self._record_utterance(stream, timeout=COMMAND_TIMEOUT)
            stream.stop_stream()
            command = self._transcribe(cmd_frames).strip()
            log.info(f"Follow-up command: '{command}'")
            if command:
                self._on_command(command)

        self._active = False

    # ── Wake-word detection ───────────────────────────────────────────────────

    def _mentions_jarvis(self, text: str) -> bool:
        """Return True if 'jarvis' appears anywhere in the transcription."""
        return "jarvis" in text.lower()

    def _extract_command(self, text: str) -> str:
        """
        Strip the 'jarvis' trigger word (and any prefix like 'hey') and
        return whatever command follows.
        E.g. "hey jarvis what's the weather" → "what's the weather"
        E.g. "jarvis"                        → ""  (bare call)
        """
        cleaned = re.sub(
            r"(?i)(hey\s+|ok\s+|yo\s+|hi\s+)?jarvis[,!.\s]*",
            " ", text
        ).strip()
        # If under 4 chars it was just the name
        return cleaned if len(cleaned) >= 4 else ""

    # ── Recording helpers ─────────────────────────────────────────────────────

    def _record_utterance(self, stream, timeout: float) -> list:
        """VAD-based recording — stops on silence or timeout."""
        pre_roll   = []
        recording  = []
        in_speech  = False
        silence_ct = 0
        start      = time.time()

        while time.time() - start < timeout:
            raw = stream.read(CHUNK, exception_on_overflow=False)
            rms = self._rms(raw)

            if not in_speech:
                pre_roll.append(raw)
                if len(pre_roll) > PRE_ROLL_CHUNKS:
                    pre_roll.pop(0)
                if rms > SPEECH_THRESH:
                    in_speech  = True
                    silence_ct = 0
                    recording  = list(pre_roll)
            else:
                recording.append(raw)
                if rms < SPEECH_THRESH:
                    silence_ct += 1
                    if silence_ct * CHUNK / RATE >= SILENCE_SECS:
                        break
                else:
                    silence_ct = 0
                if len(recording) * CHUNK / RATE >= MAX_SECS:
                    break

        return recording if recording else pre_roll

    # ── Transcription ─────────────────────────────────────────────────────────

    def _transcribe(self, frames: list) -> str:
        if not frames:
            return ""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        try:
            wf = wave.open(tmp, "wb")
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self._pa.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
            wf.close()
            segments, _ = self._model.transcribe(tmp, language="en", beam_size=1)
            return " ".join(seg.text for seg in segments).strip()
        except Exception as e:
            log.error(f"Transcription error: {e}")
            return ""
        finally:
            Path(tmp).unlink(missing_ok=True)

    @staticmethod
    def _rms(data: bytes) -> float:
        if len(data) < 2:
            return 0.0
        shorts = struct.unpack(f"{len(data) // 2}h", data)
        return (sum(s * s for s in shorts) / len(shorts)) ** 0.5 / 32768.0
