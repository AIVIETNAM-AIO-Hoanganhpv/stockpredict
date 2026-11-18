"""Cấu trúc giá: đỉnh/đáy (swing), SMC (BOS, CHoCH, Order Block, FVG, thanh khoản) và ICT
(vùng Premium/Discount, OTE, killzone).

Chỉ dùng các đỉnh/đáy ĐÃ XÁC NHẬN (có đủ `k` nến bên phải) để không "nhìn trước tương lai".
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class Swing:
    i: int          # vị trí nến
    price: float
    kind: str       # "H" = đỉnh, "L" = đáy


@dataclass
class Zone:
    kind: str       # "OB" hoặc "FVG"
    side: int       # +1 tăng (hỗ trợ), -1 giảm (kháng cự)
    top: float
    bottom: float
    i: int          # nến tạo vùng


@dataclass
class Structure:
    swings: list = field(default_factory=list)
    events: list = field(default_factory=list)   # (i, "BOS"/"CHoCH", +1/-1, mức giá bị phá)
    trend: int = 0                                 # +1 tăng, -1 giảm, 0 chưa rõ
    order_blocks: list = field(default_factory=list)
    fvgs: list = field(default_factory=list)
    sweep: int = 0                                 # +1 quét thanh khoản đáy (tín hiệu tăng), -1 quét đỉnh
    equal_highs: list = field(default_factory=list)
    equal_lows: list = field(default_factory=list)


def swings(df: pd.DataFrame, k: int = 3) -> list:
    """Đỉnh/đáy fractal: cao/thấp nhất trong cửa sổ k nến mỗi bên."""
    h, l = df["high"].to_numpy(), df["low"].to_numpy()
    out = []
    for i in range(k, len(df) - k):
        # Lớn hơn hẳn các nến bên trái, không nhỏ hơn các nến bên phải (chịu được đỉnh bằng nhau)
        if h[i] > h[i - k:i].max() and h[i] >= h[i + 1:i + k + 1].max():
            out.append(Swing(i, float(h[i]), "H"))
        if l[i] < l[i - k:i].min() and l[i] <= l[i + 1:i + k + 1].min():
            out.append(Swing(i, float(l[i]), "L"))
    return out


def _last_opposite_candle(df, start, end, bullish):
    """Nến ngược màu cuối cùng trước cú bứt phá → Order Block."""
    o, c = df["open"].to_numpy(), df["close"].to_numpy()
    for j in range(end, start - 1, -1):
        if bullish and c[j] < o[j]:
            return j
        if not bullish and c[j] > o[j]:
            return j
    return None


def analyze(df: pd.DataFrame, k: int = 3, atr_val: float | None = None) -> Structure:
    st = Structure(swings=swings(df, k))
    n = len(df)
    if n < 2 * k + 5:
        return st
    h, l, c = df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy()
    atr_val = atr_val or float(np.nanmean(h[-50:] - l[-50:]))

    # Swing được xác nhận ở nến i + k
    confirm = {}
    for s in st.swings:
        confirm.setdefault(s.i + k, []).append(s)

    last_h = last_l = None      # đỉnh/đáy gần nhất chưa bị phá
    trend = 0
    for i in range(n):
        for s in confirm.get(i, []):
            if s.kind == "H":
                last_h = s
            else:
                last_l = s
        if last_h is not None and c[i] > last_h.price:
            kind = "BOS" if trend >= 0 else "CHoCH"
            st.events.append((i, kind, 1, last_h.price))
            ob = _last_opposite_candle(df, last_l.i if last_l else max(0, i - 10), i, True)
            if ob is not None:
                st.order_blocks.append(Zone("OB", 1, float(h[ob]), float(l[ob]), ob))
            trend, last_h = 1, None
        elif last_l is not None and c[i] < last_l.price:
            kind = "BOS" if trend <= 0 else "CHoCH"
            st.events.append((i, kind, -1, last_l.price))
            ob = _last_opposite_candle(df, last_h.i if last_h else max(0, i - 10), i, False)
            if ob is not None:
                st.order_blocks.append(Zone("OB", -1, float(h[ob]), float(l[ob]), ob))
            trend, last_l = -1, None
    st.trend = trend

    # Fair Value Gap: khoảng trống giữa nến i-2 và nến i
    for i in range(2, n):
        if l[i] > h[i - 2]:
            st.fvgs.append(Zone("FVG", 1, float(l[i]), float(h[i - 2]), i - 1))
        elif h[i] < l[i - 2]:
            st.fvgs.append(Zone("FVG", -1, float(l[i - 2]), float(h[i]), i - 1))

    # Bỏ vùng đã bị phá/lấp
    def alive(z: Zone):
        after_l, after_h, after_c = l[z.i + 2:], h[z.i + 2:], c[z.i + 2:]
        if z.kind == "OB":
            return not ((after_c < z.bottom).any() if z.side > 0 else (after_c > z.top).any())
        return not ((after_l <= z.bottom).any() if z.side > 0 else (after_h >= z.top).any())

    st.order_blocks = [z for z in st.order_blocks if alive(z)][-3:]
    st.fvgs = [z for z in st.fvgs if alive(z)][-4:]

    # Thanh khoản: đỉnh/đáy bằng nhau và cú quét (râu vượt rồi đóng cửa quay lại)
    tol = 0.15 * atr_val
    hs = [s for s in st.swings if s.kind == "H" and s.i + k < n][-6:]
    ls = [s for s in st.swings if s.kind == "L" and s.i + k < n][-6:]
    st.equal_highs = [a.price for a, b in zip(hs, hs[1:]) if abs(a.price - b.price) <= tol]
    st.equal_lows = [a.price for a, b in zip(ls, ls[1:]) if abs(a.price - b.price) <= tol]
    for j in range(max(0, n - 3), n):          # 3 nến gần nhất
        prev_h = [s.price for s in hs if s.i < j - 1]
        prev_l = [s.price for s in ls if s.i < j - 1]
        if prev_h and h[j] > prev_h[-1] and c[j] < prev_h[-1]:
            st.sweep = -1
        if prev_l and l[j] < prev_l[-1] and c[j] > prev_l[-1]:
            st.sweep = 1
    return st


def dealing_range(st: Structure):
    """Biên giao dịch hiện tại: đỉnh và đáy xác nhận gần nhất (ICT)."""
    hs = [s for s in st.swings if s.kind == "H"]
    ls = [s for s in st.swings if s.kind == "L"]
    if not hs or not ls:
        return None
    return hs[-1], ls[-1]


def killzone(ts) -> str | None:
    """Phiên ICT theo giờ New York: London 2–5h, New York 7–10h."""
    try:
        t = pd.Timestamp(ts)
        t = t.tz_localize("UTC") if t.tzinfo is None else t
        hour = t.tz_convert("America/New_York").hour
    except Exception:
        return None
    if 2 <= hour < 5:
        return "London"
    if 7 <= hour < 10:
        return "New York"
    return None


# --- LEVEL 1: xu hướng theo đỉnh/đáy và đếm nhịp -----------------------------------------
def trend_by_swings(st: Structure, tol_ratio: float = 0.01) -> int:
    """Đỉnh/đáy sau cao hơn đỉnh/đáy trước → tăng; thấp hơn → giảm; tương đương → đi ngang."""
    hs = [s.price for s in st.swings if s.kind == "H"][-2:]
    ls = [s.price for s in st.swings if s.kind == "L"][-2:]
    if len(hs) < 2 or len(ls) < 2:
        return 0
    eq = lambda a, b: abs(a - b) <= tol_ratio * max(abs(a), abs(b))  # noqa: E731
    if eq(*hs) and eq(*ls):
        return 0
    if hs[1] > hs[0] and ls[1] > ls[0]:
        return 1
    if hs[1] < hs[0] and ls[1] < ls[0]:
        return -1
    return 0


def count_legs(st: Structure, direction: int) -> int:
    """Số nhịp liên tiếp cùng chiều xu hướng (đếm số lần phá cấu trúc liên tiếp)."""
    legs = 0
    for _, _, side, _ in reversed(st.events):
        if side != direction:
            break
        legs += 1
    return legs
