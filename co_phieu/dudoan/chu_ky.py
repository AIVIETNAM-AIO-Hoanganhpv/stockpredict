"""Chu kỳ thị trường (pha), xếp hạng ngành và quy tắc DÀI HẠN – theo backtest 19/11/2026 (scratchpad bt_chuky).

Kiểm định (chọn tham số 2008–2019, kiểm tra 1 lần 2020–2026, vốn 1 tỷ, đã trừ phí):
  • Lọc pha thị trường + mua đều mã thanh khoản: +16,0%/năm, sụt giảm tối đa −22%  (mua & giữ: +9,9%, −60%)
  • Lọc pha + 2 ngành mạnh nhất: +19,5%/năm, −23% (lớp ngành kém ổn định hơn)
  • Dài hạn (cuối tháng mua mã 2 ngành mạnh khi pha tốt, bán khi giá tháng < MA10 tháng hoặc sau 12 tháng): +14,7%, −30%
Lợi thế chủ yếu là tránh năm 2022; vào lại chậm khi thị trường hồi; đổi trạng thái ~17 lần/năm.

Pha (tính ở giá đóng cửa ngày t, dùng cho ngày t+1):
  I = chỉ số bình quân đều các mã thanh khoản (GTGD 20 phiên ≥ 1 tỷ), br50 = % mã đó nằm trên MA50 của chính nó.
  MS = MA20(I), ML = MA100(I), LT = MS > ML, S = (I > MS) và br50 ≥ 60%
  Tăng (LT & S) · Phân phối (LT & không S) · Tích luỹ cuối (không LT & S & I > ML) ·
  Tích luỹ (không LT & (I > MS hoặc br50 ≥ 60%)) · Giảm (còn lại)
  Nên cầm cổ phiếu (risk-on) ở Tăng / Tích luỹ cuối / Tích luỹ, TRỪ KHI lợi suất trái phiếu Mỹ 10 năm tăng > 0,75 điểm
  trong 3 tháng (số liệu cuối tháng, dùng từ tháng sau). Lãi suất VN chưa có nguồn lịch sử → chưa dùng.
"""
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

GTGD_MIN = 1e9
MS, ML, BR = 20, 100, 0.60
TNX_NGUONG = 0.75
PHA_TOT = ("Tăng", "Tích luỹ cuối", "Tích luỹ")
MAU_PHA = {"Tăng": "#2ca02c", "Tích luỹ cuối": "#98df8a", "Tích luỹ": "#ff9896", "Phân phối": "#ffbb78",
           "Giảm": "#d62728"}
LOI_KHUYEN = {
    "Tăng": "Thị trường đang TĂNG – được cầm cổ phiếu, ưu tiên 2 ngành mạnh nhất.",
    "Tích luỹ cuối": "Thị trường TÍCH LUỸ CUỐI – có thể mua dần, ưu tiên ngành mạnh.",
    "Tích luỹ": "Thị trường TÍCH LUỸ – mua thăm dò tỷ trọng nhỏ.",
    "Phân phối": "Thị trường PHÂN PHỐI – nên bán bớt / giữ tiền, không mua mới.",
    "Giảm": "Thị trường GIẢM – giữ tiền mặt, không mua mới.",
}
KIEM_DINH = ("Kiểm định 2020–2026 (vốn 1 tỷ): theo pha thị trường +16%/năm, sụt giảm tối đa −22% so với mua & giữ "
             "+9,9%/năm, −60% – lợi thế chủ yếu nhờ tránh năm 2022, vào lại chậm khi thị trường hồi.")


def bang_gia(ds: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Từ {mã: df ngày} → bảng giá đóng cửa và GTGD bình quân 20 phiên (cột = mã)."""
    c = pd.DataFrame({m: d["close"] for m, d in ds.items() if d is not None and len(d)}).sort_index()
    v = pd.DataFrame({m: (d["close"] * d.get("volume", 0)).rolling(20).mean()
                      for m, d in ds.items() if d is not None and len(d)}).reindex(c.index)
    return c, v


def chi_so_thi_truong(c: pd.DataFrame, v: pd.DataFrame) -> pd.DataFrame:
    """Chỉ số bình quân đều mã thanh khoản (I) và độ rộng br50."""
    cf = c.ffill()
    so_phien = c.notna().cumsum()
    thanh_khoan = (v >= GTGD_MIN) & (so_phien >= 60)
    r = (cf / cf.shift(1) - 1).clip(-0.30, 0.40)
    r = r.where(thanh_khoan.shift(1, fill_value=False) & c.notna())
    I = (1 + r.mean(axis=1).fillna(0)).cumprod()
    tren50 = (cf > cf.rolling(50).mean()).where(thanh_khoan & (so_phien >= 50))
    br = tren50.sum(axis=1) / tren50.notna().sum(axis=1).replace(0, np.nan)
    return pd.DataFrame({"I": I, "br50": br, "so_ma": thanh_khoan.sum(axis=1)})


def phan_pha(I: pd.Series, br: pd.Series) -> pd.Series:
    ms, ml = I.rolling(MS).mean(), I.rolling(ML).mean()
    lt = ms > ml
    s = (I > ms) & (br >= BR)
    pha = np.select([lt & s, lt & ~s, ~lt & s & (I > ml), ~lt & ((I > ms) | (br >= BR))],
                    ["Tăng", "Phân phối", "Tích luỹ cuối", "Tích luỹ"], default="Giảm")
    pha = pd.Series(pha, index=I.index)
    pha[ml.isna()] = "Giảm"
    return pha


def vi_mo_xau(tnx: pd.Series | None, ngay: pd.DatetimeIndex) -> pd.Series:
    """True khi lợi suất Mỹ 10 năm tăng > 0,75 điểm trong 3 tháng (cuối tháng, dùng từ đầu tháng sau)."""
    if tnx is None or tnx.empty:
        return pd.Series(False, index=ngay)
    m = tnx.resample("ME").last()
    co = (m - m.shift(3)) > TNX_NGUONG
    co.index = co.index + pd.Timedelta(days=1)          # dùng từ ngày 1 tháng sau
    return co.reindex(ngay.union(co.index)).ffill().reindex(ngay).fillna(False).astype(bool)


def tai_tnx() -> pd.Series | None:
    try:
        from . import du_lieu
        return du_lieu._yahoo("^TNX", "D")["close"]
    except Exception:
        return None


def xep_hang_nganh(c: pd.DataFrame, v: pd.DataFrame, nganh: dict, look: int = 63) -> pd.DataFrame:
    """Điểm ngành = hạng(lợi suất 3 tháng) + hạng(% mã trên MA50), chỉ ngành có ≥ 3 mã thanh khoản."""
    cf = c.ffill()
    tk = (v.iloc[-1] >= GTGD_MIN) & (c.notna().sum() >= 60)
    r = (cf / cf.shift(1) - 1).clip(-0.30, 0.40)
    tren50 = cf.iloc[-1] > cf.rolling(50).mean().iloc[-1]
    rows = []
    for ng in sorted({nganh.get(m, "Khác") for m in c.columns}):
        ma = [m for m in c.columns if nganh.get(m, "Khác") == ng and tk.get(m, False)]
        if len(ma) < 3:
            continue
        si = (1 + r[ma].where((v[ma] >= GTGD_MIN).shift(1, fill_value=False)).mean(axis=1).fillna(0)).cumprod()
        if len(si) <= look:
            continue
        rows.append({"Ngành": ng, "Số mã": len(ma), "Lợi suất 3 tháng %": round((si.iloc[-1] / si.iloc[-1 - look] - 1) * 100, 1),
                     "% mã trên MA50": round(float(tren50[ma].mean()) * 100, 0)})
    b = pd.DataFrame(rows)
    if b.empty:
        return b
    b["Điểm"] = b["Lợi suất 3 tháng %"].rank() + b["% mã trên MA50"].rank()
    return b.sort_values("Điểm", ascending=False).reset_index(drop=True)


def dai_han_ma(df: pd.DataFrame) -> dict:
    """Quy tắc bán dài hạn: tháng (đã kết thúc) đóng cửa dưới MA10 tháng → bán phiên kế tiếp; giữ tối đa 12 tháng."""
    if df is None or len(df) < 30:
        return {}
    c = df["close"].dropna()
    m = c.resample("ME").last()
    hom_nay = c.index[-1]
    if m.index[-1] > hom_nay and (hom_nay + pd.offsets.BDay(1)).month == hom_nay.month:
        m = m.iloc[:-1]                       # tháng hiện tại chưa kết thúc
    if len(m) < 10:
        return {"du_lieu": False}
    ma10 = m.rolling(10).mean()
    tren = bool(m.iloc[-1] >= ma10.iloc[-1])
    return {"du_lieu": True, "thang": m.index[-1].strftime("%m/%Y"), "dong_cua_thang": float(m.iloc[-1]),
            "ma10_thang": float(ma10.iloc[-1]), "tren_ma10": tren,
            "trang_thai": "Giữ (giá tháng trên MA10 tháng)" if tren else "BÁN – tháng đóng cửa dưới MA10 tháng"}


def danh_gia(ds: dict, nganh: dict, tnx: pd.Series | None = None, so_phien_luu: int = 500) -> dict:
    """Trạng thái chu kỳ hôm nay + lịch sử pha (để tô màu biểu đồ) + 2 ngành mạnh + danh sách dài hạn."""
    c, v = bang_gia(ds)
    if c.empty or len(c) < ML + 5:
        return {}
    cs = chi_so_thi_truong(c, v)
    pha = phan_pha(cs["I"], cs["br50"])
    xau = vi_mo_xau(tnx, cs.index)
    tot = pha.isin(PHA_TOT) & ~xau
    p0 = pha.iloc[-1]
    tu = pha.index[-1]
    for d, x in pha.iloc[::-1].items():
        if x != p0:
            break
        tu = d
    ng = xep_hang_nganh(c, v, nganh)
    top2 = ng["Ngành"].head(2).tolist() if not ng.empty else []
    tk_nay = v.iloc[-1]
    dai_han = []
    if bool(tot.iloc[-1]) and top2:
        ung = [m for m in c.columns if nganh.get(m) in top2 and tk_nay.get(m, 0) >= GTGD_MIN]
        for m in sorted(ung, key=lambda x: -tk_nay[x])[:10]:
            x = dai_han_ma(ds[m])
            if x.get("du_lieu"):
                dai_han.append({"Mã": m, "Ngành": nganh.get(m), "Giá": round(float(c[m].dropna().iloc[-1]), 0),
                                "MA10 tháng": round(x["ma10_thang"], 0), "Trạng thái": x["trang_thai"],
                                "GTGD (tỷ)": round(float(tk_nay[m]) / 1e9, 1)})
    lich_su = [{"t": d.strftime("%Y-%m-%d"), "I": round(float(cs["I"][d]), 5),
                "br": None if pd.isna(cs["br50"][d]) else round(float(cs["br50"][d]), 3), "pha": pha[d],
                "tot": bool(tot[d])} for d in cs.index[-so_phien_luu:]]
    return {"luc": dt.datetime.now().strftime("%d/%m/%Y %H:%M"), "ngay": cs.index[-1].strftime("%Y-%m-%d"),
            "pha": p0, "tu_ngay": tu.strftime("%Y-%m-%d"), "nen_cam_co_phieu": bool(tot.iloc[-1]),
            "vi_mo_xau": bool(xau.iloc[-1]), "loi_khuyen": LOI_KHUYEN[p0] + (
                " Lưu ý: lợi suất Mỹ tăng mạnh → tạm giữ tiền." if xau.iloc[-1] else ""),
            "do_rong_ma50": None if pd.isna(cs["br50"].iloc[-1]) else round(float(cs["br50"].iloc[-1]), 3),
            "so_ma": int(cs["so_ma"].iloc[-1]),
            "chi_so_vs_ma20": round(float(cs["I"].iloc[-1] / cs["I"].rolling(MS).mean().iloc[-1] - 1), 4),
            "chi_so_vs_ma100": round(float(cs["I"].iloc[-1] / cs["I"].rolling(ML).mean().iloc[-1] - 1), 4),
            "nganh": json.loads(ng.head(8).to_json(orient="records", force_ascii=False)) if not ng.empty else [],
            "nganh_top2": top2, "dai_han": dai_han, "lich_su": lich_su, "kiem_dinh": KIEM_DINH}


def doc(thu_muc) -> dict:
    f = Path(thu_muc) / "chu_ky.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}
