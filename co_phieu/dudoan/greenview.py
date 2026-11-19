"""Cầu nối StockPredict ↔ GreenView.

  • goi_du_lieu(ma): giá ngày (Vietcap / Yahoo) + kế hoạch khuyến nghị hiện tại + tín hiệu Mua trong quá khứ
    (mỗi lệnh: ngày mua, giá, cắt lỗ, chốt lời, kết quả) – dạng JSON cho GreenView.
  • html_nhung(du_lieu): file GreenView (greenview/dist/GreenView.html) có sẵn dữ liệu, mở thẳng mã đó
    (dùng trong web app Streamlit).
Trình duyệt không gọi thẳng được API giá của Vietcap (bị chặn CORS) nên Python lấy giá rồi đưa cho GreenView.
"""
import datetime as dt
import json
import math
from pathlib import Path

import pandas as pd

from . import du_lieu, khuyen_nghi as K, phan_tich

GOC = Path(__file__).resolve().parents[2]
FILE_GV = GOC / "greenview" / "dist" / "GreenView.html"


def _so(x, nd=2):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, nd) if math.isfinite(x) else None


def _phan_tich(ma: str, df: pd.DataFrame):
    loai, chuan = du_lieu.phan_loai(ma)
    frames = {"M": du_lieu.resample(df, "M"), "W": du_lieu.resample(df, "W"), "D": df}
    ds = [phan_tich.phan_tich_khung(f, k) for k, f in frames.items()]
    kq = phan_tich.tong_hop(chuan, loai, ds)
    kq.frames = frames
    return kq


def ke_hoach(ma: str, df: pd.DataFrame) -> dict:
    """Kế hoạch khuyến nghị hiện tại (giống bảng khuyến nghị của công cụ)."""
    kq = _phan_tich(ma, df)
    if not kq.khung:
        return {}
    kn = K.khuyen_nghi(kq, "D")
    dinh = K.tin_hieu_dinh(kq, "D")
    tg = kn.thoi_gian
    du_kien = som = muon = None
    if tg is not None and tg.thuong is not None:
        d = tg.ngay(tg.thuong)
        du_kien = int(pd.Timestamp(d).timestamp()) if d is not None else None
        som = int(pd.Timestamp(tg.ngay(tg.som)).timestamp()) if tg.som is not None else None
        muon = int(pd.Timestamp(tg.ngay(tg.muon)).timestamp()) if tg.muon is not None else None
    return {
        "muc": kn.muc, "diem": _so(kn.diem, 1), "gia": _so(kn.gia), "gia_mua": _so(kn.gia_mua),
        "cat_lo": _so(kn.cat_lo), "chot_loi": _so(kn.chot_loi1), "rr": _so(kn.rr),
        "vung": [_so(kn.vung.thap), _so(kn.vung.cao)] if kn.vung else None,
        "du_kien": du_kien, "du_kien_som": som, "du_kien_muon": muon,
        "giu_toi_da": K.GIU_TOI_DA, "ly_do": kn.ly_do,
        "dinh": {"muc": dinh.muc, "so": dinh.so_dau_hieu, "dau_hieu": dinh.dau_hieu},
        "xu_huong": kq.nhan, "diem_xu_huong": _so(kq.diem, 1),
    }


def tin_hieu_qua_khu(ma: str, df: pd.DataFrame, so_phien: int = 500, buoc: int = 3) -> list[dict]:
    """Các lần công cụ báo "Mua" trong `so_phien` phiên gần nhất (chỉ dùng dữ liệu đến từng ngày),
    giả lập lệnh theo đúng quy tắc: mua giá mở cửa phiên sau, thoát khi chạm cắt lỗ / chốt lời / hết 60 phiên.
    Không mở lệnh mới khi lệnh trước chưa đóng. Lãi đã trừ phí & thuế."""
    o, h, l, c = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    n = len(df)
    ra = []
    i = max(260, n - so_phien)
    het_lenh = -1
    while i < n - 1:
        if i <= het_lenh:
            i += 1
            continue
        try:
            kq = _phan_tich(ma, df.iloc[max(0, i + 1 - 1500): i + 1])
            kn = K.khuyen_nghi(kq, "D")
        except Exception:
            i += buoc
            continue
        if kn.muc != "Mua" or not kn.cat_lo or not kn.chot_loi1:
            i += buoc
            continue
        j0 = i + 1
        vao, sl, tp = o[j0], kn.cat_lo, kn.chot_loi1
        if not sl < vao < tp:
            i += buoc
            continue
        het = min(j0 + K.GIU_TOI_DA - 1, n - 1)
        ket_qua, j_ra, gia_ra = "Đang giữ", n - 1, c[n - 1]
        for j in range(j0, het + 1):
            if l[j] <= sl:
                ket_qua, j_ra, gia_ra = "Cắt lỗ", j, (min(o[j], sl) if j > j0 else sl)
                break
            if h[j] >= tp:
                ket_qua, j_ra, gia_ra = "Chốt lời", j, (max(o[j], tp) if j > j0 else tp)
                break
        else:
            if het < n - 1 or het - j0 + 1 >= K.GIU_TOI_DA:
                ket_qua, j_ra, gia_ra = "Hết 60 phiên", het, c[het]
        lai = gia_ra * (1 - K.PHI_BAN - K.THUE_BAN) / (vao * (1 + K.PHI_MUA)) - 1
        ra.append({"t_bao": int(df.index[i].timestamp()), "t_mua": int(df.index[j0].timestamp()),
                   "t_ra": int(df.index[j_ra].timestamp()), "gia_mua": _so(vao), "cat_lo": _so(sl),
                   "chot_loi": _so(tp), "gia_ra": _so(gia_ra), "ket_qua": ket_qua, "lai_pct": _so(lai * 100, 1),
                   "diem": _so(kn.diem, 1)})
        het_lenh = j_ra
        i = j_ra + 1
    return ra


def nen(df: pd.DataFrame) -> list[dict]:
    """Nến dạng GreenView: time = giây (đầu ngày, UTC), giá giữ nguyên đơn vị của nguồn."""
    df = df.dropna(subset=["open", "high", "low", "close"])
    return [{"time": int(t.timestamp()), "open": _so(r.open, 4), "high": _so(r.high, 4), "low": _so(r.low, 4),
             "close": _so(r.close, 4), "volume": _so(r.volume, 0) or 0}
            for t, r in zip(df.index, df.itertuples(index=False))]


def goi_du_lieu(ma: str, df: pd.DataFrame | None = None, qua_khu: bool = True, so_nen: int = 1500) -> dict:
    """Gói dữ liệu cho GreenView: nến ngày + kế hoạch + tín hiệu quá khứ."""
    ma = ma.strip().upper()
    if df is None:
        df = du_lieu.tai(ma, "D")
    df = df.dropna(subset=["open", "high", "low", "close"]).iloc[-so_nen:]
    goi = {"ma": ma, "bars": nen(df), "luc": dt.datetime.now().strftime("%d/%m/%Y %H:%M")}
    try:
        goi["ke_hoach"] = ke_hoach(ma, df)
    except Exception as e:
        goi["ke_hoach"] = {"loi": str(e)[:120]}
    if qua_khu:
        try:
            goi["tin_hieu"] = tin_hieu_qua_khu(ma, df)
        except Exception:
            goi["tin_hieu"] = []
    return goi


def html_nhung(du_lieu_goi: dict | None = None, api: str | None = None) -> str:
    """GreenView kèm dữ liệu (`window.GV_DATA`) và/hoặc địa chỉ máy chủ giá (`window.GV_API`)."""
    html = FILE_GV.read_text(encoding="utf-8")
    cau_hinh = "<script>"
    if du_lieu_goi is not None:
        cau_hinh += "window.GV_DATA=" + json.dumps(du_lieu_goi, ensure_ascii=False).replace("</", "<\\/") + ";"
    if api is not None:
        cau_hinh += "window.GV_API=" + json.dumps(api) + ";"
    cau_hinh += "</script>"
    return html.replace("<head>", "<head>" + cau_hinh, 1)
