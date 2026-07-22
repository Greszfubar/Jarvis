"""
Hands service — camera → MediaPipe Hands → GestureEngine → bus events.

Runs a daemon capture thread. Events are published on the bus as
"hands.event" payloads; ui.os_routes forwards them to the OS page
over the existing /ws broadcast as kind "hands".

Started/stopped by the OS camera button via POST /api/os/camera.
"""
import logging
import threading
import time

from core.bus import bus
from hands.gestures import GestureEngine

log = logging.getLogger("jarvis.hands")

CAM_INDEX = 0
FRAME_W, FRAME_H = 640, 360


class HandsService:
    def __init__(self):
        self._thread = None
        self._stop = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="hands")
        self._thread.start()
        log.info("Hands service starting")

    def stop(self):
        self._stop.set()
        log.info("Hands service stopping")

    def _loop(self):
        try:
            import cv2
            import mediapipe as mp
        except ImportError as e:
            log.error(f"Hands service needs mediapipe + opencv: {e}")
            bus.publish_sync("hands.event", {"type": "error", "message": str(e)})
            return

        cap = cv2.VideoCapture(CAM_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
        if not cap.isOpened():
            log.error("Hands: camera not available (check macOS camera permission)")
            bus.publish_sync("hands.event", {"type": "error", "message": "camera unavailable"})
            return

        engine = GestureEngine()
        hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,          # fastest — fine for cursor work
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        bus.publish_sync("hands.event", {"type": "started"})
        log.info("Hands: tracking loop live")

        try:
            import base64
            frame_i = 0
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.05)
                    continue
                # Mirror once at the source: gestures AND the on-screen feed
                # both behave like a mirror (hand right → cursor right)
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = hands.process(rgb)

                lm = None
                if result.multi_hand_landmarks:
                    pts = result.multi_hand_landmarks[0].landmark
                    lm = [(p.x, p.y) for p in pts]

                for ev in engine.update(lm):
                    bus.publish_sync("hands.event", ev)

                # Faint live feed behind the OS — every 3rd frame (~10 fps)
                frame_i += 1
                if frame_i % 3 == 0:
                    small = cv2.resize(frame, (480, 270))
                    ok_j, jpg = cv2.imencode(
                        ".jpg", small, [int(cv2.IMWRITE_JPEG_QUALITY), 45]
                    )
                    if ok_j:
                        bus.publish_sync("hands.frame", {
                            "jpg": base64.b64encode(jpg.tobytes()).decode("ascii"),
                        })
        finally:
            cap.release()
            hands.close()
            bus.publish_sync("hands.event", {"type": "stopped"})
            log.info("Hands: tracking loop ended")


_service = HandsService()


def get_hands() -> HandsService:
    return _service
