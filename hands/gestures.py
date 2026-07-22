"""
Gesture engine — turns MediaPipe hand landmarks into JARVIS OS events.

Pure logic, no camera or MediaPipe imports: feed it 21 (x, y) landmark tuples
per frame (normalised 0..1, already mirrored to screen orientation) and it
returns a list of event dicts:

    {type: "cursor",     x, y, pinched}   fingertip position (EMA-smoothed)
    {type: "pinch_down", x, y}            thumb+index closed → click/grab
    {type: "pinch_up",   x, y}            released
    {type: "scroll",     dy}              two-finger vertical scroll
    {type: "zoom",       ds}              open-hand spread change
    {type: "hand_lost"}                   no hand for a few frames

Landmark indices (MediaPipe Hands):
    0 wrist · 4 thumb tip · 6 index pip · 8 index tip
    10 middle pip · 12 middle tip · 14 ring pip · 16 ring tip
    18 pinky pip · 20 pinky tip · 9 middle mcp
"""
from dataclasses import dataclass, field


def _dist(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


@dataclass
class GestureEngine:
    # Pinch hysteresis — thresholds are ratios of hand size (wrist→middle-mcp)
    pinch_close: float = 0.40
    pinch_open:  float = 0.55
    ema_alpha:   float = 0.38     # cursor smoothing (higher = snappier)
    scroll_gain: float = 2.6
    lost_after:  int   = 6        # frames without a hand → hand_lost

    _pinched:   bool  = False
    _cx:        float = 0.5
    _cy:        float = 0.5
    _have_cursor: bool = False
    _scroll_ref: float = None
    _spread_ref: float = None
    _missing:   int   = 0
    _was_present: bool = False

    def update(self, lm) -> list:
        """lm = list of 21 (x, y) tuples, or None if no hand this frame."""
        if lm is None:
            self._missing += 1
            if self._was_present and self._missing >= self.lost_after:
                self._was_present = False
                self._scroll_ref = None
                self._spread_ref = None
                events = [{"type": "hand_lost"}]
                if self._pinched:
                    self._pinched = False
                    events.insert(0, {"type": "pinch_up", "x": self._cx, "y": self._cy})
                return events
            return []

        self._missing = 0
        self._was_present = True
        events = []

        hand_size = _dist(lm[0], lm[9]) or 1e-6
        pinch_ratio = _dist(lm[4], lm[8]) / hand_size

        index_ext  = _dist(lm[8],  lm[0]) > _dist(lm[6],  lm[0])
        middle_ext = _dist(lm[12], lm[0]) > _dist(lm[10], lm[0])
        ring_ext   = _dist(lm[16], lm[0]) > _dist(lm[14], lm[0])
        pinky_ext  = _dist(lm[20], lm[0]) > _dist(lm[18], lm[0])

        # Cursor target: index tip normally, thumb-index midpoint while pinched
        # (the midpoint doesn't jump when the fingers close)
        if self._pinched or pinch_ratio < self.pinch_close:
            tx = (lm[4][0] + lm[8][0]) / 2
            ty = (lm[4][1] + lm[8][1]) / 2
        else:
            tx, ty = lm[8][0], lm[8][1]

        if not self._have_cursor:
            self._cx, self._cy = tx, ty
            self._have_cursor = True
        else:
            a = self.ema_alpha
            self._cx += a * (tx - self._cx)
            self._cy += a * (ty - self._cy)

        # ── Pinch (click / grab) — takes priority over everything ─────────────
        if not self._pinched and pinch_ratio < self.pinch_close:
            self._pinched = True
            self._scroll_ref = None
            self._spread_ref = None
            events.append({"type": "pinch_down", "x": self._cx, "y": self._cy})
        elif self._pinched and pinch_ratio > self.pinch_open:
            self._pinched = False
            events.append({"type": "pinch_up", "x": self._cx, "y": self._cy})

        # ── Scroll: index+middle up, ring+pinky down, not pinched ─────────────
        scroll_pose = (index_ext and middle_ext and not ring_ext
                       and not pinky_ext and not self._pinched)
        if scroll_pose:
            mid_y = (lm[8][1] + lm[12][1]) / 2
            if self._scroll_ref is not None:
                dy = (mid_y - self._scroll_ref) * self.scroll_gain
                if abs(dy) > 0.002:
                    events.append({"type": "scroll", "dy": round(dy, 4)})
            self._scroll_ref = mid_y
        else:
            self._scroll_ref = None

        # ── Zoom: open hand (all fingers extended), spread changing ───────────
        open_hand = (index_ext and middle_ext and ring_ext and pinky_ext
                     and not self._pinched)
        if open_hand:
            tips = [lm[4], lm[8], lm[12], lm[16], lm[20]]
            cx = sum(p[0] for p in tips) / 5
            cy = sum(p[1] for p in tips) / 5
            spread = sum(_dist(p, (cx, cy)) for p in tips) / 5 / hand_size
            if self._spread_ref is not None:
                ds = spread - self._spread_ref
                if abs(ds) > 0.015:
                    events.append({"type": "zoom", "ds": round(ds, 4)})
            self._spread_ref = spread
        else:
            self._spread_ref = None

        events.append({
            "type": "cursor",
            "x": round(self._cx, 4),
            "y": round(self._cy, 4),
            "pinched": self._pinched,
        })
        return events
