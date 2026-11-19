"""Điểm mua đẹp, khuyến nghị mua, tín hiệu bán ở đỉnh, tính lãi/lỗ theo số vốn và đánh giá danh mục.

Vùng mua đẹp = nơi nhiều mức hỗ trợ trùng nhau (hợp lưu) ngay dưới giá hiện tại:
  Fibonacci hồi 0.5 / 0.618 / 0.705 (OTE) / 0.786 của nhịp tăng gần nhất,
  Order Block tăng, Fair Value Gap tăng (SMC), MA20 / MA50, đáy gần nhất.
Chốt lời theo Fibonacci mở rộng ("hồi ít thì lên nhiều"), cắt lỗ dưới vùng mua.
"""
import math
from dataclasses import dataclass, field

import pandas as pd

from . import chi_bao, fibo
from .phan_tich import KetQua, KetQuaKhung

# Phí giao dịch mặc định (chứng khoán VN): mua 0,15%; bán 0,15% + thuế 0,1%
PHI_MUA = 0.0015
PHI_BAN = 0.0015
THUE_BAN = 0.001

MUC = ["Không mua", "Theo dõi", "Chờ về vùng mua", "Mua", "Mua mạnh"]   # hạng 0..4
MAU_MUC = {"Mua mạnh": "#15803d", "Mua": "#16a34a", "Chờ về vùng mua": "#d97706",
           "Theo dõi": "#64748b", "Không mua": "#dc2626"}
KHUNG_LON = {"D": "W", "W": "M", "4H": "D", "1H": "4H"}

MUC_BAN = ["Chưa có đỉnh", "Theo dõi đỉnh", "Chốt lời dần", "Bán mạnh"]   # hạng 0..3
MAU_BAN = {"Bán mạnh": "#b91c1c", "Chốt lời dần": "#dc2626", "Theo dõi đỉnh": "#d97706",
           "Chưa có đỉnh": "#64748b"}
NGUONG_DINH = 3          # số dấu hiệu tối thiểu để báo chốt lời (mức "Cân bằng")


@dataclass
class VungMua:
    thap: float
    cao: float
    ly_do: list = field(default_factory=list)


@dataclass
class KhuyenNghi:
    ma: str
    tam: str                    # khung tính kế hoạch: "D" ngắn hạn, "W" trung hạn
    muc: str
    gia: float
    diem: float
    vung: VungMua | None = None
    gia_mua: float | None = None
    cat_lo: float | None = None
    chot_loi1: float | None = None
    chot_loi2: float | None = None
    ly_do: list = field(default_factory=list)
    gtgd: float | None = None   # giá trị giao dịch bình quân 20 phiên
    san: str = ""

    @property
    def hang(self) -> int:
        return MUC.index(self.muc)

    @property
    def rr(self) -> float | None:
        """Tỷ lệ lãi/lỗ kỳ vọng (Reward:Risk)."""
        if not (self.gia_mua and self.cat_lo and self.chot_loi1) or self.gia_mua <= self.cat_lo:
            return None
        return (self.chot_loi1 - self.gia_mua) / (self.gia_mua - self.cat_lo)

    @property
    def lai_pct(self):
        return (self.chot_loi1 / self.gia_mua - 1) if self.gia_mua and self.chot_loi1 else None

    @property
    def lo_pct(self):
        return (self.cat_lo / self.gia_mua - 1) if self.gia_mua and self.cat_lo else None

    @property
    def cach_vung_pct(self):
        """Giá hiện tại cao hơn giá mua đề xuất bao nhiêu %."""
        return (self.gia / self.gia_mua - 1) if self.gia_mua else None


# ------------------------------------------------------------------------- làm tròn giá
def buoc_gia(p: float, loai: str = "vn") -> float:
    if loai != "vn" or p <= 0:
        return 0.0
    return 10.0 if p < 10_000 else (50.0 if p < 50_000 else 100.0)


def lam_tron(p, loai="vn", xuong=True):
    if p is None or not math.isfinite(p):
        return p
    b = buoc_gia(p, loai)
    if not b:
        return p
    return (math.floor if xuong else math.ceil)(p / b) * b


# ------------------------------------------------------------------------- vùng mua
def _nhip_tang(kqk: KetQuaKhung):
    """Nhịp tăng gần nhất: (đáy, đỉnh)."""
    st = kqk.cau_truc
    if not st:
        return None
    hs = [s for s in st.swings if s.kind == "H"]
    ls = [s for s in st.swings if s.kind == "L"]
    if not hs:
        return None
    h = hs[-1]
    truoc = [s for s in ls if s.i < h.i]
    if not truoc:
        return None
    lo = min(truoc[-3:], key=lambda s: s.price)       # đáy thấp nhất trong 3 đáy trước đỉnh
    return (lo.price, h.price) if h.price > lo.price else None


def tim_vung_mua(df: pd.DataFrame, kqk: KetQuaKhung) -> VungMua | None:
    gia = float(df["close"].iloc[-1])
    atr = float(chi_bao.atr(df).iloc[-1])
    if not math.isfinite(atr) or atr <= 0:
        return None
    ung_vien = []                                   # (giá, lý do)
    nhip = _nhip_tang(kqk)
    if nhip:
        lo, hi = nhip
        for r in (0.5, 0.618, 0.705, 0.786):
            ung_vien.append((hi - (hi - lo) * r, f"Fibo {r:g}"))
    st = kqk.cau_truc
    if st:
        for z in st.order_blocks + st.fvgs:
            if z.side > 0:
                ung_vien.append(((z.top + z.bottom) / 2, f"{z.kind} tăng"))
        ls = [s.price for s in st.swings if s.kind == "L" and s.price < gia]
        if ls:
            ung_vien.append((ls[-1], "Đáy gần nhất"))
    for n in (20, 50):
        ma = chi_bao.sma(df["close"], n).iloc[-1]
        if pd.notna(ma):
            ung_vien.append((float(ma), f"MA{n}"))

    # chỉ xét vùng dưới giá (cho phép cao hơn giá 0,3 ATR) và không quá xa (6 ATR)
    ung_vien = [(p, t) for p, t in ung_vien if gia - 6 * atr <= p <= gia + 0.3 * atr and p > 0]
    if not ung_vien:
        return None
    tot, best = None, None
    for p, _ in ung_vien:
        cum = [(q, t) for q, t in ung_vien if abs(q - p) <= 0.6 * atr]
        loai_khac = len({t.split()[0] for _, t in cum})
        diem = loai_khac + 0.3 * len(cum) - 0.15 * (gia - p) / atr     # hợp lưu nhiều, gần giá
        if tot is None or diem > tot:
            tot, best = diem, cum
    thap = min(q for q, _ in best) - 0.15 * atr
    cao = max(q for q, _ in best) + 0.15 * atr
    return VungMua(thap, cao, sorted({t for _, t in best}))


# ------------------------------------------------------------------------- khuyến nghị
def khuyen_nghi(kq: KetQua, tam: str = "D", loai: str = "vn") -> KhuyenNghi:
    """Khuyến nghị MUA cho khung `tam` (D: ngắn hạn 1–3 tháng, W: trung hạn 3–9 tháng)."""
    kqk = next((k for k in kq.khung if k.khung == tam), None)
    df = kq.frames.get(tam)
    if kqk is None or df is None or len(df) < 40:
        return KhuyenNghi(kq.ma, tam, "Theo dõi", kq.khung[-1].gia if kq.khung else float("nan"),
                          kq.diem, ly_do=["Chưa đủ dữ liệu cho khung này."])
    lon = next((k for k in kq.khung if k.khung == KHUNG_LON.get(tam)), None)
    gia = kqk.gia
    atr = float(chi_bao.atr(df).iloc[-1])
    diem = (kqk.diem * 2 + (lon.diem if lon else kqk.diem)) / 3     # khung giữ lệnh + khung lớn
    ly_do = [f"Điểm khung {tam}: {kqk.diem:+.0f}" + (f", khung {lon.khung}: {lon.diem:+.0f}" if lon else "")]
    kn = KhuyenNghi(kq.ma, tam, "Theo dõi", gia, round(diem, 1), ly_do=ly_do)

    vung = tim_vung_mua(df, kqk)
    nhip = _nhip_tang(kqk)
    if vung:
        kn.vung = vung
        trong_vung = gia <= vung.cao + 0.1 * atr
        kn.gia_mua = gia if trong_vung else (vung.thap + vung.cao) / 2
        kn.cat_lo = vung.thap - 0.5 * atr
        if nhip and nhip[1] > nhip[0]:
            p = fibo.plan(nhip[1], nhip[0], min(vung.thap, kn.gia_mua), True)
            kn.chot_loi1, kn.chot_loi2 = p.tp1, p.tp2
        if not kn.chot_loi1 or kn.chot_loi1 <= kn.gia_mua * 1.01:
            kn.chot_loi1 = kn.gia_mua + 2 * (kn.gia_mua - kn.cat_lo)
        ly_do.append("Vùng mua hợp lưu: " + ", ".join(vung.ly_do))
    else:
        trong_vung = False
        ly_do.append("Không có vùng hỗ trợ rõ ràng gần giá.")

    stoch_k = float(chi_bao.stoch(df)["k"].iloc[-1])
    rr = kn.rr
    if diem < -20 or kqk.xu_huong == -1:
        kn.muc = "Không mua"
        ly_do.append("Xu hướng giảm – đứng ngoài, chờ tín hiệu đảo chiều (CHoCH tăng).")
    elif diem <= 20:
        kn.muc = "Theo dõi"
        ly_do.append("Xu hướng chưa rõ (đi ngang).")
    elif not vung:
        kn.muc = "Theo dõi"
    elif not trong_vung:
        kn.muc = "Chờ về vùng mua"
        ly_do.append(f"Giá đang cao hơn vùng mua {kn.cach_vung_pct:.1%} – đặt lệnh chờ, không mua đuổi.")
    elif rr is not None and rr >= 2 and diem >= 40 and (not lon or lon.xu_huong != -1) and stoch_k < 85:
        kn.muc = "Mua mạnh"
        ly_do.append(f"Giá trong vùng mua, xu hướng mạnh, lãi/lỗ kỳ vọng {rr:.1f} lần.")
    elif rr is not None and rr >= 1.5:
        kn.muc = "Mua"
        ly_do.append(f"Giá trong vùng mua, lãi/lỗ kỳ vọng {rr:.1f} lần.")
    else:
        kn.muc = "Theo dõi"
        ly_do.append("Giá trong vùng mua nhưng tỷ lệ lãi/lỗ chưa hấp dẫn (< 1,5).")
    if stoch_k >= 85 and kn.muc in ("Mua", "Mua mạnh"):
        kn.muc = "Chờ về vùng mua"
        ly_do.append(f"Stoch quá mua ({stoch_k:.0f}) – chờ nhịp chỉnh.")

    for f in ("gia_mua", "cat_lo"):
        setattr(kn, f, lam_tron(getattr(kn, f), loai, xuong=True))
    for f in ("chot_loi1", "chot_loi2"):
        setattr(kn, f, lam_tron(getattr(kn, f), loai, xuong=True))
    if kn.vung:
        kn.vung = VungMua(lam_tron(kn.vung.thap, loai), lam_tron(kn.vung.cao, loai, xuong=False),
                          kn.vung.ly_do)
    dfd = kq.frames.get("D", df)
    kn.gtgd = float((dfd["close"] * dfd["volume"]).iloc[-20:].mean()) if len(dfd) else None
    return kn


# ------------------------------------------------------------------------- tín hiệu đỉnh
@dataclass
class TinHieuDinh:
    ma: str
    tam: str
    muc: str
    gia: float
    dau_hieu: list = field(default_factory=list)
    vung_ban: tuple | None = None          # (thấp, cao)
    gia_ban: float | None = None
    gia_dinh: float | None = None          # đỉnh gần nhất (mất hiệu lực nếu giá đóng cửa vượt lên)

    @property
    def hang(self) -> int:
        return MUC_BAN.index(self.muc)

    @property
    def so_dau_hieu(self) -> int:
        return len(self.dau_hieu)


def _nen_dao_chieu(df, atr) -> str | None:
    o, h, l, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    for j in (-1, -2):
        than = abs(c[j] - o[j])
        rau_tren = h[j] - max(o[j], c[j])
        bien = h[j] - l[j]
        if bien > 0.5 * atr and rau_tren >= 2 * max(than, 1e-9) and rau_tren >= 0.5 * bien:
            return "Nến râu trên dài (nến búa ngược / sao băng)"
        if (c[j] < o[j] and c[j - 1] > o[j - 1] and o[j] >= c[j - 1] and c[j] <= o[j - 1]
                and than > 0.5 * atr):
            return "Nến nhấn chìm giảm"
        if (c[j] < o[j] and c[j - 1] > o[j - 1] and o[j] > h[j - 1] * 0.998
                and c[j] < (o[j - 1] + c[j - 1]) / 2 and than > 0.5 * atr):
            return "Mây đen che phủ (Dark Cloud Cover)"
    return None


def tin_hieu_dinh(kq: KetQua, tam: str = "D", loai: str = "vn",
                  nguong: int = NGUONG_DINH) -> TinHieuDinh:
    """Đếm dấu hiệu đỉnh trên khung `tam`. ≥ nguong dấu hiệu → Chốt lời dần; ≥ nguong+2 hoặc có
    CHoCH giảm → Bán mạnh; nguong-1 → Theo dõi đỉnh."""
    kqk = next((k for k in kq.khung if k.khung == tam), None)
    df = kq.frames.get(tam)
    if kqk is None or df is None or len(df) < 40 or not kqk.cau_truc:
        return TinHieuDinh(kq.ma, tam, "Chưa có đỉnh", kq.khung[-1].gia if kq.khung else float("nan"))
    gia = kqk.gia
    atr = float(chi_bao.atr(df).iloc[-1])
    st = kqk.cau_truc
    hs = [x for x in st.swings if x.kind == "H"]
    ls = [x for x in st.swings if x.kind == "L"]
    dh = []
    dinh_gan = float(df["high"].iloc[-60:].max())
    gan_dinh = gia >= dinh_gan * 0.92          # chỉ xét khi giá còn ở gần vùng đỉnh
    cao5 = float(df["high"].iloc[-5:].max())

    # 1. Chạm Fibonacci mở rộng 1.272 / 1.618 của nhịp tăng trước
    ext = None
    if len(hs) >= 1 and ls:
        h0 = hs[-1] if hs[-1].i < len(df) - 3 else (hs[-2] if len(hs) > 1 else None)
        if h0:
            truoc = [x for x in ls if x.i < h0.i]
            sau = [x for x in ls if x.i > h0.i]
            if truoc and sau and sau[-1].price > truoc[-1].price:
                bien = h0.price - truoc[-1].price
                ext = {r: sau[-1].price + bien * r for r in (1.0, 1.272, 1.618)}
                for r in (1.618, 1.272):
                    if cao5 >= ext[r] - 0.3 * atr:
                        dh.append(f"Chạm Fibonacci mở rộng {r:g} ({ext[r]:,.0f})")
                        break
    # 2. Stoch / MFI quá mua
    s = chi_bao.stoch(df)
    k_, d_ = float(s["k"].iloc[-1]), float(s["d"].iloc[-1])
    if s["k"].iloc[-3:].max() > 80 and (k_ < d_ or k_ > 90):
        dh.append(f"Stoch quá mua ({s['k'].iloc[-3:].max():.0f})" + (" và cắt xuống" if k_ < d_ else ""))
    mf = chi_bao.mfi(df)
    if mf.notna().iloc[-1] and mf.iloc[-3:].max() > 80:
        dh.append(f"MFI quá mua ({mf.iloc[-3:].max():.0f}) – dòng tiền vào quá nóng")
    # 3. Phân kỳ giảm MACD: đỉnh sau cao hơn nhưng MACD thấp hơn
    if len(hs) >= 2:
        m = chi_bao.macd(df)["macd"].to_numpy()
        a, b = hs[-2], hs[-1]
        if b.price > a.price and m[b.i] < m[a.i] and len(df) - 1 - b.i <= 15:
            dh.append("Phân kỳ giảm MACD (giá đỉnh cao hơn, MACD thấp hơn)")
    # 4. SMC: quét thanh khoản đỉnh, chạm vùng cung (OB/FVG giảm), CHoCH giảm
    if st.sweep == -1:
        dh.append("Quét thanh khoản đỉnh cũ rồi đóng cửa quay xuống")
    for z in st.order_blocks + st.fvgs:
        if z.side < 0 and z.bottom - 0.2 * atr <= cao5 and gia <= z.top + 0.2 * atr:
            dh.append(f"Chạm vùng cung {z.kind} giảm [{z.bottom:,.0f} – {z.top:,.0f}]")
            break
    choch = bool(st.events) and st.events[-1][1] == "CHoCH" and st.events[-1][2] < 0 \
        and len(df) - 1 - st.events[-1][0] <= 10
    if choch:
        dh.append("CHoCH giảm – cấu trúc tăng bị phá")
    # 5. Nến đảo chiều (LEVEL 1)
    nen = _nen_dao_chieu(df, atr)
    if nen and gan_dinh:
        dh.append(nen)
    # 6. Số nhịp (Nguyên lý II: thường đảo chiều ở nhịp 3, 4)
    from .cau_truc import count_legs
    legs = count_legs(st, 1) if st.trend == 1 else 0
    if legs >= 3:
        dh.append(f"Đã chạy {legs} nhịp tăng – hay đảo chiều ở nhịp 3–4")

    th = TinHieuDinh(kq.ma, tam, "Chưa có đỉnh", gia, dh, gia_dinh=float(hs[-1].price) if hs else None)
    n = len(dh)
    if not gan_dinh and not choch:
        th.muc = "Chưa có đỉnh"
        th.dau_hieu = dh + ["Giá đã cách xa đỉnh 60 phiên (> 8%) – không còn ở vùng đỉnh"]
    elif n >= nguong + 2 or (n >= nguong and choch):
        th.muc = "Bán mạnh"
    elif n >= nguong:
        th.muc = "Chốt lời dần"
    elif n == nguong - 1:
        th.muc = "Theo dõi đỉnh"

    # Vùng bán đẹp: hợp lưu kháng cự quanh/ trên giá
    ung = []
    if ext:
        ung += [(v, f"Fibo mở rộng {r:g}") for r, v in ext.items()]
    ung += [(x.price, "Đỉnh cũ") for x in hs[-4:]]
    ung += [((z.top + z.bottom) / 2, f"{z.kind} giảm") for z in st.order_blocks + st.fvgs if z.side < 0]
    ung = [(p, t) for p, t in ung if gia - 0.3 * atr <= p <= gia + 4 * atr]
    if ung:
        best = max(([(q, t) for q, t in ung if abs(q - p) <= 0.6 * atr] for p, _ in ung),
                   key=lambda c: (len({t.split()[0] for _, t in c}), -min(q for q, _ in c)))
        thap = min(q for q, _ in best) - 0.15 * atr
        cao = max(q for q, _ in best) + 0.15 * atr
        th.vung_ban = (lam_tron(thap, loai, xuong=False), lam_tron(cao, loai, xuong=False))
        th.gia_ban = lam_tron(gia if gia >= thap else (thap + cao) / 2, loai, xuong=False)
    elif th.hang >= 2:
        th.gia_ban = gia
    return th


# ------------------------------------------------------------------------- tính lãi
def tinh_lai(von: float, gia_mua: float, gia_ban: float, lo: int = 100,
             phi_mua: float = PHI_MUA, phi_ban: float = PHI_BAN, thue: float = THUE_BAN) -> dict:
    """Số cổ phiếu mua được (theo lô) và tiền/% lãi khi bán ở `gia_ban`, đã trừ phí và thuế."""
    if not gia_mua or gia_mua <= 0 or von <= 0:
        return {"so_cp": 0, "tien_mua": 0.0, "tien_ban": 0.0, "lai": 0.0, "pct": 0.0}
    so_cp = int(von // (gia_mua * (1 + phi_mua) * lo)) * lo
    tien_mua = so_cp * gia_mua * (1 + phi_mua)
    tien_ban = so_cp * gia_ban * (1 - phi_ban - thue)
    lai = tien_ban - tien_mua
    return {"so_cp": so_cp, "tien_mua": tien_mua, "tien_ban": tien_ban, "lai": lai,
            "pct": lai / tien_mua if tien_mua else 0.0}


def ke_hoach_von(kn: KhuyenNghi, von: float, lo: int = 100, **phi) -> dict:
    """Lãi khi chạm chốt lời 1, 2 và lỗ khi chạm cắt lỗ."""
    if not kn.gia_mua:
        return {}
    out = {"tp1": tinh_lai(von, kn.gia_mua, kn.chot_loi1, lo, **phi) if kn.chot_loi1 else None,
           "tp2": tinh_lai(von, kn.gia_mua, kn.chot_loi2, lo, **phi) if kn.chot_loi2 else None,
           "sl": tinh_lai(von, kn.gia_mua, kn.cat_lo, lo, **phi) if kn.cat_lo else None}
    return out


# ------------------------------------------------------------------------- danh mục
def danh_gia_vi_the(gia_von: float, so_luong: float, kq: KetQua, kn: KhuyenNghi | None,
                    phi_ban: float = PHI_BAN, thue: float = THUE_BAN, dinh: "TinHieuDinh | None" = None) -> dict:
    """Lãi/lỗ hiện tại của một vị thế và gợi ý Giữ / Chốt lời / Bán ở đỉnh / Cắt lỗ."""
    if not kq.khung:
        return {"gia": None, "lai": None, "pct": None, "goi_y": "Không có dữ liệu", "cat_lo": None,
                "gia_ban": None, "lai_neu_ban": None}
    gia = kq.khung[-1].gia
    tien_von = gia_von * so_luong * (1 + PHI_MUA)
    lai = gia * so_luong * (1 - phi_ban - thue) - tien_von
    pct = lai / tien_von if tien_von else 0.0
    kqk = kq.chinh
    df = kq.frames.get(kqk.khung)
    atr = float(chi_bao.atr(df).iloc[-1]) if df is not None else 0.0
    # Cắt lỗ động: dưới đáy gần nhất (nâng dần theo giá)
    ls = [s.price for s in (kqk.cau_truc.swings if kqk.cau_truc else []) if s.kind == "L" and s.price < gia]
    cat_lo = (ls[-1] - 0.3 * atr) if ls else None
    if pct < -0.07 and kq.xu_huong <= 0:
        goi_y = "Cắt lỗ"
    elif cat_lo and gia < cat_lo:
        goi_y = "Bán – thủng hỗ trợ"
    elif dinh and dinh.muc == "Bán mạnh":
        goi_y = "Bán ở đỉnh"
    elif kq.xu_huong == -1:
        goi_y = "Chốt lời / hạ tỷ trọng" if pct > 0 else "Cân nhắc bán"
    elif dinh and dinh.muc == "Chốt lời dần" and pct > 0:
        goi_y = "Chốt lời một phần (tín hiệu đỉnh)"
    elif kn and kn.chot_loi1 and gia >= kn.chot_loi1 * 0.99 and pct > 0:
        goi_y = "Chốt lời một phần"
    elif kq.xu_huong == 1:
        goi_y = "Giữ"
    else:
        goi_y = "Theo dõi"
    gia_ban = dinh.gia_ban if dinh and dinh.gia_ban else None
    lai_neu_ban = (gia_ban * so_luong * (1 - phi_ban - thue) - tien_von) if gia_ban else None
    return {"gia": gia, "lai": lai, "pct": pct, "goi_y": goi_y, "cat_lo": cat_lo,
            "gia_ban": gia_ban, "lai_neu_ban": lai_neu_ban}
