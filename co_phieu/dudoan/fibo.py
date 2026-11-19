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


# ------------------------------------------------------------------ chốt lời Fibo theo sóng của khung lệnh
NGUONG_TL = ((0.441, 1.618), (0.691, 1.272), (9.9, 1.0))     # hồi ~23,6–38,2% → 1.618 · ~50–61,8% → 1.272 · ~78,6% → 1.0
BAC_TL = [1.0, 1.272, 1.618, 2.0, 2.618]


def ti_le_theo_hoi(sau: float) -> float:
    """'Hồi ít thì lên nhiều' (tài liệu CHIẾN LƯỢC FIBONACCI)."""
    for nguong, tl in NGUONG_TL:
        if sau < nguong:
            return tl
    return 1.0


def muc_tieu_song(df_ngay, khung: str = "W", gia_vao: float | None = None, k: int | None = None) -> dict | None:
    """Mục tiêu chốt lời Fibo đo trên sóng tăng gần nhất của khung lệnh (W: lệnh tuần, M: lệnh tháng, D: ngày).
    A = đáy trước đỉnh B, B = đỉnh gần nhất đã xác nhận (k nến mỗi bên), C = giá thấp nhất từ sau B đến nay.
    Độ sâu hồi = (B − C)/(B − A) → tỉ lệ 1.618 / 1.272 / 1.0; mục tiêu = C + tỉ lệ × (B − A).
    Nếu mục tiêu ≤ giá vào + 1% thì nâng lên mức kế tiếp (1.0 → 1.272 → 1.618 → 2.0 → 2.618)."""
    from . import level1
    b = level1.nen_khung(df_ngay, khung)
    k = k or (3 if khung == "D" else 2)
    n = len(b)
    if n < 2 * k + 5:
        return None
    h, l = b["high"].to_numpy(float), b["low"].to_numpy(float)
    dinh = [p for p in range(k, n - k) if h[p] == h[p - k:p + k + 1].max()]
    day = [p for p in range(k, n - k) if l[p] == l[p - k:p + k + 1].min()]
    if not dinh:
        return None
    ib = dinh[-1]
    truoc = [p for p in day if p < ib]
    if not truoc:
        return None
    ia = truoc[-1]
    gia_vao = gia_vao if gia_vao is not None else float(df_ngay["close"].iloc[-1])

    def thu(A, B, C, ngay_a, ngay_b, moi):
        if not (B > A and C >= A):
            return None
        sau = (B - C) / (B - A)
        tl0 = ti_le_theo_hoi(sau)
        for x in BAC_TL:
            if x >= tl0 and C + x * (B - A) > gia_vao * 1.01:
                tp = C + x * (B - A)
                return {"khung": khung, "A": A, "B": B, "C": C, "ngay_A": ngay_a, "ngay_B": ngay_b, "do_sau": sau,
                        "ti_le": x, "chot_loi": tp, "lai_pct": tp / gia_vao - 1, "song_moi": moi}
        return None

    A, B = float(l[ia]), float(h[ib])
    sau_b = df_ngay.loc[df_ngay.index > b.index[ib], "low"]
    C = float(sau_b.min()) if len(sau_b) else float(l[ib])
    kq = thu(A, B, C, b.index[ia], b.index[ib], False) if C > A else None
    if kq:
        return kq
    # sóng cũ hỏng (phá đáy A) hoặc quá nhỏ so với giá → đo SÓNG MỚI: A = đáy thấp nhất sau đỉnh cũ, B = đỉnh cao nhất sau đó,
    # C = đáy hồi sau B
    if len(sau_b):
        ngay_a = sau_b.idxmin()
        A2 = min(float(sau_b.min()), A)
    else:
        ngay_a, A2 = b.index[ia], A
    sau_a = df_ngay.loc[df_ngay.index >= ngay_a]
    ngay_b = sau_a["high"].idxmax()
    B2 = float(sau_a["high"].max())
    C2 = float(df_ngay.loc[df_ngay.index >= ngay_b, "low"].min())
    return thu(A2, B2, C2, ngay_a, ngay_b, True)
