"""Chấm điểm xu hướng cho một khung thời gian và gộp nhiều khung.

Mỗi yếu tố "bỏ phiếu" trong khoảng -1 (giảm) .. +1 (tăng) với một trọng số.
Điểm = trung bình có trọng số × 100, nằm trong -100..+100.
  > +20  → Tăng      < -20 → Giảm      còn lại → Đi ngang
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import cau_truc, chi_bao, fibo

NGUONG = 20
NHAN = {1: "Tăng", -1: "Giảm", 0: "Đi ngang"}


@dataclass
class Vote:
    ten: str
    gia_tri: float      # -1..+1
    trong_so: float
    ly_do: str


@dataclass
class KetQuaKhung:
    khung: str
    diem: float
    xu_huong: int
    gia: float
    votes: list = field(default_factory=list)
    fibo: object = None
    cau_truc: object = None
    ghi_chu: list = field(default_factory=list)

    @property
    def nhan(self):
        return NHAN[self.xu_huong]


def _sign(x, eps=0.0):
    return 1 if x > eps else (-1 if x < -eps else 0)


def _clip(x):
    return float(max(-1.0, min(1.0, x)))


def phan_tich_khung(df: pd.DataFrame, khung: str = "D", k: int | None = None) -> KetQuaKhung:
    df = df.dropna(subset=["open", "high", "low", "close"])
    if len(df) < 40:
        return KetQuaKhung(khung, 0.0, 0, float(df["close"].iloc[-1]) if len(df) else float("nan"),
                           ghi_chu=["Không đủ dữ liệu (cần ≥ 40 nến)."])
    k = k or (2 if khung in ("W", "M") else 3)
    c = df["close"]
    gia = float(c.iloc[-1])
    atr = float(chi_bao.atr(df).iloc[-1])
    votes: list[Vote] = []
    ghi_chu: list[str] = []

    # ---------- LEVEL 1: xu hướng ----------
    st = cau_truc.analyze(df, k=k, atr_val=atr)
    t_sw = cau_truc.trend_by_swings(st)
    votes.append(Vote("Đỉnh/đáy", t_sw, 2.0, {
        1: "Đỉnh sau cao hơn đỉnh trước, đáy sau cao hơn đáy trước",
        -1: "Đỉnh sau thấp hơn đỉnh trước, đáy sau thấp hơn đáy trước",
        0: "Đỉnh/đáy tương đương hoặc lẫn lộn → đi ngang"}[t_sw]))

    ma = chi_bao.sma(c, 20)
    tren = float((c.iloc[-20:] > ma.iloc[-20:]).mean())
    v_ma = 1 if tren >= 0.8 else (-1 if tren <= 0.2 else 0)
    votes.append(Vote("Vị thế giá/MA20", v_ma, 1.0,
                      f"{tren:.0%} số nến gần đây nằm trên MA20"
                      + (" (≥80% → tăng)" if v_ma > 0 else " (≤20% → giảm)" if v_ma < 0
                         else " → cắt lên xuống liên tục, đi ngang")))

    m = chi_bao.macd(df)
    cross = int((np.sign(m["hist"].iloc[-20:]).diff().fillna(0) != 0).sum())
    if cross >= 4:
        v_macd, ly = 0, f"MACD và đường tín hiệu cuốn vào nhau ({cross} lần cắt/20 nến)"
    else:
        h = m["hist"]
        v_macd = _sign(h.iloc[-1]) * (1.0 if _sign(h.iloc[-1] - h.iloc[-2]) == _sign(h.iloc[-1]) else 0.5)
        ly = ("MACD trên đường tín hiệu" if h.iloc[-1] > 0 else "MACD dưới đường tín hiệu") + \
             (", histogram đang mở rộng" if abs(v_macd) == 1 else ", histogram đang thu hẹp")
    votes.append(Vote("MACD", v_macd, 1.5, ly))

    ha = chi_bao.heikin_ashi(df).iloc[-3:]
    green = (ha["close"] > ha["open"])
    no_low = (ha[["open", "close"]].min(axis=1) - ha["low"]) <= 0.05 * atr
    no_up = (ha["high"] - ha[["open", "close"]].max(axis=1)) <= 0.05 * atr
    if green.all() and no_low.all():
        v_ha, ly = 1, "3 nến Heikin Ashi xanh liên tiếp, không râu dưới"
    elif (~green).all() and no_up.all():
        v_ha, ly = -1, "3 nến Heikin Ashi đỏ liên tiếp, không râu trên"
    elif green.all() or (~green).all():
        v_ha, ly = (0.5 if green.all() else -0.5), "Nến Heikin Ashi cùng màu nhưng còn râu"
    else:
        v_ha, ly = 0, "Nến Heikin Ashi xanh đỏ lẫn lộn"
    votes.append(Vote("Heikin Ashi", v_ha, 0.5, ly))

    # ---------- Chỉ báo dao động ----------
    s = chi_bao.stoch(df)
    kk, dd = s["k"].iloc[-1], s["d"].iloc[-1]
    kp, dp = s["k"].iloc[-2], s["d"].iloc[-2]
    if kp <= dp and kk > dd and kk < 50:
        v_st, ly = 1, f"Stoch %K cắt lên %D vùng thấp ({kk:.0f})"
    elif kp >= dp and kk < dd and kk > 50:
        v_st, ly = -1, f"Stoch %K cắt xuống %D vùng cao ({kk:.0f})"
    elif kk > 80:
        v_st, ly = -0.3, f"Stoch quá mua ({kk:.0f})"
    elif kk < 20:
        v_st, ly = 0.3, f"Stoch quá bán ({kk:.0f})"
    else:
        v_st, ly = 0.5 * _sign(kk - dd), f"Stoch %K {'trên' if kk > dd else 'dưới'} %D ({kk:.0f})"
    votes.append(Vote("Stochastic", v_st, 1.0, ly))

    mf = chi_bao.mfi(df)
    if mf.notna().iloc[-1] and df["volume"].iloc[-30:].sum() > 0:
        x = float(mf.iloc[-1])
        slope = float(mf.iloc[-1] - mf.iloc[-4])
        if x > 80:
            v_mf, ly = -0.7, f"MFI quá mua ({x:.0f}) – dòng tiền có thể chững"
        elif x < 20:
            v_mf, ly = 0.7, f"MFI quá bán ({x:.0f}) – dòng tiền có thể quay lại"
        else:
            v_mf = _clip(slope / 15) * 0.6 + (0.4 if x > 50 else -0.4)
            ly = f"MFI {x:.0f}, {'tăng' if slope > 0 else 'giảm'} trong 3 nến – dòng tiền {'vào' if x > 50 else 'ra'}"
        votes.append(Vote("MFI", _clip(v_mf), 1.0, ly))
    else:
        ghi_chu.append("Không có khối lượng (thường gặp ở forex) → bỏ qua MFI.")

    a = chi_bao.adx(df)
    adx_v, pdi, mdi = float(a["adx"].iloc[-1]), float(a["pdi"].iloc[-1]), float(a["mdi"].iloc[-1])
    if adx_v >= 25:
        votes.append(Vote("ADX", _sign(pdi - mdi), 1.0,
                          f"ADX {adx_v:.0f} ≥ 25: xu hướng mạnh, +DI {'>' if pdi > mdi else '<'} -DI"))
    else:
        votes.append(Vote("ADX", 0, 0.5, f"ADX {adx_v:.0f} < 25: xu hướng yếu"))

    # ---------- SMC ----------
    if st.events:
        i_ev, kind, side, lvl = st.events[-1]
        age = len(df) - 1 - i_ev
        w = 2.0 if age <= 10 else 1.5
        votes.append(Vote("SMC cấu trúc", side, w,
                          f"{kind} {'tăng' if side > 0 else 'giảm'} (phá {lvl:,.4g}) cách đây {age} nến"))
    zone_vote, zone_txt = 0.0, []
    for z in st.order_blocks + st.fvgs:
        if z.bottom - 0.2 * atr <= gia <= z.top + 0.2 * atr:
            zone_vote += 0.6 * z.side
            zone_txt.append(f"giá đang ở {z.kind} {'tăng' if z.side > 0 else 'giảm'} "
                            f"[{z.bottom:,.4g} – {z.top:,.4g}]")
    if zone_txt:
        votes.append(Vote("SMC vùng OB/FVG", _clip(zone_vote), 1.0, "; ".join(zone_txt)))
    if st.sweep:
        votes.append(Vote("Quét thanh khoản", st.sweep, 1.0,
                          "Râu quét dưới đáy cũ rồi đóng cửa quay lên" if st.sweep > 0
                          else "Râu quét trên đỉnh cũ rồi đóng cửa quay xuống"))

    # ---------- ICT: Premium/Discount + OTE ----------
    dr = cau_truc.dealing_range(st)
    plan = None
    if dr:
        H, L = dr
        mid = (H.price + L.price) / 2
        bias = st.trend or t_sw
        if H.price > L.price and bias:
            depth = (H.price - gia) / (H.price - L.price) if bias > 0 else (gia - L.price) / (H.price - L.price)
            if 0.62 <= depth <= 0.79:
                votes.append(Vote("ICT OTE", bias, 1.0,
                                  f"Giá trong vùng OTE (hồi {depth:.0%}) thuận xu hướng {NHAN[bias].lower()}"))
            elif bias > 0 and gia > mid:
                votes.append(Vote("ICT Premium/Discount", -0.3, 0.5,
                                  "Xu hướng tăng nhưng giá ở vùng Premium (đắt) – chờ hồi"))
            elif bias < 0 and gia < mid:
                votes.append(Vote("ICT Premium/Discount", 0.3, 0.5,
                                  "Xu hướng giảm nhưng giá ở vùng Discount (rẻ) – chờ hồi"))
        if khung in ("15m", "1H"):
            kz = cau_truc.killzone(df.index[-1])
            if kz:
                ghi_chu.append(f"Nến cuối nằm trong killzone {kz} (ICT) – biến động mạnh.")

        # Fibonacci cho kế hoạch giao dịch
        hs = [x for x in st.swings if x.kind == "H"]
        ls = [x for x in st.swings if x.kind == "L"]
        up = (bias or 1) > 0
        if up:
            hh = hs[-1]
            prev = [x for x in ls if x.i < hh.i]
            if prev:
                p3 = float(df["low"].iloc[hh.i + 1:].min()) if hh.i + 1 < len(df) else prev[-1].price
                plan = fibo.plan(hh.price, prev[-1].price, p3, True, buffer=0.3 * atr)
        else:
            ll = ls[-1]
            prev = [x for x in hs if x.i < ll.i]
            if prev:
                p3 = float(df["high"].iloc[ll.i + 1:].max()) if ll.i + 1 < len(df) else prev[-1].price
                plan = fibo.plan(prev[-1].price, ll.price, p3, False, buffer=0.3 * atr)

    # ---------- Nhịp sóng (Nguyên lý II) ----------
    if st.trend:
        legs = cau_truc.count_legs(st, st.trend)
        if legs >= 3:
            ghi_chu.append(f"Xu hướng đã chạy {legs} nhịp – giá thường đảo chiều ở nhịp 2, 3, 4, 6 → cẩn trọng.")
        elif legs:
            ghi_chu.append(f"Xu hướng đang ở nhịp {legs}.")

    tong_w = sum(v.trong_so for v in votes)
    diem = 100 * sum(v.gia_tri * v.trong_so for v in votes) / tong_w if tong_w else 0.0
    if adx_v < 20:
        diem *= 0.7
        ghi_chu.append("ADX < 20 → giảm độ tin cậy 30%.")
    xh = 1 if diem > NGUONG else (-1 if diem < -NGUONG else 0)
    return KetQuaKhung(khung, round(diem, 1), xh, gia, votes, plan, st, ghi_chu)


@dataclass
class KetQua:
    ma: str
    loai: str
    khung: list            # list[KetQuaKhung], khung lớn → nhỏ
    diem: float
    xu_huong: int
    dong_thuan: str
    ghi_chu: list = field(default_factory=list)

    @property
    def nhan(self):
        return NHAN[self.xu_huong]

    @property
    def chinh(self) -> KetQuaKhung:
        """Khung giao dịch chính (dùng cho điểm vào / TP / SL)."""
        for kq in self.khung:
            if kq.khung == ("D" if self.loai != "fx" else "4H"):
                return kq
        return self.khung[-1]


TRONG_SO_KHUNG = {"M": 1.0, "W": 1.5, "D": 2.0, "4H": 2.0, "1H": 1.5, "15m": 1.0}


def tong_hop(ma: str, loai: str, ds: list) -> KetQua:
    thieu = [x.khung for x in ds if not x.votes]
    ds = [x for x in ds if x.votes]
    if not ds:
        return KetQua(ma, loai, [], 0.0, 0, "Không có dữ liệu", ["Không tải được dữ liệu."])
    w = [TRONG_SO_KHUNG.get(x.khung, 1.0) for x in ds]
    diem = sum(x.diem * wi for x, wi in zip(ds, w)) / sum(w)
    xh = 1 if diem > NGUONG else (-1 if diem < -NGUONG else 0)
    cung = sum(1 for x in ds if x.xu_huong == xh)
    ghi = [f"Khung {', '.join(thieu)} chưa đủ dữ liệu nên bỏ qua."] if thieu else []
    lon, nho = ds[0], ds[-1]
    if lon.xu_huong and nho.xu_huong and lon.xu_huong != nho.xu_huong:
        ghi.append(f"Khung lớn ({lon.khung}) {lon.nhan.lower()} nhưng khung nhỏ ({nho.khung}) "
                   f"{nho.nhan.lower()} → có thể chỉ là nhịp hồi.")
    return KetQua(ma, loai, ds, round(diem, 1), xh, f"{cung}/{len(ds)} khung", ghi)


def kiem_tra_qua_khu(df: pd.DataFrame, khung: str, so_nen: int = 120, toi: int = 5) -> dict:
    """Thử lại tín hiệu trên dữ liệu quá khứ: tại mỗi nến, chỉ dùng dữ liệu đến nến đó,
    rồi so với giá đóng cửa sau `toi` nến. Trả về tỉ lệ đúng của các tín hiệu Tăng/Giảm."""
    dung = sai = 0
    start = max(60, len(df) - so_nen - toi)
    for i in range(start, len(df) - toi):
        kq = phan_tich_khung(df.iloc[:i + 1], khung)
        if not kq.xu_huong:
            continue
        thay_doi = df["close"].iloc[i + toi] - df["close"].iloc[i]
        if _sign(thay_doi) == kq.xu_huong:
            dung += 1
        else:
            sai += 1
    tong = dung + sai
    return {"tin_hieu": tong, "dung": dung, "ti_le": (dung / tong) if tong else None, "toi": toi}
