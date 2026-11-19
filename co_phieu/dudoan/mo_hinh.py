"""Mô hình xếp hạng cổ phiếu VN (nghiên cứu 19/11/2026) – tự chứa, không cần mạng, không cần lightgbm.

Cần: numpy, pandas và file `mo_hinh_model.json` cùng thư mục.

- diem_mo_hinh(df): 1 mã, chỉ dùng giá/khối lượng của chính mã đó (mô hình A_raw).
- xep_hang(ds):     nhiều mã cùng phiên (nên ≥ ~100 mã thanh khoản), thêm hạng chéo + bối cảnh thị trường
                    (mô hình B_raw_rank_mkt, tốt hơn A một chút).

Kết quả kiểm định ngoài mẫu (2020–2026, top-10 mỗi 20 phiên so với giỏ đều mọi mã thanh khoản ≥1 tỷ/phiên):
lợi thế YẾU, ~+1%/20 phiên, t≈1.7–1.9, không chắc chắn; chỉ là một yếu tố tham khảo (xem RESULT.md).
Mỗi mã chỉ "thắng trung bình" khoảng 50% số lần kể cả ở nhóm điểm cao nhất – lợi thế đến từ việc
lãi trung bình cao hơn, cần đa dạng hoá nhiều mã.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

_DUONG_DAN = Path(__file__).with_name("mo_hinh_model.json")
_M = None
GTGD_MIN = 1e9           # vũ trụ huấn luyện: GTGD bình quân 20 phiên ≥ 1 tỷ đồng
SO_PHIEN_MIN = 260       # cần ≥ 260 phiên để tính đủ đặc trưng 250 phiên


def _model():
    global _M
    if _M is None:
        _M = json.load(open(_DUONG_DAN, encoding="utf-8"))
    return _M


# ------------------------------------------------------------------ đặc trưng (giống hệt lúc huấn luyện)
def _dac_trung(df: pd.DataFrame) -> dict:
    """Đặc trưng tại phiên CUỐI của df (chỉ dùng dữ liệu đến phiên đó). Giá tính bằng đồng (VND)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return _dac_trung_(df.iloc[-300:])


def _dac_trung_(df: pd.DataFrame) -> dict:
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    v = df["volume"].to_numpy(float)
    n = len(c)
    if n < SO_PHIEN_MIN:
        raise ValueError(f"cần ≥ {SO_PHIEN_MIN} phiên, mới có {n}")
    prev = np.r_[np.nan, c[:-1]]
    r1 = c / prev - 1
    s = pd.Series(np.log(c / prev))
    F = {}

    def lui(k):
        return c[-1 - k] if n > k else np.nan

    for w in (1, 5, 20, 60, 120, 250):
        F[f"r{w}"] = c[-1] / lui(w) - 1
    F["mom12_1"] = lui(20) / lui(250) - 1
    F["mom6_1"] = lui(20) / lui(120) - 1
    hh250, ll250 = h[-250:].max(), l[-250:].min()
    F["d_hi250"] = c[-1] / hh250 - 1
    F["d_lo250"] = c[-1] / ll250 - 1
    F["pos250"] = (c[-1] - ll250) / (hh250 - ll250) if hh250 > ll250 else np.nan
    F["dd60"] = c[-1] / h[-60:].max() - 1
    F["d_hi20"] = c[-1] / h[-20:].max() - 1
    vol20 = s.rolling(20, min_periods=15).std().iloc[-1]
    vol60 = s.rolling(60, min_periods=40).std().iloc[-1]
    F["vol20"], F["vol60"] = vol20, vol60
    F["vol_ratio"] = vol20 / vol60 if vol60 else np.nan
    cs = pd.Series(c)
    m20, m50, m200 = (cs.rolling(w, min_periods=w).mean().to_numpy() for w in (20, 50, 200))
    F["p_ma20"], F["p_ma50"], F["p_ma200"] = c[-1] / m20[-1] - 1, c[-1] / m50[-1] - 1, c[-1] / m200[-1] - 1
    F["sl_ma20"] = m20[-1] / m20[-6] - 1
    F["sl_ma50"] = m50[-1] / m50[-11] - 1
    F["sl_ma200"] = m200[-1] / m200[-21] - 1 if n >= 220 else np.nan
    F["ma50_200"] = m50[-1] / m200[-1] - 1
    gap = o / prev - 1
    F["gaps20"] = float((np.abs(gap[-20:]) > 0.03).sum())
    F["ceil20"] = float((r1[-20:] > 0.065).sum())
    F["floor20"] = float((r1[-20:] < -0.065).sum())
    F["max20"] = np.nanmax(r1[-20:])
    F["up20"] = float((r1[-20:] > 0).mean())
    F["zero20"] = float((r1[-20:] == 0).mean())
    F["skew60"] = s.rolling(60, min_periods=40).skew().iloc[-1]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev), np.abs(l - prev)))
    F["atr_pct"] = pd.Series(tr).rolling(14, min_periods=14).mean().iloc[-1] / c[-1]
    gtgd = float(np.mean(c[-20:] * v[-20:]))
    F["lgtgd"] = math.log10(gtgd) if gtgd > 0 else np.nan
    F["_gtgd"] = gtgd
    return {k: (float(x) if x is not None and np.isfinite(x) else np.nan) for k, x in F.items()}


# ------------------------------------------------------------------ chạy cây LightGBM bằng Python thuần
def _cay(node, x):
    while "leaf_value" not in node:
        val = x[node["split_feature"]]
        mt = node.get("missing_type", "None")
        if math.isnan(val):
            if mt == "NaN":
                node = node["left_child"] if node["default_left"] else node["right_child"]
                continue
            val = 0.0
        if mt == "Zero" and val == 0.0:
            node = node["left_child"] if node["default_left"] else node["right_child"]
            continue
        node = node["left_child"] if val <= node["threshold"] else node["right_child"]
    return node["leaf_value"]


def _du_doan(ten, x):
    return sum(_cay(t, x) for t in _model()["models"][ten]["trees"])


def _bang(ten, diem):
    cal = _model()["models"][ten]["calibration"]
    b = cal[min(9, int(diem // 10))]
    return {"nhom": b["bucket"], "vuot_tb_20": b["ex20"], "vuot_tb_60": b["ex60"], "ti_le_thang_20": b["hit20"],
            "lai_tb_20": b["ret20"], "lai_tb_60": b["ret60"], "so_mau": b["n"], "so_phien_mau": b["dates"]}


def diem_mo_hinh(df_daily: pd.DataFrame) -> dict:
    """Điểm 0–100 cho 1 mã (phiên cuối của df). df: cột open/high/low/close/volume, DatetimeIndex, giá VND.
    Trả về điểm, nhóm (1–10), mức vượt trung bình thị trường kỳ vọng 20/60 phiên (đã trừ phí, theo lịch sử
    ngoài mẫu 2017–2026 của nhóm điểm đó) và tỉ lệ số lần vượt."""
    df = df_daily.sort_index().dropna(subset=["open", "high", "low", "close"])
    F = _dac_trung(df)
    M = _model()["models"]["A_raw"]
    x = [F[k] for k in M["features"]]
    p = _du_doan("A_raw", x)
    diem = float(np.interp(p, M["score_quantiles"], np.linspace(0, 100, 101)))
    kq = {"ngay": str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(df.index[-1]),
          "diem": round(diem, 1), "du_doan_tho": p, **_bang("A_raw", diem),
          "du_thanh_khoan": F["_gtgd"] >= GTGD_MIN,
          "ghi_chu": "Lợi thế lịch sử yếu (~+1%/20 phiên cho nhóm 10 mã điểm cao nhất, chưa chắc chắn)."}
    if not kq["du_thanh_khoan"]:
        kq["ghi_chu"] += " GTGD < 1 tỷ/phiên: ngoài vùng mô hình đã học."
    return kq


def xep_hang(ds: dict) -> pd.DataFrame:
    """Xếp hạng chéo nhiều mã tại cùng phiên cuối. ds: {mã: df_daily}. Chỉ xếp các mã GTGD ≥ 1 tỷ và
    phiên cuối trùng phiên mới nhất chung. Nên có ≥ ~100 mã (bản quét toàn thị trường hằng ngày).
    Trả về bảng: ma, diem (phân vị chéo 0–100), nhom, vuot_tb_20, vuot_tb_60, ti_le_thang_20, diem_don (mô hình A)."""
    hang = {}
    for ma, df in ds.items():
        try:
            df = df.sort_index().dropna(subset=["open", "high", "low", "close"])
            F = _dac_trung(df)
        except Exception:
            continue
        F["_ngay"] = df.index[-1]
        hang[ma] = F
    if not hang:
        return pd.DataFrame()
    X = pd.DataFrame(hang).T
    X = X[X["_ngay"] == X["_ngay"].max()]
    X = X[X["_gtgd"].astype(float) >= GTGD_MIN].drop(columns=["_ngay"]).astype(float)
    if len(X) < 30:
        raise ValueError(f"chỉ có {len(X)} mã thanh khoản cùng phiên – cần ≥ 30 (nên ≥ 100) để xếp hạng chéo")
    MB = _model()["models"]["B_raw_rank_mkt"]
    raw = [c for c in MB["features"] if not c.startswith("k_") and not c.startswith("mkt_") and not c.startswith("breadth")]
    for c in raw:
        X["k_" + c] = X[c].rank(pct=True)
    X["mkt_r20"], X["mkt_r60"], X["mkt_r250"] = X.r20.median(), X.r60.median(), X.r250.median()
    X["breadth50"], X["breadth200"] = (X.p_ma50 > 0).mean(), (X.p_ma200 > 0).mean()
    X["mkt_vol20"] = X.vol20.median()
    pB = np.array([_du_doan("B_raw_rank_mkt", r) for r in X[MB["features"]].to_numpy()])
    MA = _model()["models"]["A_raw"]
    pA = np.array([_du_doan("A_raw", r) for r in X[MA["features"]].to_numpy()])
    out = pd.DataFrame({"ma": X.index, "du_doan_tho": pB}).reset_index(drop=True)
    out["diem"] = (pd.Series(pB).rank(pct=True) * 100).round(1).to_numpy()
    cal = [_bang("B_raw_rank_mkt", min(d, 99.9)) for d in out["diem"]]
    out = pd.concat([out, pd.DataFrame(cal)], axis=1)
    out["diem_don"] = np.round(np.interp(pA, MA["score_quantiles"], np.linspace(0, 100, 101)), 1)
    return out.sort_values("diem", ascending=False).reset_index(drop=True)
