"""Kế hoạch giao dịch forex / vàng / bạc / dầu / crypto – khác cổ phiếu VN:

  • Có cả lệnh MUA (Buy) và BÁN (Sell) – theo xu hướng khung giao dịch (mặc định 4H), khung lớn hơn để lọc.
  • Khoảng cắt lỗ / chốt lời tính bằng pip (point), khối lượng tính bằng LOT theo % rủi ro tài khoản (USD),
    đúng như cBot của người dùng (code_bot_nonfixvol / cbot_doc_file_csv):
        Tiền rủi ro = Vốn × Rủi ro %   (không vượt "Rủi ro tối đa $" nếu có)
        Lot = Tiền rủi ro / (SL pip × Giá trị 1 pip của 1 lot)
        Làm tròn XUỐNG theo bước lot (0,01), không nhỏ hơn lot tối thiểu; kiểm tra rủi ro thực ≤ giới hạn.
  • Không có thuế bán, phí T+ như chứng khoán VN; chi phí là spread (đặt tham số).
Quy tắc cắt lỗ / chốt lời giống bản cổ phiếu (vùng hỗ trợ/kháng cự ± 0,5 ATR, chốt lời 3R) nhưng CHƯA được
kiểm định riêng cho forex.
"""
import math
from dataclasses import dataclass

from . import chi_bao, du_lieu

KHUNG_GD = "4H"            # khung giao dịch mặc định cho forex
KHUNG_LON = {"15m": "1H", "1H": "4H", "4H": "D", "D": "W", "W": "M", "M": None}
KHUNG_THU_TU = ["15m", "1H", "4H", "D", "W", "M"]
TAM_GIU = {"15m": "4–8 giờ", "1H": "1–3 ngày", "4H": "1–2 tuần", "D": "1–2 tháng", "W": "3–6 tháng",
           "M": "11–18 tháng"}                          # bảng "Khung thời gian giao dịch" của khoá học (forex)
TAM_GIU_COIN = {**TAM_GIU, "D": "1–1,5 tháng", "W": "3–4,5 tháng"}
SL_ATR = 0.5
TP_R = 3.0
SL_MAX_ATR = 3.0         # cắt lỗ xa hơn 3 ATR thì dùng 1,5 ATR (giữ khối lượng hợp lý)


@dataclass
class ThongSo:
    loai: str            # forex / vang / bac / dau / crypto / khac
    pip: float           # 1 pip (point) = bao nhiêu giá
    lot: float           # 1 lot = bao nhiêu đơn vị (100.000 tiền / 100 oz vàng / 5.000 oz bạc / 1.000 thùng dầu / 1 coin)
    goc: str = ""        # đồng tiền gốc (EUR trong EURUSD)
    dinh_gia: str = "USD"  # đồng tiền định giá (USD trong EURUSD, JPY trong USDJPY)
    lot_min: float = 0.01
    buoc_lot: float = 0.01
    don_vi: str = "lot"


def thong_so(ma: str) -> ThongSo:
    m = ma.upper().replace("/", "")
    if m in ("XAUUSD", "GOLD"):
        return ThongSo("vang", 0.01, 100, "XAU", "USD")
    if m in ("XAGUSD", "SILVER"):
        return ThongSo("bac", 0.001, 5000, "XAG", "USD")
    if m in ("USOIL", "WTI", "XTIUSD", "UKOIL", "BRENT", "XBRUSD"):
        return ThongSo("dau", 0.01, 1000, "OIL", "USD")
    for c in du_lieu.CRYPTO:
        if m in (c + "USD", c + "USDT"):
            return ThongSo("crypto", 1.0 if c in ("BTC", "ETH") else 0.0001, 1, c, "USD", 0.01, 0.01, "coin")
    if len(m) == 6 and m[:3] in du_lieu.TIEN_TE and m[3:] in du_lieu.TIEN_TE:
        return ThongSo("forex", 0.01 if m[3:] == "JPY" else 0.0001, 100_000, m[:3], m[3:])
    return ThongSo("khac", 0.01, 1, "", "USD", 1, 1, "đơn vị")


def ty_gia_ve_usd(tien: str, gia_cap: float | None = None, ma: str = "") -> float:
    """1 đơn vị `tien` = ? USD (dùng để quy giá trị pip về USD)."""
    if tien == "USD":
        return 1.0
    if ma and ma.upper().startswith("USD") and ma.upper()[3:] == tien and gia_cap:
        return 1.0 / gia_cap                                   # USDJPY: 1 JPY = 1/giá USD
    for cap, dao in ((tien + "USD", False), ("USD" + tien, True)):
        try:
            g = float(du_lieu.tai(cap, "D")["close"].iloc[-1])
            return 1.0 / g if dao else g
        except Exception:
            continue
    raise RuntimeError(f"Không lấy được tỷ giá {tien}/USD")


def gia_tri_pip_lot(ma: str, gia: float, ts: ThongSo | None = None) -> float:
    """Giá trị (USD) khi giá chạy 1 pip với 1 lot."""
    ts = ts or thong_so(ma)
    return ts.pip * ts.lot * ty_gia_ve_usd(ts.dinh_gia, gia, ma)


def khoi_luong(ma: str, gia: float, sl_gia: float, von_usd: float, rui_ro_pct: float,
               rui_ro_toi_da_usd: float = 0.0, gioi_han_pct: float | None = None) -> dict:
    """Số lot theo % rủi ro (công thức cBot). sl_gia = khoảng cách giá tới cắt lỗ (số dương)."""
    ts = thong_so(ma)
    tien_rui_ro = von_usd * rui_ro_pct / 100
    if rui_ro_toi_da_usd and tien_rui_ro > rui_ro_toi_da_usd:
        tien_rui_ro = rui_ro_toi_da_usd
    sl_pip = abs(sl_gia) / ts.pip
    pv = gia_tri_pip_lot(ma, gia, ts)
    if sl_pip <= 0 or pv <= 0:
        raise ValueError("Khoảng cắt lỗ phải > 0")
    lot_tho = tien_rui_ro / (sl_pip * pv)
    lot = math.floor(lot_tho / ts.buoc_lot + 1e-9) * ts.buoc_lot
    canh_bao = ""
    if lot < ts.lot_min:
        lot = ts.lot_min
        canh_bao = (f"Lot tính ra {lot_tho:.3f} < lot tối thiểu {ts.lot_min} – vào {ts.lot_min} lot thì rủi ro "
                    "cao hơn mức đặt.")
    rui_ro_thuc = lot * sl_pip * pv
    gh = gioi_han_pct if gioi_han_pct is not None else max(rui_ro_pct, 1.0)
    vuot = rui_ro_thuc > von_usd * gh / 100 + 1e-9
    if vuot:
        canh_bao = (f"Rủi ro thực {rui_ro_thuc:,.2f} USD ({rui_ro_thuc / von_usd:.2%}) vượt {gh:g}% vốn → "
                    "NÊN BỎ LỆNH (giống cBot) hoặc nới tài khoản.")
    return {"lot": round(lot, 4), "lot_tho": lot_tho, "don_vi": round(lot * ts.lot, 4), "sl_pip": sl_pip,
            "gia_tri_pip_lot": pv, "tien_rui_ro": tien_rui_ro, "rui_ro_thuc": rui_ro_thuc,
            "rui_ro_thuc_pct": rui_ro_thuc / von_usd if von_usd else None, "vuot_gioi_han": vuot,
            "canh_bao": canh_bao, "thong_so": ts}


def ke_hoach_fx(kq, von_usd: float = 10_000, rui_ro_pct: float = 1.0, rui_ro_toi_da_usd: float = 0.0,
                khung: str | None = None, spread_pip: float = 0.0) -> dict:
    """Kế hoạch Buy/Sell cho forex & hàng hoá từ kết quả phân tích (phan_tich_ma)."""
    khung = khung or (KHUNG_GD if KHUNG_GD in kq.frames else "D")
    kqk = next((k for k in kq.khung if k.khung == khung), None)
    df = kq.frames.get(khung)
    if kqk is None or df is None or len(df) < 40:
        return {"huong": None, "ly_do": f"Chưa đủ dữ liệu khung {khung}."}
    ten_lon = KHUNG_LON.get(khung)
    lon = next((k for k in kq.khung if k.khung == ten_lon), None)
    gia = float(df["close"].iloc[-1])
    atr = float(chi_bao.atr(df).iloc[-1])
    ts = thong_so(kq.ma)
    xh = kqk.xu_huong
    xl = lon.xu_huong if lon else xh      # khung tháng: không có khung lớn hơn để lọc
    if xh == 1 and xl >= 0:
        huong = "MUA (Buy)"
    elif xh == -1 and xl <= 0:
        huong = "BÁN (Sell)"
    else:
        huong = None
    sw = sorted(kqk.cau_truc.swings, key=lambda s: s.i) if kqk.cau_truc else []
    gan_ = sw[-8:]
    ho_tro = max([s.price for s in gan_ if s.kind == "L" and s.price < gia], default=None)
    khang_cu = min([s.price for s in gan_ if s.kind == "H" and s.price > gia], default=None)
    if huong is None:
        ly = (f"Khung {khung} {'tăng' if xh == 1 else 'giảm' if xh == -1 else 'đi ngang'}"
              + (f", khung {ten_lon} {'tăng' if xl == 1 else 'giảm' if xl == -1 else 'đi ngang'}" if lon else "")
              + " → không rõ hướng, đứng ngoài.")
        if ho_tro or khang_cu:
            ly += (" Tham khảo khi đi ngang: " + (f"mua gần hỗ trợ {ho_tro:,.5g}" if ho_tro else "")
                   + (", " if ho_tro and khang_cu else "") + (f"bán gần kháng cự {khang_cu:,.5g}" if khang_cu else "") + ".")
        return {"huong": None, "gia": gia, "khung": khung, "ly_do": ly, "atr": atr, "thong_so": ts,
                "ho_tro": ho_tro, "khang_cu": khang_cu}
    mua = huong.startswith("MUA")
    gan = sw[-8:]                                   # 8 đỉnh/đáy gần nhất
    if mua:
        ung = [s.price - SL_ATR * atr for s in gan if s.kind == "L" and s.price < gia]
        sl = max(ung) if ung else None              # đáy gần giá nhất
        ten = "dưới đáy gần nhất 0,5 ATR"
    else:
        ung = [s.price + SL_ATR * atr for s in gan if s.kind == "H" and s.price > gia]
        sl = min(ung) if ung else None              # đỉnh gần giá nhất
        ten = "trên đỉnh gần nhất 0,5 ATR"
    if sl is None or abs(gia - sl) > SL_MAX_ATR * atr or abs(gia - sl) < 0.5 * atr:
        sl = gia - 1.5 * atr if mua else gia + 1.5 * atr
        ly_sl = "cách giá 1,5 ATR (đỉnh/đáy gần nhất quá xa hoặc quá sát)"
    else:
        ly_sl = ten
    r = abs(gia - sl)
    tp = gia + TP_R * r if mua else gia - TP_R * r
    kl = khoi_luong(kq.ma, gia, r, von_usd, rui_ro_pct, rui_ro_toi_da_usd)
    pv = kl["gia_tri_pip_lot"] * kl["lot"]
    sl_pip, tp_pip = r / ts.pip, TP_R * r / ts.pip
    chi_phi = spread_pip * pv
    return {
        "huong": huong, "khung": khung, "gia": gia, "vao": gia, "cat_lo": sl, "chot_loi": tp, "atr": atr,
        "sl_pip": sl_pip, "tp_pip": tp_pip, "rr": TP_R, "lot": kl["lot"], "don_vi": kl["don_vi"],
        "lai_usd": tp_pip * pv - chi_phi, "lo_usd": -(sl_pip * pv + chi_phi), "gia_tri_pip": pv,
        "khoi_luong": kl, "thong_so": ts,
        "ho_tro": ho_tro, "khang_cu": khang_cu,
        "ly_do": (f"Khung {khung} {'tăng' if mua else 'giảm'} (điểm {kqk.diem:+.0f})"
                  + (f", khung {ten_lon} {'tăng' if xl == 1 else 'giảm' if xl == -1 else 'đi ngang'}" if lon else "")
                  + f". Cắt lỗ {ly_sl}; chốt lời = "
                  f"{TP_R:g} × khoảng cắt lỗ. CHƯA kiểm định riêng cho forex."),
    }


def ke_hoach_cac_khung(kq, von_usd: float = 10_000, rui_ro_pct: float = 1.0, rui_ro_toi_da_usd: float = 0.0) -> list[dict]:
    """Kế hoạch Mua/Bán cho từng khung 15m → 1H → 4H → D → W → M (khung nào thiếu dữ liệu thì bỏ qua)."""
    ra = []
    for k in KHUNG_THU_TU:
        if k not in kq.frames:
            continue
        try:
            kh = ke_hoach_fx(kq, von_usd, rui_ro_pct, rui_ro_toi_da_usd, khung=k)
        except Exception as e:
            kh = {"huong": None, "khung": k, "ly_do": str(e)[:100]}
        kh["khung"] = k
        kh["tam_giu"] = (TAM_GIU_COIN if thong_so(kq.ma).loai == "crypto" else TAM_GIU)[k]
        ra.append(kh)
    return ra


# Kết quả backtest 19/11/2026 (tài khoản 10.000 USD, rủi ro 1%/lệnh, 7 cặp chính + vàng + BTC, có spread, chưa swap)
KIEM_DINH = {
    "15m": ("−98% (60 ngày dữ liệu) – CHÁY TÀI KHOẢN: cắt lỗ quá sát, spread ăn mất lợi nhuận", True),
    "1H": ("−98% (~2,8 năm) – CHÁY TÀI KHOẢN, không nên dùng", True),
    "4H": ("+60% (~2,7 năm) nhưng chọn chiều ngẫu nhiên cũng +29% – lãi chủ yếu nhờ BTC/vàng tăng", False),
    "D": ("+172% (1997–2026), chọn chiều ngẫu nhiên +168% – tín hiệu chưa hơn ngẫu nhiên", False),
    "W": ("+6,5% (2000–2026), ngẫu nhiên −7%", False),
    "M": ("+11% (2001–2026), ngẫu nhiên +6% – ít lệnh", False),
}
KIEM_DINH_L1 = ("Cặp MA5/MA10 theo slide CHƯA kiểm định; cặp MA10/MA20 khung ngày đã kiểm định: +26%, sụt giảm −20% – "
                "tốt nhất trong các công thức forex đã thử nhưng chưa chắc chắn (thử 10 tổ hợp).")
