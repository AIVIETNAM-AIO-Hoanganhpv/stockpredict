"""Điểm mua đẹp, khuyến nghị mua, tín hiệu bán ở đỉnh, tính lãi/lỗ theo số vốn và đánh giá danh mục.

Vùng mua đẹp = nơi nhiều mức hỗ trợ trùng nhau (hợp lưu) ngay dưới giá hiện tại:
  Fibonacci hồi 0.5 / 0.618 / 0.705 (OTE) / 0.786 của nhịp tăng gần nhất,
  Order Block tăng, Fair Value Gap tăng (SMC), MA20 / MA50, đáy gần nhất.
Chốt lời theo Fibonacci mở rộng ("hồi ít thì lên nhiều"), cắt lỗ dưới vùng mua.
"""
import math
import re
from dataclasses import dataclass, field

import pandas as pd

from . import chi_bao
from .phan_tich import KetQua, KetQuaKhung

# Phí giao dịch mặc định (chứng khoán VN): mua 0,15%; bán 0,15% + thuế 0,1%
PHI_MUA = 0.0015
PHI_BAN = 0.0015
THUE_BAN = 0.001

MUC = ["Không mua", "Theo dõi", "Gần đủ điều kiện", "Mua"]   # hạng 0..3
MAU_MUC = {"Mua": "#15803d", "Gần đủ điều kiện": "#d97706",
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
    thoi_gian: object = None    # ThoiGian – ngày chốt lời dự kiến

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
def loai_gia(ma: str, loai: str = "vn", san: str | None = None) -> str:
    """Kiểu bước giá: 'vn' (HOSE: 10/50/100 đ), 'vn_100' (HNX, UPCoM: 100 đ),
    'chi_so' (VNINDEX…: không làm tròn), còn lại (forex, quốc tế): không làm tròn."""
    from .du_lieu import CHI_SO_VN, san_cua
    if loai != "vn":
        return loai
    if ma.upper() in CHI_SO_VN:
        return "chi_so"
    san = san if san is not None else san_cua(ma)
    return "vn_100" if san in ("HNX", "UPCOM") else "vn"


def buoc_gia(p: float, loai: str = "vn") -> float:
    if p <= 0:
        return 0.0
    if loai == "vn_100":
        return 100.0
    if loai != "vn":
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
# Tham số đã kiểm định (backtest 2006–2026, 891 mã, chỉnh trên 2006–2019, kiểm tra trên 2020–2026):
#   trọng số "động lượng", điểm ≥ 50 và khung lớn đang tăng, mua ngay phiên sau, cắt lỗ dưới vùng hỗ trợ 0,5 ATR
#   (không có vùng: giá − 1 ATR), chốt lời = 3 × rủi ro, giữ tối đa 60 phiên.
#   Kiểm tra 2020–2026: 2.245 lệnh, lãi TB +3,6%/lệnh (mua ngẫu nhiên giữ 60 phiên: +2,3%), thắng 44%.
TRONG_SO = {"MACD": 2.5, "Stochastic": 1.5, "MFI": 1.5, "Heikin Ashi": 1, "ADX": 1.5,
            "Đỉnh/đáy": 1, "SMC cấu trúc": 1}
NGUONG_MUA = 50.0
NGUONG_GAN = 35.0
SL_ATR = 0.5
TP_R = 3.0
GIU_TOI_DA = 60


def diem_trong_so(kqk: KetQuaKhung, df: pd.DataFrame | None = None, trong_so: dict | None = None) -> float:
    """Điểm khung tính lại với bộ trọng số đã kiểm định (chỉ các chỉ báo có phiếu)."""
    trong_so = TRONG_SO if trong_so is None else trong_so
    tu = mau = 0.0
    for v in kqk.votes:
        w = trong_so.get(v.ten, 0.0) if v.trong_so > 0 else 0.0
        tu += v.gia_tri * w
        mau += w
    d = 100 * tu / mau if mau else 0.0
    if df is not None and len(df) > 30:
        adx = float(chi_bao.adx(df)["adx"].iloc[-1])
        if adx < 20:
            d *= 0.7
    return d


def khuyen_nghi(kq: KetQua, tam: str = "D", loai: str | None = None, san: str | None = None) -> KhuyenNghi:
    """Khuyến nghị MUA cho khung `tam` theo bộ tham số đã kiểm định (xem TRONG_SO, NGUONG_MUA…).
    D: ngắn hạn (đã kiểm định) · W: trung hạn (cùng quy tắc, CHƯA kiểm định riêng).
    `loai`/`san` quyết định bước giá; để trống thì tự suy ra từ mã."""
    loai = loai_gia(kq.ma, loai or kq.loai, san)
    kqk = next((k for k in kq.khung if k.khung == tam), None)
    df = kq.frames.get(tam)
    if kqk is None or df is None or len(df) < 40:
        return KhuyenNghi(kq.ma, tam, "Theo dõi", kq.khung[-1].gia if kq.khung else float("nan"),
                          kq.diem, ly_do=["Chưa đủ dữ liệu cho khung này."])
    lon = next((k for k in kq.khung if k.khung == KHUNG_LON.get(tam)), None)
    gia = kqk.gia
    atr = float(chi_bao.atr(df).iloc[-1])
    dd = diem_trong_so(kqk, df)
    dw = diem_trong_so(lon, df) if lon and lon.votes else 0.0     # giống lúc kiểm định: phạt ADX theo khung giữ lệnh
    if KHUNG_LON.get(tam) is None:            # khung tháng: không có khung lớn hơn → dùng chính khung tháng
        diem = dd
        lon_tang = kqk.xu_huong == 1
    else:
        diem = (2 * dd + dw) / 3
        lon_tang = bool(lon and lon.xu_huong == 1)
    ly_do = [f"Điểm động lượng khung {tam}: {dd:+.0f}" + (f", khung {lon.khung}: {dw:+.0f}" if lon else "")
             + f" → tổng {diem:+.0f}"]
    kn = KhuyenNghi(kq.ma, tam, "Theo dõi", gia, round(diem, 1), ly_do=ly_do)

    vung = tim_vung_mua(df, kqk)
    if vung:
        kn.vung = vung
        ly_do.append("Vùng hỗ trợ: " + ", ".join(vung.ly_do))
    # Kế hoạch theo tham số đã kiểm định: mua ngay, cắt lỗ dưới vùng hỗ trợ, chốt lời 3R
    kn.gia_mua = gia
    sl = (vung.thap - SL_ATR * atr) if vung and vung.thap - SL_ATR * atr < gia else gia - atr
    kn.cat_lo = sl
    kn.chot_loi1 = gia + TP_R * (gia - sl)
    kn.chot_loi2 = None
    for f in ("gia_mua", "cat_lo"):
        setattr(kn, f, lam_tron(getattr(kn, f), loai, xuong=True))
    kn.chot_loi1 = lam_tron(kn.chot_loi1, loai, xuong=False)
    if kn.vung:
        kn.vung = VungMua(lam_tron(kn.vung.thap, loai), lam_tron(kn.vung.cao, loai, xuong=False), kn.vung.ly_do)

    if diem < -20 or kqk.xu_huong == -1:
        kn.muc = "Không mua"
        ly_do.append("Xu hướng giảm – đứng ngoài.")
    elif diem >= NGUONG_MUA and dd > 0 and lon_tang:
        kn.muc = "Mua"
        ly_do.append(f"Đủ điều kiện: điểm ≥ {NGUONG_MUA:.0f} và khung {lon.khung} đang tăng. Mua phiên sau, "
                     f"cắt lỗ {kn.cat_lo:,.0f}, chốt lời {kn.chot_loi1:,.0f} (3 × rủi ro), giữ tối đa {GIU_TOI_DA} phiên.")
    elif diem >= NGUONG_GAN and dd > 0:
        kn.muc = "Gần đủ điều kiện"
        thieu = []
        if diem < NGUONG_MUA:
            thieu.append(f"điểm {diem:.0f} < {NGUONG_MUA:.0f}")
        if not lon_tang:
            thieu.append(f"khung {lon.khung if lon else 'lớn'} chưa tăng")
        ly_do.append("Còn thiếu: " + ", ".join(thieu) + ".")
    else:
        kn.muc = "Theo dõi"
        ly_do.append("Động lượng chưa đủ mạnh.")

    if kn.muc in ("Mua", "Gần đủ điều kiện") and kn.chot_loi1:
        try:
            kn.thoi_gian = du_kien_thoi_gian(df, kqk, kn.gia_mua, kn.chot_loi1)
        except Exception:
            kn.thoi_gian = None
    dfd = kq.frames.get("D", df)
    kn.gtgd = float((dfd["close"] * dfd["volume"]).iloc[-20:].mean()) if len(dfd) else None
    return kn


# ------------------------------------------------------------------------- timing: ngày chốt lời dự kiến
PHIEN_MOI_NEN = {"D": 1, "W": 5, "M": 21, "4H": 0.5, "1H": 0.2, "15m": 0.05}
# Hiệu chỉnh từ backtest 19/11/2026 (170 lệnh chạm chốt lời, 267 mã): thực tế / dự kiến theo tốc độ
# = 1.45 (phân vị 25%) · 2.68 (trung vị) · 4.61 (75%). Kiểm tra trên nửa dữ liệu không dùng để hiệu chỉnh:
# 53% lệnh nằm trong khoảng sớm–muộn, sai số trung vị 7,5 phiên. Fibonacci thời gian lệch xa hơn (~6 lần).
HIEU_CHINH_TG = (1.45, 2.68, 4.61)


def _nhip_tang_cu(kqk: KetQuaKhung, so: int = 12) -> list:
    """Các nhịp tăng đáy → đỉnh gần đây: (vị trí đáy, vị trí đỉnh, giá đáy, giá đỉnh)."""
    st = kqk.cau_truc
    if not st:
        return []
    sw = sorted(st.swings, key=lambda x: x.i)
    out = []
    for a, b in zip(sw, sw[1:]):
        if a.kind == "L" and b.kind == "H" and b.price > a.price and b.i > a.i:
            out.append((a.i, b.i, a.price, b.price))
    return out[-so:]


@dataclass
class ThoiGian:
    som: float | None = None          # số nến (khung đang xét)
    thuong: float | None = None
    muon: float | None = None
    fibo: tuple | None = None         # (0.618, 1, 1.618) × độ dài nhịp trước, tính từ đáy hồi – số nến từ hôm nay
    khung: str = "D"
    tu_ngay: object = None

    def phien(self, x):
        return None if x is None else max(1, round(x * PHIEN_MOI_NEN.get(self.khung, 1)))

    def ngay(self, x):
        """Ngày giao dịch dự kiến (bỏ thứ 7, CN; chưa trừ ngày lễ)."""
        n = self.phien(x)
        if n is None or self.tu_ngay is None:
            return None
        return pd.bdate_range(pd.Timestamp(self.tu_ngay) + pd.Timedelta(days=1), periods=n)[-1]

    def mo_ta(self) -> str:
        if self.thuong is None:
            return ""
        f = lambda d: d.strftime("%d/%m/%Y") if d is not None else "?"  # noqa: E731
        return (f"~{self.phien(self.thuong)} phiên ({f(self.ngay(self.som))} – {f(self.ngay(self.muon))}, "
                f"thường {f(self.ngay(self.thuong))})")


def du_kien_thoi_gian(df: pd.DataFrame, kqk: KetQuaKhung, gia_vao: float, chot_loi: float) -> ThoiGian:
    """Dự kiến bao lâu chạm chốt lời.
    • Tốc độ: mỗi nhịp tăng cũ đi được bao nhiêu ATR mỗi nến → số nến cần để đi (chốt lời − giá vào),
      nhân hệ số hiệu chỉnh từ backtest (HIEU_CHINH_TG) → sớm / thường / muộn.
    • Fibonacci thời gian (LEVEL 1): đáy hồi + 0.618 / 1 / 1.618 × độ dài nhịp tăng trước."""
    tg = ThoiGian(khung=kqk.khung, tu_ngay=df.index[-1])
    if not gia_vao or not chot_loi or chot_loi <= gia_vao or len(df) < 40:
        return tg
    atr = chi_bao.atr(df).to_numpy()
    nhip = _nhip_tang_cu(kqk)
    toc = []
    for i0, i1, p0, p1 in nhip:
        a = atr[i1] if i1 < len(atr) and atr[i1] > 0 else None
        if a:
            toc.append((p1 - p0) / a / (i1 - i0))
    a_now = atr[-1]
    if toc and a_now > 0:
        can = (chot_loi - gia_vao) / a_now
        v = float(pd.Series(toc).median())
        if v > 0:
            co_so = can / v                      # số nến nếu đi nhanh như nhịp cũ (thường quá lạc quan)
            tg.som, tg.thuong, tg.muon = (min(250, max(1, co_so * h)) for h in HIEU_CHINH_TG)
    if nhip:
        i0, i1, _, _ = nhip[-1]
        T = i1 - i0
        sau_dinh = df["low"].iloc[i1 + 1:]
        goc = int(sau_dinh.values.argmin()) + i1 + 1 if len(sau_dinh) else i1   # đáy hồi sau đỉnh
        hien_tai = len(df) - 1
        moc = [goc + T * r - hien_tai for r in (0.618, 1.0, 1.618)]
        if moc[-1] <= 0:                         # các mốc đã qua → đếm lại từ hôm nay
            moc = [T * r for r in (0.618, 1.0, 1.618)]
        tg.fibo = tuple(max(1, x) for x in moc)
    return tg


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


def tin_hieu_dinh(kq: KetQua, tam: str = "D", loai: str | None = None,
                  nguong: int = NGUONG_DINH, san: str | None = None) -> TinHieuDinh:
    """Đếm dấu hiệu đỉnh trên khung `tam`. ≥ nguong dấu hiệu → Chốt lời dần; ≥ nguong+2 hoặc có
    CHoCH giảm → Bán mạnh; nguong-1 → Theo dõi đỉnh."""
    loai = loai_gia(kq.ma, loai or kq.loai, san)
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
                "gia_ban": None, "lai_neu_ban": None, "vi_sao": ""}
    gia = kq.khung[-1].gia
    tien_von = gia_von * so_luong * (1 + PHI_MUA)
    lai = gia * so_luong * (1 - phi_ban - thue) - tien_von
    pct = lai / tien_von if tien_von else 0.0
    kqk = kq.chinh
    df = kq.frames.get(kqk.khung)
    atr = float(chi_bao.atr(df).iloc[-1]) if df is not None else 0.0
    # Cắt lỗ động: dưới đáy gần nhất (nâng dần theo giá)
    ls = [s.price for s in (kqk.cau_truc.swings if kqk.cau_truc else []) if s.kind == "L"]
    cat_lo = (ls[-1] - 0.3 * atr) if ls else None      # đáy gần nhất – giá thủng xuống là tín hiệu bán
    if pct < -0.07 and kq.xu_huong <= 0:
        goi_y, vi_sao = "Cắt lỗ", f"Đang lỗ {pct:.1%} (quá 7%) và xu hướng không còn tăng – giữ tiếp dễ lỗ sâu hơn."
    elif cat_lo and gia < cat_lo:
        goi_y, vi_sao = "Bán – thủng hỗ trợ", f"Giá {gia:,.0f} đã thủng đáy gần nhất ({cat_lo:,.0f}) – cấu trúc tăng bị phá."
    elif dinh and dinh.muc == "Bán mạnh":
        goi_y, vi_sao = "Bán ở đỉnh", f"Có {dinh.so_dau_hieu} dấu hiệu đỉnh (độ tin cậy thấp theo kiểm định)."
    elif kq.xu_huong == -1:
        goi_y = "Chốt lời / hạ tỷ trọng" if pct > 0 else "Cân nhắc bán"
        vi_sao = "Xu hướng chung của mã đã chuyển sang giảm."
    elif dinh and dinh.muc == "Chốt lời dần" and pct > 0:
        goi_y, vi_sao = "Chốt lời một phần (tín hiệu đỉnh)", f"Đang lãi {pct:.1%} và xuất hiện {dinh.so_dau_hieu} dấu hiệu đỉnh."
    elif kn and kn.chot_loi1 and gia >= kn.chot_loi1 * 0.99 and pct > 0:
        goi_y, vi_sao = "Chốt lời một phần", f"Giá đã tới mức chốt lời {kn.chot_loi1:,.0f}."
    elif kq.xu_huong == 1:
        goi_y, vi_sao = "Giữ", "Xu hướng vẫn tăng, giá còn trên đáy gần nhất – giữ và dời cắt lỗ theo đáy mới."
    else:
        goi_y, vi_sao = "Theo dõi", "Xu hướng đi ngang – giữ nhưng bán nếu thủng mức cắt lỗ."
    gia_ban = dinh.gia_ban if dinh and dinh.gia_ban else None
    lai_neu_ban = (gia_ban * so_luong * (1 - phi_ban - thue) - tien_von) if gia_ban else None
    return {"gia": gia, "lai": lai, "pct": pct, "goi_y": goi_y, "cat_lo": cat_lo,
            "gia_ban": gia_ban, "lai_neu_ban": lai_neu_ban, "vi_sao": vi_sao}



# ------------------------------------------------------------------------- giải thích dễ hiểu
# Kết quả kiểm định toàn thị trường 2020–2026 (xem ghi chú ở TRONG_SO)
KD_LENH, KD_THANG, KD_LAI_TB, KD_NGAU_NHIEN = 2245, 0.44, 0.036, 0.023
TEN_HO_TRO = {"MA50": "đường trung bình 50 phiên", "MA20": "đường trung bình 20 phiên", "MA200": "đường trung bình 200 phiên",
              "OB tăng": "vùng lệnh mua lớn trước đây (Order Block)", "FVG tăng": "khoảng trống giá chưa lấp (FVG)",
              "Đáy gần nhất": "đáy gần nhất", "Đáy trước": "đáy trước đó"}


def _ten_ho_tro(x: str) -> str:
    if x.startswith("Fibo "):
        try:
            return f"mức hồi Fibonacci {float(x.split()[1]):.1%}".replace(".0%", "%").replace(".", ",")
        except ValueError:
            return x
    return TEN_HO_TRO.get(x, x)


def _so_dep(text: str) -> str:
    """1.38e+05 → 138,000 trong câu giải thích."""
    return re.sub(r"\d+(?:\.\d+)?e[+-]\d+", lambda m: f"{float(m.group()):,.0f}".replace(",", "."), text)


def giai_thich(kq: KetQua, kn: KhuyenNghi, von: float | None = None, lo: int = 100) -> dict:
    """Kế hoạch rõ ràng cho 1 mã: điểm mua, cắt lỗ, chốt lời (giá, %, tiền), ngày dự kiến, lãi kỳ vọng và VÌ SAO.
    Mã chưa đủ điều kiện vẫn có kế hoạch nhưng ghi 'tham khảo – chưa vào' và điều kiện còn thiếu."""
    def _d(x):
        return f"{x:,.0f}".replace(",", ".")
    sl_atr = str(SL_ATR).replace(".", ",")
    tam = kn.tam
    lon_ten = KHUNG_LON.get(tam, "lớn")
    kqk = next((k for k in kq.khung if k.khung == tam), None)
    lon = next((k for k in kq.khung if k.khung == lon_ten), None)
    vao = kn.muc == "Mua"
    if vao:
        dieu_kien = f"Đã đủ điều kiện: điểm ≥ {NGUONG_MUA:.0f} và khung {lon_ten} đang tăng."
    else:
        thieu = []
        if kqk is not None and kqk.xu_huong == -1:
            thieu.append(f"khung {tam} hết giảm")
        if kn.diem < NGUONG_MUA:
            thieu.append(f"điểm lên ≥ {NGUONG_MUA:.0f} (đang {kn.diem:+.0f})")
        if not (lon and lon.xu_huong == 1):
            thieu.append(f"khung {lon_ten} chuyển sang tăng")
        if getattr(kn, "muc_goc", None):
            thieu.insert(0, "thị trường chung chuyển sang pha tốt (Tích luỹ/Tăng)")
        dieu_kien = "Chỉ vào khi: " + (", ".join(thieu) or "tín hiệu xác nhận") + "."
    kh = {"vao_lenh": vao, "trang_thai": "VÀO LỆNH" if vao else "THAM KHẢO – CHƯA VÀO", "dieu_kien": dieu_kien,
          "gia": kn.gia, "gia_mua": kn.gia_mua, "cat_lo": kn.cat_lo, "chot_loi": kn.chot_loi1,
          "lai_pct": kn.lai_pct, "lo_pct": kn.lo_pct, "rr": kn.rr, "giu_toi_da": GIU_TOI_DA,
          "vung": (kn.vung.thap, kn.vung.cao) if kn.vung else None}
    # Điểm mua
    if kn.vung:
        ho_tro = ", ".join(_ten_ho_tro(x) for x in kn.vung.ly_do[:4])
        kh["vi_sao_mua"] = (f"Mua giá mở cửa phiên sau (~{_d(kn.gia_mua)}) theo quy tắc đã kiểm định; giá đẹp hơn nếu "
                            f"hồi về vùng {_d(kn.vung.thap)}–{_d(kn.vung.cao)} – nơi hội tụ {ho_tro}.")
    else:
        kh["vi_sao_mua"] = f"Mua giá mở cửa phiên sau (~{_d(kn.gia_mua)}); chưa có vùng hỗ trợ rõ gần giá."
    # Cắt lỗ
    if kn.vung and kn.cat_lo and kn.cat_lo < kn.vung.thap:
        kh["vi_sao_cat_lo"] = (f"Đặt dưới vùng hỗ trợ ({_d(kn.vung.thap)}) thêm {sl_atr} lần biên dao động trung bình "
                               "(ATR): giá thủng mức này nghĩa là vùng hỗ trợ đã hỏng, nhận định sai.")
    else:
        kh["vi_sao_cat_lo"] = "Giá mua trừ 1 lần biên dao động trung bình (ATR) – không có vùng hỗ trợ gần để dựa vào."
    kh["vi_sao_chot_loi"] = (f"= giá mua + {TP_R:g} × khoảng cắt lỗ (lãi gấp {TP_R:g} lần mức chấp nhận lỗ) – mức cho kết quả "
                             f"tốt nhất khi kiểm định 2006–2026. Chưa chạm sau {GIU_TOI_DA} phiên thì bán.")
    # Ngày dự kiến
    tg = kn.thoi_gian
    if tg is None and kqk is not None and kn.chot_loi1 and kq.frames.get(tam) is not None:
        try:
            tg = du_kien_thoi_gian(kq.frames[tam], kqk, kn.gia_mua, kn.chot_loi1)
        except Exception:
            tg = None
    kh["ngay_du_kien"] = tg.ngay(tg.thuong) if tg is not None and tg.thuong is not None else None
    kh["ngay_som"] = tg.ngay(tg.som) if tg is not None and tg.som is not None else None
    kh["ngay_muon"] = tg.ngay(tg.muon) if tg is not None and tg.muon is not None else None
    # Tiền
    if von:
        t = ke_hoach_von(kn, von, lo)
        if t.get("tp1") and t["tp1"]["so_cp"] > 0:
            kh.update(so_cp=t["tp1"]["so_cp"], tien_mua=t["tp1"]["tien_mua"], tien_lai=t["tp1"]["lai"],
                      pct_lai_rong=t["tp1"]["pct"], tien_lo=t["sl"]["lai"], pct_lo_rong=t["sl"]["pct"],
                      tien_ky_vong=t["tp1"]["tien_mua"] * KD_LAI_TB)
    kh["ky_vong_pct"] = KD_LAI_TB
    kh["ky_vong"] = (f"Theo kiểm định 2020–2026 ({KD_LENH:,} lệnh Mua): {KD_THANG:.0%} số lệnh có lãi, trung bình "
                     f"{KD_LAI_TB:+.1%}/lệnh; mua ngẫu nhiên giữ 60 phiên được {KD_NGAU_NHIEN:+.1%}. Một nghiên cứu khác "
                     "(so từng 20 phiên) cho thấy tín hiệu Mua chưa hơn ngẫu nhiên → lãi kỳ vọng KHÔNG chắc chắn.")
    # Vì sao (các chỉ báo đang ủng hộ / phản đối, theo trọng số đã kiểm định)
    ung_ho, phan_doi = [], []
    for k, nhan in ((kqk, f"khung {tam}"), (lon, f"khung {lon_ten}")):
        if k is None:
            continue
        for v in k.votes:
            w = TRONG_SO.get(v.ten, 0)
            if not w or not v.gia_tri:
                continue
            dong = (abs(v.gia_tri) * w, f"{v.ten} ({nhan}): {_so_dep(v.ly_do)}")
            (ung_ho if v.gia_tri > 0 else phan_doi).append(dong)
    ung_ho.sort(reverse=True)
    phan_doi.sort(reverse=True)
    xh = {1: "tăng", -1: "giảm", 0: "đi ngang"}
    kh["vi_sao"] = ([f"Xu hướng: khung {tam} {xh[kqk.xu_huong] if kqk else '?'}, khung {lon_ten} "
                     f"{xh[lon.xu_huong] if lon else '?'} · điểm tổng {kn.diem:+.0f}/100 (cần ≥ {NGUONG_MUA:.0f} để mua)."]
                   + ["✔ " + x for _, x in ung_ho[:4]] + ["✖ " + x for _, x in phan_doi[:3]])
    # Chốt lời theo Fibonacci của sóng tăng gần nhất trên khung lệnh (tài liệu: "hồi ít thì lên nhiều")
    kh["fibo"] = None
    try:
        from . import fibo as F
        if kq.frames.get("D") is not None and kn.gia_mua:
            fb = None
            if tam in ("W", "M"):
                # Trung/dài hạn: Fibo 1,0 của CẢ sóng tháng và sóng tuần (đỉnh đã xác nhận, hồi ≥ 23,6%) đều phải ≥ 10%;
                # giá phải hồi về vùng hỗ trợ (≤ C + 50% đoạn C→B của sóng tuần). Mục tiêu hiển thị = mức thấp hơn.
                fm = F.muc_tieu_song(kq.frames["D"], "M", kn.gia_mua, ti_le_co_dinh=LAI_FIBO_TL, chat=True)
                fw = F.muc_tieu_song(kq.frames["D"], "W", kn.gia_mua, ti_le_co_dinh=LAI_FIBO_TL, chat=True)
                co = [x for x in (fm, fw) if x]
                if co:
                    fb = dict(min(co, key=lambda x: x["chot_loi"]))
                    fb["du_hai_song"] = bool(fm and fw)
                    fb["lai_thang"] = fm["lai_pct"] if fm else None
                    fb["lai_tuan"] = fw["lai_pct"] if fw else None
                    fb["vung_ho_tro"] = (fw["C"] + 0.5 * (fw["B"] - fw["C"])) if fw else None
                    fb["da_hoi"] = bool(fw) and kn.gia_mua <= fb["vung_ho_tro"]
            else:
                fb = F.muc_tieu_song(kq.frames["D"], tam, kn.gia_mua)
            if fb:
                fb["chot_loi"] = lam_tron(fb["chot_loi"], loai_gia(kq.ma, kq.loai), xuong=False)
                fb["lai_pct"] = fb["chot_loi"] / kn.gia_mua - 1
                fb["du_lai"] = fb["lai_pct"] >= LAI_TOI_THIEU and fb.get("du_hai_song", True)
                ten_song = {"M": "tháng", "W": "tuần", "D": "ngày"}[fb["khung"]]
                tl = str(fb["ti_le"]).replace(".", ",")
                fb["vi_sao"] = (f"Sóng {ten_song}: đáy A {_d(fb['A'])} ({fb['ngay_A']:%m/%Y}) → đỉnh B {_d(fb['B'])} ({fb['ngay_B']:%m/%Y}), "
                                f"hồi về C {_d(fb['C'])} = {fb['do_sau']:.0%} biên độ → mục tiêu C + {tl} × (B − A).")
                kh["fibo"] = fb
    except Exception:
        kh["fibo"] = None
    # Trung/dài hạn: ADX(14) khung TUẦN (tuần đã xong) ≥ 25 và +DI > −DI mới vào; giữ tối đa 9 tháng / 10 năm; cắt lỗ ≤ 15%
    kh["adx_tuan"], kh["tam"] = None, tam
    if tam in ("W", "M") and kq.frames.get("D") is not None:
        try:
            from . import level1
            a = chi_bao.adx(level1.nen_khung(kq.frames["D"], "W")).dropna()
            if len(a):
                v, p_, m_ = (float(a[c].iloc[-1]) for c in ("adx", "pdi", "mdi"))
                kh["adx_tuan"] = {"adx": v, "pdi": p_, "mdi": m_, "dat": v >= ADX_TOI_THIEU and p_ > m_}
        except Exception:
            kh["adx_tuan"], kh["tam"] = None, tam
    kh["tom_tat"] = (f"Mua ~{_d(kn.gia_mua)}, cắt lỗ {_d(kn.cat_lo)} ({kn.lo_pct:+.1%}), chốt lời {_d(kn.chot_loi1)} "
                     f"({kn.lai_pct:+.1%})" if kn.gia_mua and kn.cat_lo and kn.chot_loi1 and kn.lo_pct is not None else "")
    return kh


LAI_FIBO_TL = 1.0       # cổ phiếu dài hạn: chỉ dùng mức Fibo 1,0 (không 1,618)
LAI_TOI_THIEU = 0.10    # lãi dự kiến tới mức 1,0 dưới 10% → không vào lệnh
ADX_TOI_THIEU = 25      # ADX tuần tối thiểu (kèm +DI > −DI)
CAT_LO_TOI_DA = 0.15    # cắt lỗ không xa quá 15%
GIU_TOI_DA_DAI_HAN = {"W": "9 tháng", "M": "10 năm"}


def ap_pha(kn: KhuyenNghi, ck: dict | None) -> KhuyenNghi:
    """Bộ lọc pha thị trường (đã kiểm định, xem chu_ky.py): thị trường không ở pha tốt → mã đang 'Mua' / 'Gần đủ
    điều kiện' chuyển sang 'Theo dõi' (chờ). Giữ nguyên giá mua/cắt lỗ/chốt lời để tham khảo."""
    if not ck or ck.get("nen_cam_co_phieu", True) or kn.muc not in ("Mua", "Gần đủ điều kiện"):
        return kn
    kn.muc_goc = kn.muc
    kn.muc = "Theo dõi"
    kn.ly_do.append(f"Thị trường chung đang pha {ck.get('pha', '?').upper()} → CHỜ, chưa mua mới "
                    f"(tín hiệu mã: {kn.muc_goc}).")
    return kn
