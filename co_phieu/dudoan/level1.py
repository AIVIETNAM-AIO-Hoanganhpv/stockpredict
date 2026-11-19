"""Công thức giao dịch LEVEL 1 (tài liệu LEVEL_1_IFT) – trạng thái hiện tại của MỘT mã trên khung D / W / M.

  • Cặp MA tín hiệu / điều kiện: MA6–MA10 hoặc MA10–MA20 (D: tự chọn – MA10 sát giá → MA10/20, xa giá → MA6/10;
    W: MA6/10; M: MA10/20 – theo kết quả chọn trên 2008–2019).
  • Lệnh VỊ THẾ: MA tín hiệu cắt lên MA điều kiện (≤ 2 nến trước) và nến đóng cửa là nến tăng, trên cả 2 MA.
    Cắt lỗ: đáy thấp nhất của đoạn nến gần nhất có giá thấp < MA điều kiện.
  • Lệnh XÁC NHẬN: sau đó, nến tăng đóng cửa trên MA điều kiện khi lệnh vị thế đang có lãi.
    Cắt lỗ: nến gần nhất có đáy dưới MA điều kiện (cách MA ≥ 0,25 ATR).
  • BÁN 50%: nến đóng cửa dưới MA điều kiện · BÁN HẾT: MA tín hiệu cắt xuống MA điều kiện · luôn tôn trọng cắt lỗ.
  • Đồng pha: D cần khung W tăng (MA10 > MA20 tuần) và thị trường chung tốt; W cần khung M tăng (cho phép thăm dò
    30% nếu đã có ≥ 2 nhịp giảm – công thức GĐ2); M không cần.
  • Quản trị vốn: tiền chấp nhận cắt lỗ cho 1 cơ hội = D 5% · W 12% · M 12% tài khoản, chia đều cho tối đa 10 mã,
    nhân hệ số nhịp (nhịp 1–2: 100%, 3: 60%, 4: 40%, ≥5: 30%); lệnh vị thế 30%, lệnh xác nhận 70%.
    Khối lượng = tiền cắt lỗ ÷ (giá vào − giá cắt lỗ), làm tròn xuống lô 100.

Kiểm định 2020–2026 (vốn 1 tỷ, chọn tham số trên 2008–2019): D +4,0%/năm, W +2,6%, M +5,2%, cả 3 khung +6,7%/năm
(sụt giảm tối đa −35%) – THẤP HƠN mua & giữ (+9,9%) và lọc pha thị trường (+16%). Chỉ để tham khảo.
"""
import numpy as np
import pandas as pd

CAP_MA = {"D": "tu_chon", "W": (6, 10), "M": (10, 20)}
NGUONG_HUG = {"D": 0.874, "W": 0.848, "M": 0.820}
TIEN_CAT_LO = {"D": 0.05, "W": 0.12, "M": 0.12}
SO_MA = 10
KHUNG_LON = {"D": "W", "W": "M"}
KIEM_DINH = {"D": "+4,0%/năm", "W": "+2,6%/năm", "M": "+5,2%/năm"}
TEN = {"D": "Ngày (1–3 tháng)", "W": "Tuần (3–9 tháng)", "M": "Tháng (1–2 năm)"}


def nen_khung(df: pd.DataFrame, khung: str) -> pd.DataFrame:
    """Nến D/W/M; W, M chỉ lấy nến ĐÃ KẾT THÚC (không dùng nến đang chạy)."""
    df = df.dropna(subset=["close"]).copy()
    df["open"] = df["open"].fillna(df["close"].shift(1)).fillna(df["close"])
    if khung == "D":
        return df
    quy = "W-FRI" if khung == "W" else "ME"
    g = df.resample(quy).agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna(subset=["close"])
    hom_nay = df.index[-1]
    if len(g) and g.index[-1] > hom_nay:
        het = (khung == "W" and hom_nay.weekday() == 4) or (
            khung == "M" and (hom_nay + pd.offsets.BDay(1)).month != hom_nay.month)
        if not het:
            g = g.iloc[:-1]
    return g


def _chi_bao(b: pd.DataFrame) -> pd.DataFrame:
    c = b["close"]
    for n in (6, 10, 20):
        b[f"ma{n}"] = c.rolling(n).mean()
    tr = pd.concat([b["high"] - b["low"], (b["high"] - c.shift()).abs(), (b["low"] - c.shift()).abs()], axis=1).max(axis=1)
    b["atr"] = tr.rolling(14).mean()
    b["hug"] = (c - b["ma10"]).abs().rolling(20).mean() / b["atr"]
    return b


def _nhip(duoi: np.ndarray, low: np.ndarray, den: int) -> tuple[int, int]:
    """Đếm nhịp bằng đáy các đoạn điều chỉnh (đóng cửa dưới MA điều kiện): nhịp = số đáy sau cao hơn đáy trước + 1."""
    s, k = [], den
    while k >= 0 and len(s) < 12:
        if duoi[k]:
            m = low[k]
            while k - 1 >= 0 and duoi[k - 1]:
                k -= 1
                m = min(m, low[k])
            s.append(m)
        k -= 1
    s = s[::-1]
    if not s:
        return 1, 0
    len_ = 0
    cur = s[-1]
    for p in s[-2::-1]:
        if cur > p:
            len_ += 1
            cur = p
        else:
            break
    xuong = 0
    cur = s[-1]
    for p in s[-2::-1]:
        if cur < p:
            xuong += 1
            cur = p
        else:
            break
    return len_ + 1, xuong


def he_so_nhip(nhip: int, lon_tang: bool) -> float:
    if not lon_tang:
        return 0.3                      # công thức GĐ2: thăm dò tối đa 30%
    return 1.0 if nhip <= 2 else 0.6 if nhip == 3 else 0.4 if nhip == 4 else 0.3


def khung_lon_tang(df: pd.DataFrame, khung: str) -> bool:
    lon = KHUNG_LON.get(khung)
    if lon is None:
        return True
    b = _chi_bao(nen_khung(df, lon))
    return bool(len(b) >= 20 and b["ma10"].iloc[-1] > b["ma20"].iloc[-1])


def trang_thai(df: pd.DataFrame, khung: str = "D", von: float = 1e9, thi_truong_tot: bool = True,
               so_ma: int = SO_MA, tien_cat_lo_pct: float | None = None, lo: int = 100,
               cap: tuple | None = None) -> dict:
    """Trạng thái LEVEL 1 hiện tại: tín hiệu mới / đang giữ / bán 50% / bán hết / không có, kèm giá & khối lượng."""
    b = _chi_bao(nen_khung(df, khung))
    n = len(b)
    if n < 25:
        return {"khung": khung, "trang_thai": "Chưa đủ dữ liệu", "co_lenh": False}
    o, h, l, c = (b[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    cap_cd = cap or CAP_MA[khung]
    if cap_cd == "tu_chon":
        cap_hien = (10, 20) if b["hug"].iloc[-1] <= NGUONG_HUG[khung] else (6, 10)
    else:
        cap_hien = cap_cd
    lon_tang = khung_lon_tang(df, khung)
    ket = None
    # duyệt các lần lệnh vị thế trong ~150 nến gần nhất, mô phỏng tới nến cuối
    j = max(21, n - 150)
    while j < n:
        cap_j = ((10, 20) if b["hug"].iloc[j] <= NGUONG_HUG[khung] else (6, 10)) if cap_cd == "tu_chon" else cap_cd
        sg, cd = b[f"ma{cap_j[0]}"].to_numpy(), b[f"ma{cap_j[1]}"].to_numpy()
        tren = sg > cd
        cat_len = any(tren[x] and not tren[x - 1] and all(tren[x:j + 1]) for x in range(max(1, j - 2), j + 1))
        if not (cat_len and c[j] > o[j] and c[j] > sg[j] and c[j] > cd[j]):
            j += 1
            continue
        k = j
        while k >= max(0, j - 30) and not l[k] < cd[k]:
            k -= 1
        if k < max(0, j - 30):
            j += 1
            continue
        sl = l[k]
        while k - 1 >= max(0, j - 30) and l[k - 1] < cd[k - 1]:
            k -= 1
            sl = min(sl, l[k])
        if not sl < c[j]:
            j += 1
            continue
        duoi = c < cd
        nhip, nhip_giam = _nhip(duoi, l, j)
        e = {"cap": cap_j, "j": j, "vao": c[j], "cat_lo": sl, "nhip": nhip, "nhip_giam": nhip_giam,
             "xac_nhan": None, "ban_50": None, "ban_het": None, "dung_lo": None, "xn_cat_lo": None}
        # mô phỏng sau nến tín hiệu
        for m in range(j + 1, n):
            if l[m] < e["cat_lo"]:
                e["dung_lo"] = m
                break
            if sg[m] < cd[m]:
                e["ban_het"] = m
                break
            if e["ban_50"] is None and c[m] < cd[m]:
                e["ban_50"] = m
            if e["xac_nhan"] is None and e["ban_50"] is None and c[m] > o[m] and c[m] > c[j] and c[m] > cd[m]:
                e["xac_nhan"] = m
                cand = [q for q in range(m, max(-1, m - 20), -1) if l[q] < cd[q]]
                xa = [q for q in cand if l[q] <= cd[q] - 0.25 * b["atr"].iloc[q]]
                e["xn_cat_lo"] = l[xa[0]] if xa else (min(l[q] for q in cand) if cand else sl)
        ket = e
        ket_thuc = e["dung_lo"] or e["ban_het"]
        j = (ket_thuc + 1) if ket_thuc else n
    gia = c[-1]
    ngay = lambda i: b.index[i].strftime("%d/%m/%Y")  # noqa: E731
    out = {"khung": khung, "ten_khung": TEN[khung], "gia": gia, "khung_lon_tang": lon_tang,
           "cap_ma": f"MA{cap_hien[0]}/MA{cap_hien[1]}", "kiem_dinh": KIEM_DINH[khung], "co_lenh": False}
    dang_mo = ket and not (ket["dung_lo"] or ket["ban_het"])
    vua_dong = ket and (ket["dung_lo"] == n - 1 or ket["ban_het"] == n - 1)
    if ket is None or not (dang_mo or vua_dong):
        sg, cd = b[f"ma{cap_hien[0]}"].iloc[-1], b[f"ma{cap_hien[1]}"].iloc[-1]
        out.update(trang_thai="KHÔNG CÓ TÍN HIỆU",
                   mo_ta=f"MA{cap_hien[0]} {'trên' if sg > cd else 'dưới'} MA{cap_hien[1]} – chờ MA tín hiệu cắt lên "
                         "MA điều kiện và có nến tăng đóng cửa trên cả 2 MA.")
        return out
    e = ket
    out["cap_ma"] = f"MA{e['cap'][0]}/MA{e['cap'][1]}"
    dong_pha = lon_tang and (thi_truong_tot or khung != "D")
    tham_do = (not lon_tang) and e["nhip_giam"] >= 2 and khung == "W"
    f = he_so_nhip(e["nhip"], lon_tang)
    pct = tien_cat_lo_pct if tien_cat_lo_pct is not None else TIEN_CAT_LO[khung]
    vung = von * pct / so_ma * f
    def cp(tien, vao, sl):  # noqa: E306
        return int(tien / (vao - sl) // lo * lo) if vao > sl else 0
    out.update(co_lenh=True, ngay_tin_hieu=ngay(e["j"]), vao=e["vao"], cat_lo=e["cat_lo"], nhip=e["nhip"],
               he_so=f, dong_pha=dong_pha or tham_do, tham_do=tham_do,
               tien_cat_lo=vung, cp_vi_the=cp(0.3 * vung, e["vao"], e["cat_lo"]))
    if e["xac_nhan"] is not None:
        vx = c[e["xac_nhan"]]
        out.update(xac_nhan=True, ngay_xac_nhan=ngay(e["xac_nhan"]), vao_xn=vx, cat_lo_xn=e["xn_cat_lo"],
                   cp_xac_nhan=cp(0.7 * vung, vx, e["xn_cat_lo"]) if e["xn_cat_lo"] else 0)
    if e["dung_lo"] == n - 1:
        tt = "ĐÃ CẮT LỖ"
    elif e["ban_het"] == n - 1:
        tt = "BÁN HẾT (MA tín hiệu cắt xuống)"
    elif e["j"] == n - 1:
        tt = "MUA LỆNH VỊ THẾ" if (dong_pha or tham_do) else "TÍN HIỆU NGƯỢC PHA – KHÔNG VÀO"
    elif e["xac_nhan"] == n - 1:
        tt = "MUA LỆNH XÁC NHẬN"
    elif e["ban_50"] == n - 1:
        tt = "BÁN 50% (đóng cửa dưới MA điều kiện)"
    elif e["ban_50"] is not None:
        tt = "ĐANG GIỮ 50% – bán nốt khi MA cắt xuống"
    else:
        tt = "ĐANG GIỮ"
    out["trang_thai"] = tt
    out["lai_pct"] = gia / e["vao"] - 1
    d_ = lambda x: f"{x:,.0f}".replace(",", ".")  # noqa: E731
    out["mo_ta"] = (f"Lệnh vị thế {ngay(e['j'])} giá {d_(e['vao'])}, cắt lỗ {d_(e['cat_lo'])}; nhịp {e['nhip']} "
                    f"(hệ số vốn {f:.0%}); khung lớn {'tăng' if lon_tang else 'chưa tăng'}"
                    + ("" if khung != "D" else f"; thị trường {'tốt' if thi_truong_tot else 'xấu'}") + ".")
    return out
