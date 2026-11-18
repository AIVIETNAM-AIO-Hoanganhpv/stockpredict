"""Fibonacci hồi (Retracement) và mở rộng (Extension) theo tài liệu CHIẾN LƯỢC FIBONACCI.

Quy tắc chốt lời "hồi ít thì lên nhiều" (độ sâu hồi thực tế → mức Extension):
  ~21,4%  → 1.618 hoặc 2.0
  ~38,2%  → 1.618
  ~50%    → 1.272 (hoặc bằng biên độ nhịp trước = 1.0)
  ~61,8%  → 1.272
  ~76,4%  → 1.0 hoặc 1.272
"""
from dataclasses import dataclass

RETRACE = [0.236, 0.382, 0.5, 0.618, 0.786]
EXTEND = [1.0, 1.272, 1.382, 1.618, 2.0]

# (độ sâu hồi, mục tiêu chính, mục tiêu phụ)
TP_RULES = [
    (0.214, 1.618, 2.0),
    (0.382, 1.618, None),
    (0.5, 1.272, 1.0),
    (0.618, 1.272, None),
    (0.764, 1.0, 1.272),
]


def retracement_levels(swing_high: float, swing_low: float, up: bool) -> dict:
    rng = swing_high - swing_low
    if up:   # kéo xuống từ đỉnh
        return {r: swing_high - rng * r for r in RETRACE}
    return {r: swing_low + rng * r for r in RETRACE}


def extension_levels(swing_high: float, swing_low: float, point3: float, up: bool) -> dict:
    rng = swing_high - swing_low
    if up:
        return {r: point3 + rng * r for r in EXTEND}
    return {r: point3 - rng * r for r in EXTEND}


def tp_ratios(depth: float):
    """Chọn mức Extension theo độ sâu hồi gần nhất trong bảng."""
    best = min(TP_RULES, key=lambda t: abs(t[0] - depth))
    return best[1], best[2]


@dataclass
class FiboPlan:
    up: bool
    swing_high: float
    swing_low: float
    point3: float          # đáy hồi (uptrend) / đỉnh hồi (downtrend)
    depth: float           # độ sâu hồi 0..1
    retrace: dict
    extend: dict
    tp1: float
    tp2: float | None
    sl: float


def plan(swing_high, swing_low, point3, up: bool, buffer: float = 0.0) -> FiboPlan | None:
    rng = swing_high - swing_low
    if rng <= 0:
        return None
    depth = (swing_high - point3) / rng if up else (point3 - swing_low) / rng
    depth = max(0.0, min(1.0, depth))
    r1, r2 = tp_ratios(depth)
    ext = extension_levels(swing_high, swing_low, point3, up)
    sign = 1 if up else -1
    tp = lambda r: point3 + sign * rng * r  # noqa: E731
    return FiboPlan(
        up=up, swing_high=swing_high, swing_low=swing_low, point3=point3, depth=depth,
        retrace=retracement_levels(swing_high, swing_low, up), extend=ext,
        tp1=tp(r1), tp2=tp(r2) if r2 else None,
        sl=point3 - sign * buffer,
    )
