"""Speaker — macOS TTS with optional ElevenLabs upgrade.

Fixes vs original:
- Strip markdown before TTS (bold, headers, bullets crash `say` with long timeouts)
- Cap spoken text at 450 chars so `say` never hangs
- play_chirp() — generates a futuristic ascending tone played via afplay
"""
import logging
import math
import os
import re
import struct
import subprocess
import tempfile
import wave
from queue import Queue
from threading import Thread

from core.config import cfg, env

log = logging.getLogger("jarvis.speaker")
_queue: Queue = Queue()
_worker: Thread = None


# ── Markdown stripper ─────────────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    """Remove markdown formatting so TTS reads cleanly."""
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', '', text)
    # Headers → plain text
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Bold / italic
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    # Horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Bullet / numbered lists → sentence breaks
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # Links
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Emoji clusters (keep single emoji, remove stacked ones)
    text = re.sub(r'[\U0001F300-\U0001FAFF]{2,}', '', text)
    # Collapse whitespace / blank lines
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _tts_clip(text: str, max_chars: int = 450) -> str:
    """Strip markdown and truncate for TTS so `say` never hangs."""
    clean = _strip_markdown(text)
    if len(clean) <= max_chars:
        return clean
    # Cut at last sentence boundary within limit
    cut = clean[:max_chars]
    last = max(cut.rfind('. '), cut.rfind('! '), cut.rfind('? '))
    return (cut[:last + 1] if last > 50 else cut) + "…"


# ── Futuristic activation chirp ───────────────────────────────────────────────

def play_chirp(kind: str = "wake"):
    """
    Generate and play a short sci-fi tone using afplay.
    kind='wake'    → ascending chirp (JARVIS activating / listening)
    kind='done'    → descending chirp (command acknowledged)
    kind='alert'   → double ping
    """
    rate     = 22050
    duration = 0.35   # seconds

    samples = []
    n = int(rate * duration)
    for i in range(n):
        t = i / rate
        progress = t / duration

        if kind == "wake":
            # 300 Hz → 1400 Hz, exponential sweep
            freq = 300 * (1400 / 300) ** progress
        elif kind == "done":
            # 1200 Hz → 350 Hz
            freq = 1200 * (350 / 1200) ** progress
        else:  # alert — two pulses
            pulse = math.sin(progress * math.pi * 2) ** 2
            freq  = 800 + 400 * pulse

        # Smooth envelope: fast attack, gentle decay
        env_val = min(progress * 12, 1.0) * (1 - progress) ** 0.5
        val = int(28000 * env_val * math.sin(2 * math.pi * freq * t))
        samples.append(struct.pack('<h', max(-32767, min(32767, val))))

    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp.close()
    wf = wave.open(tmp.name, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(rate)
    wf.writeframes(b''.join(samples))
    wf.close()

    try:
        subprocess.Popen(['afplay', tmp.name],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log.debug(f"afplay error: {e}")
    finally:
        # Delete after a short delay (afplay reads async)
        def _cleanup():
            import time; time.sleep(2)
            try: os.unlink(tmp.name)
            except: pass
        Thread(target=_cleanup, daemon=True).start()


# ── Sentence chunker (prevents `say` timeout on long responses) ───────────────

def _split_sentences(text: str, max_chars: int = 180) -> list:
    """
    Split cleaned text into sentence-sized chunks safe for `say`.
    Each chunk ≤ max_chars so a 30 s timeout is never hit.
    """
    clean = _strip_markdown(text)
    if not clean:
        return []
    # Split at sentence-ending punctuation followed by space / end-of-string
    parts = re.split(r'(?<=[.!?])\s+', clean)
    chunks, current = [], ""
    for part in parts:
        if len(current) + len(part) + 1 <= max_chars:
            current = (current + " " + part).strip() if current else part
        else:
            if current:
                chunks.append(current)
            # part itself too long — hard-break at word boundary
            while len(part) > max_chars:
                cut = part[:max_chars].rsplit(" ", 1)
                chunks.append(cut[0])
                part = cut[1] if len(cut) > 1 else part[max_chars:]
            current = part
    if current:
        chunks.append(current)
    return chunks


# ── TTS engines ───────────────────────────────────────────────────────────────

def _macos_say_raw(text: str):
    """Speak a single already-clean chunk. 20 s timeout per chunk is plenty."""
    voice = cfg["voice"]["macos_voice"]
    rate  = cfg["voice"]["speech_rate"]
    try:
        subprocess.run(["say", "-v", voice, "-r", str(rate), text], timeout=20)
    except Exception as e:
        log.error(f"say error: {e}")


def _speak_sync(text: str):
    engine   = cfg["voice"]["tts_engine"]
    chunks   = _split_sentences(text)
    if not chunks:
        return
    if engine == "elevenlabs":
        _elevenlabs(" ".join(chunks))   # ElevenLabs handles length itself
    else:
        for chunk in chunks:
            _macos_say_raw(chunk)


def _elevenlabs(text: str):
    try:
        from elevenlabs import generate, play
        audio = generate(
            text=text,
            voice=env("ELEVENLABS_VOICE_ID", "Josh"),
            api_key=env("ELEVENLABS_API_KEY"),
        )
        play(audio)
    except Exception as e:
        log.warning(f"ElevenLabs failed, falling back to say: {e}")
        for chunk in _split_sentences(text):
            _macos_say_raw(chunk)


# ── Worker thread ─────────────────────────────────────────────────────────────

def _set_listener_muted(muted: bool):
    """Mute/unmute the browser listener so JARVIS doesn't hear itself."""
    try:
        from voice.browser_listener import get_listener
        get_listener().set_muted(muted)
    except Exception:
        pass


def _broadcast_speaking(muted: bool, text: str = ""):
    """Notify the UI via the event bus so JS mutes mic capture and shows word animation."""
    try:
        from core.bus import bus
        payload: dict = {"speaking": muted}
        if muted and text:
            payload["text"] = _strip_markdown(text)
        bus.publish_sync("jarvis.speaking", payload)
    except Exception:
        pass


def _run_worker():
    log.info("Speaker worker started")
    while True:
        try:
            text = _queue.get()
            if text is None:
                break
            log.info(f"Speaking: '{text[:80]}{'…' if len(text) > 80 else ''}'")
            _set_listener_muted(True)
            _broadcast_speaking(True, text)
            try:
                _speak_sync(text)
            except Exception as e:
                log.error(f"_speak_sync error: {e}", exc_info=True)
            finally:
                _set_listener_muted(False)
                _broadcast_speaking(False)
            _queue.task_done()
        except Exception as e:
            log.error(f"Speaker worker loop error: {e}", exc_info=True)
            # Don't let the worker die — loop continues
    log.warning("Speaker worker stopped")


def start():
    global _worker
    _worker = Thread(target=_run_worker, daemon=True, name="speaker-worker")
    _worker.start()
    log.info("Speaker started")


def speak(text: str):
    """Queue text for speech (non-blocking)."""
    if not text:
        log.debug("speak() called with empty text — ignored")
        return
    log.info(f"speak() queued: '{text[:60]}{'…' if len(text) > 60 else ''}'")
    _queue.put(text)


def stop():
    _queue.put(None)
