"""
BrowserListener — receives raw PCM audio streamed from the browser via WebSocket.

State machine
─────────────
  STANDBY           → waiting for launch trigger (double-clap + "wake up jarvis")
  IDLE              → accumulating pre-roll, waiting for speech energy
  RECORDING         → speech detected, recording until silence
  TRANSCRIBING      → Whisper running in thread
  WAITING_CMD       → bare "jarvis" heard, chirp+ack spoken, waiting for follow-up
  CONVERSATION MODE → JARVIS just replied; next speech (≥4 words) needs no wake word
                      (expires after CONVERSATION_WINDOW seconds)
"""
import asyncio
import logging
import re
import struct
import tempfile
import time
import wave
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger("jarvis.browser_listener")

RATE                = 16000
SPEECH_THRESH       = 0.020   # RMS threshold — raised from 0.008 to suppress ambient TV/background
SILENCE_SECS        = 1.5     # natural pause — 1.5s is snappy without cutting sentences short
MAX_SECS            = 12.0    # hard cap per utterance (was 20) — shorter = faster Whisper
PRE_ROLL            = 4
CONVERSATION_WINDOW = 20.0    # seconds after JARVIS speaks where reply needs no wake word
MIN_CONV_WORDS      = 7       # conversational replies must be at least this many words
                               # (guards against ambient noise triggering responses)

# Whisper tends to hallucinate these short phrases from ambient noise/TV.
# Any transcription fully matching one of these patterns is silently dropped.
_HALLUCINATION_RE = re.compile(
    r"^("
    r"(yeah[.,!]?\s*)+"            # "Yeah.", "Yeah yeah."
    r"|(okay[.,!]?\s*)+"           # "Okay.", "Okay okay."
    r"|(ok[.,!]?\s*)+"             # "Ok."
    r"|(uh+[.,!]?\s*)+"            # "Uh.", "Uhh."
    r"|(um+[.,!]?\s*)+"            # "Um."
    r"|(hmm+[.,!]?\s*)+"           # "Hmm."
    r"|thank\s+you.*"              # "Thank you so much."
    r"|thanks\s+for.*"             # "Thanks for watching."
    r"|(so[,.]?\s+){2,}.*"         # "So, so, anyway."
    r"|you\s+too[.,!]?.*"          # "You too."
    r"|see\s+you\s+later[.,!]?.*"  # "See you later."
    r"|bye[.,!]?.*"                # "Bye."
    r")\s*$",
    re.IGNORECASE,
)

# Launch trigger
LAUNCH_PHRASE       = "wake up jarvis"
CLAP_THRESH         = 0.18    # RMS spike considered a clap/knock
CLAP_WINDOW         = 2.0     # two claps must be within this many seconds
LAUNCH_TIMEOUT      = 6.0     # seconds after double-clap to say the phrase


class BrowserListener:
    """Singleton — one per JARVIS process. Fed by /ws/audio WebSocket."""

    def __init__(self):
        # Callbacks
        self._on_wake:         Optional[Callable] = None   # bare "Jarvis" → chirp + "Yes sir"
        self._on_wake_quiet:   Optional[Callable] = None   # "Jarvis + cmd" → chirp only
        self._on_command:      Optional[Callable] = None
        self._on_launch:       Optional[Callable] = None   # called once when launch phrase heard
        self._model = None

        # VAD state
        self._pre_roll:    list = []
        self._recording:   list = []
        self._in_speech:   bool = False
        self._silence_ct:  int  = 0

        # Conversation / wake state
        self._active:               bool  = False
        self._waiting_command:      bool  = False
        self._muted:                bool  = False
        self._conversation_expires: float = 0.0
        self._skip_next_conv_window:bool  = False  # set for startup/proactive speech

        # Launch mode
        self._standby:          bool  = True     # True until launch phrase heard
        self._clap_times:       list  = []       # timestamps of detected claps
        self._launch_armed:     float = 0.0      # epoch time when double-clap detected

        # Command deduplication — one command in flight at a time.
        # If a second command arrives while one is processing, hold it here
        # (overwriting on each new utterance) and run it when the current one finishes.
        self._processing:           bool  = False
        self._queued_command:       str   = ""

        # Extra wake words — agent names added when a Layer-2 window is open
        self._extra_wake_words:     set   = set()

        # UI push callback
        self._notify: Optional[Callable] = None

    # ── Setup ─────────────────────────────────────────────────────────────────

    def configure(self, on_wake: Callable, on_command: Callable,
                  on_wake_quiet: Optional[Callable] = None,
                  notify: Optional[Callable] = None):
        self._on_wake        = on_wake
        self._on_wake_quiet  = on_wake_quiet or on_wake   # fallback to on_wake
        self._on_command     = on_command
        self._notify         = notify

    def set_launch_callback(self, cb: Callable):
        self._on_launch = cb

    def load_model(self):
        log.info("Loading faster-whisper (base.en) for browser listener…")
        # cpu_threads=4 / num_workers=1 prevents the OpenMP semaphore crash on
        # Apple Silicon + Python 3.9 + ctranslate2 4.x.
        # inter_threads=1 keeps the session count to 1 (sufficient for our use).
        import os
        os.environ.setdefault("OMP_NUM_THREADS",        "1")
        os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
        from faster_whisper import WhisperModel
        self._model = WhisperModel(
            "base.en",
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=1,
        )
        log.info("Whisper ready")

    def set_muted(self, muted: bool):
        """
        Called by speaker so we don't detect JARVIS's own voice.
        When unmuted after a COMMAND response, open the conversation window.
        When unmuted after proactive/startup speech, skip the window.
        """
        self._muted = muted
        if not muted:
            if self._skip_next_conv_window:
                self._skip_next_conv_window = False
                log.debug("Conversation window suppressed (proactive speech)")
            else:
                self._conversation_expires = time.monotonic() + CONVERSATION_WINDOW
                log.debug(f"Conversation window open for {CONVERSATION_WINDOW:.0f}s")

    def skip_conversation_window(self):
        """Call before speaking a proactive/startup message to suppress the window."""
        self._skip_next_conv_window = True

    def set_wake_words(self, extra: set):
        """
        Set additional wake words alongside 'jarvis'.
        Called by sub_apps when a Layer-2 window opens/closes.
        e.g. set_wake_words({'ultron'}) → 'Hey Ultron, ...' is accepted.
        Pass an empty set to revert to 'jarvis' only.
        """
        self._extra_wake_words = {w.lower() for w in extra}
        if extra:
            log.info(f"Wake words: jarvis + {extra}")
        else:
            log.info("Wake words: jarvis only")

    def activate(self):
        """Called when launch phrase is heard — exit standby mode."""
        self._standby = False
        log.info("BrowserListener: standby mode OFF — full voice pipeline active")

    # ── Main entry point ──────────────────────────────────────────────────────

    async def process_chunk(self, data: bytes):
        """
        data = raw Int16 LE PCM at 16 kHz sent from browser JS.
        """
        rms = self._rms(data)

        # ── STANDBY: listen only for double-clap + launch phrase ──────────────
        if self._standby:
            await self._standby_detect(data, rms)
            return

        if self._muted or self._active:
            return

        if not self._in_speech:
            self._pre_roll.append(data)
            if len(self._pre_roll) > PRE_ROLL:
                self._pre_roll.pop(0)
            if rms > SPEECH_THRESH:
                self._in_speech  = True
                self._silence_ct = 0
                self._recording  = list(self._pre_roll)
                log.info(f"Speech started (RMS={rms:.4f})")
        else:
            self._recording.append(data)
            chunk_secs = len(data) / 2 / RATE
            if rms < SPEECH_THRESH:
                self._silence_ct += 1
                if self._silence_ct * chunk_secs >= SILENCE_SECS:
                    await self._flush()
            else:
                self._silence_ct = 0
            total_secs = sum(len(c) for c in self._recording) / 2 / RATE
            if total_secs >= MAX_SECS:
                await self._flush()

    # ── Standby detection (double-clap + phrase) ──────────────────────────────

    async def _standby_detect(self, data: bytes, rms: float):
        now = time.monotonic()

        # Detect clap/knock: a sudden high-energy spike
        if rms > CLAP_THRESH:
            # Only count if this spike isn't within 0.3s of the last one (de-bounce)
            if not self._clap_times or now - self._clap_times[-1] > 0.3:
                self._clap_times.append(now)
                log.debug(f"Clap detected (RMS={rms:.3f}), total={len(self._clap_times)}")
                # Keep only claps within the clap window
                self._clap_times = [t for t in self._clap_times if now - t <= CLAP_WINDOW]
                if len(self._clap_times) >= 2:
                    # Double-clap! Arm the launch window.
                    self._launch_armed = now
                    self._clap_times   = []
                    log.info("Double-clap detected — listening for launch phrase…")
                    await self._notify_ui("clap_detected", {})

        # Check if we're in the launch window and have speech to transcribe
        if self._launch_armed and now - self._launch_armed <= LAUNCH_TIMEOUT:
            # Accumulate audio for transcription check
            if not self._in_speech:
                self._pre_roll.append(data)
                if len(self._pre_roll) > PRE_ROLL:
                    self._pre_roll.pop(0)
                if rms > SPEECH_THRESH:
                    self._in_speech  = True
                    self._silence_ct = 0
                    self._recording  = list(self._pre_roll)
            else:
                self._recording.append(data)
                chunk_secs = len(data) / 2 / RATE
                if rms < SPEECH_THRESH:
                    self._silence_ct += 1
                    if self._silence_ct * chunk_secs >= SILENCE_SECS:
                        await self._check_launch_phrase()
                else:
                    self._silence_ct = 0
        elif self._launch_armed and now - self._launch_armed > LAUNCH_TIMEOUT:
            # Timed out — reset
            self._launch_armed  = 0.0
            self._recording     = []
            self._in_speech     = False
            self._silence_ct    = 0
            log.info("Launch phrase window timed out")

    async def _check_launch_phrase(self):
        chunks = self._recording[:]
        self._recording  = []
        self._in_speech  = False
        self._silence_ct = 0
        self._launch_armed = 0.0

        text = await asyncio.to_thread(self._transcribe, chunks)
        if not text:
            return
        log.debug(f"[Standby] Heard: '{text}'")

        if LAUNCH_PHRASE in text.lower():
            log.info("Launch phrase confirmed — activating JARVIS!")
            await self._notify_ui("launching", {})
            self.activate()
            if self._on_launch:
                self._on_launch()
        else:
            log.info(f"Not launch phrase: '{text}' — still in standby")

    # ── Flush utterance ───────────────────────────────────────────────────────

    async def _flush(self):
        chunks = self._recording[:]
        self._recording  = []
        self._in_speech  = False
        self._silence_ct = 0
        self._pre_roll   = []
        if chunks:
            asyncio.create_task(self._handle_utterance(chunks))

    async def _handle_utterance(self, chunks: list):
        text = await asyncio.to_thread(self._transcribe, chunks)
        if not text:
            return

        # ── Hallucination filter ──────────────────────────────────────────────
        if _HALLUCINATION_RE.match(text.strip()):
            log.debug(f"Hallucination filtered: '{text}'")
            return

        log.debug(f"Heard: '{text}'")

        # ── Deduplication: if a command is in flight, queue this one ────────────
        if self._processing:
            log.info(f"Command in flight — queuing: '{text}'")
            self._queued_command = text   # last utterance wins
            return

        # ── Follow-up command (immediately after bare "Jarvis") ───────────────
        if self._waiting_command:
            self._waiting_command = False
            self._active          = False
            log.info(f"Follow-up command: '{text}'")
            await self._notify_ui("got_command", {"text": text})
            if self._on_command:
                self._processing = True
                self._on_command(text)
            return

        # ── Conversational reply (within window, minimum word count) ──────────
        word_count = len(text.strip().split())
        if time.monotonic() < self._conversation_expires and word_count >= MIN_CONV_WORDS:
            # Do NOT re-extend the window here — only extend when JARVIS actually responds
            # (set_muted(False) after TTS playback does the extension).
            log.info(f"Conversational reply ({word_count}w): '{text}'")
            await self._notify_ui("got_command", {"text": text})
            if self._on_command:
                self._processing = True
                command = self._extract_command(text) or text
                self._on_command(command)
            return

        # ── Wake-word check ───────────────────────────────────────────────────
        lower = text.lower()
        wake_words = {"jarvis"} | self._extra_wake_words
        heard_wake = next((w for w in wake_words if w in lower), None)
        if not heard_wake:
            return

        self._active = True
        log.info(f"Wake word detected ('{heard_wake}'): '{text}'")
        await self._notify_ui("wake", {})

        command = self._extract_command(text)

        if command:
            # "Jarvis, do X" — chirp only, no "Yes sir" (would interrupt the flow)
            log.info(f"Bundled command: '{command}'")
            if self._on_wake_quiet:
                self._on_wake_quiet()
            if self._on_command:
                self._processing = True
                self._on_command(command)
            self._active = False
        else:
            # Bare "Jarvis" — chirp + acknowledgement + wait for follow-up
            if self._on_wake:
                self._on_wake()
            self._waiting_command = True
            self._active          = False
            await self._notify_ui("waiting_command", {})

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_command(self, text: str) -> str:
        # Strip any recognised wake word (jarvis or active agent name)
        all_words = "|".join(re.escape(w) for w in {"jarvis"} | self._extra_wake_words)
        cleaned = re.sub(
            rf"(?i)(hey\s+|ok\s+|yo\s+|hi\s+)?({all_words})[,!.\s]*", " ", text
        ).strip()
        return cleaned if len(cleaned) >= 4 else ""

    def _transcribe(self, chunks: list) -> str:
        if not chunks or self._model is None:
            return ""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        try:
            wf = wave.open(tmp, "wb")
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(chunks))
            wf.close()
            segments, _ = self._model.transcribe(tmp, language="en", beam_size=1)
            return " ".join(seg.text for seg in segments).strip()
        except Exception as e:
            log.error(f"Transcription error: {e}")
            return ""
        finally:
            Path(tmp).unlink(missing_ok=True)

    async def _notify_ui(self, kind: str, payload: dict):
        if self._notify:
            try:
                await self._notify(kind, payload)
            except Exception:
                pass

    @staticmethod
    def _rms(data: bytes) -> float:
        n = len(data) // 2
        if n == 0:
            return 0.0
        shorts = struct.unpack(f"{n}h", data[:n * 2])
        return (sum(s * s for s in shorts) / n) ** 0.5 / 32768.0


# Module-level singleton
_listener = BrowserListener()


def get_listener() -> BrowserListener:
    return _listener
