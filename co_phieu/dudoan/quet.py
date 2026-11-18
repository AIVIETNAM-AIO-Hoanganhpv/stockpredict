"""Quét toàn thị trường chứng khoán VN (HOSE, HNX, UPCoM): khuyến nghị mua và xếp hạng."""
import datetime as dt
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import du_lieu, khuyen_nghi as K, phan_tich


@dataclass
class KetQuaMa:
    ma: str
    san: str
    ten: str
    kq: object = None           # phan_tich.KetQua
    kn: dict = None             # {"D": KhuyenNghi, "W": KhuyenNghi}
    gtgd: float = 0.0
    thay_doi: float = 0.0       # % thay đổi phiên gần nhất
    loi: str = ""


def phan_tich_df(ma: str, df: pd.DataFrame, loai: str = "vn"):
    """Phân tích đủ M/W/D từ dữ liệu ngày, trả về (KetQua, {tầm: KhuyenNghi})."""
    frames = {"M": du_lieu.resample(df, "M"), "W": du_lieu.resample(df, "W"), "D": df.iloc[-600:]}
    ds = [phan_tich.phan_tich_khung(f, k) for k, f in frames.items()]
    kq = phan_tich.tong_hop(ma, loai, ds)
    kq.frames = frames
    return kq, {tam: K.khuyen_nghi(kq, tam, loai) for tam in ("D", "W")}


def _mot_ma(ma, san, ten, gtgd_min):
    r = KetQuaMa(ma, san, ten)
    try:
        df = du_lieu._vci(ma, "D")
        gt = (df["close"] * df["volume"]).iloc[-20:]
        r.gtgd = float(gt.mean()) if len(gt) else 0.0
        if len(df) >= 2:
            r.thay_doi = float(df["close"].iloc[-1] / df["close"].iloc[-2] - 1)
        if df.index[-1] < pd.Timestamp.now() - pd.Timedelta(days=14):
            r.loi = "Không giao dịch 2 tuần gần đây"
        elif r.gtgd < gtgd_min:
            r.loi = "Thanh khoản thấp"
        else:
            r.kq, r.kn = phan_tich_df(ma, df)
    except Exception as e:
        r.loi = str(e)[:120]
    return r


def quet(san=("HSX", "HNX", "UPCOM"), gtgd_min: float = 1e9, so_luong: int = 6,
         ds_ma: list | None = None, tien_trinh=None) -> list[KetQuaMa]:
    """Tải & phân tích mọi mã. `gtgd_min`: bỏ qua mã có GTGD bình quân 20 phiên thấp hơn (đồng).
    `tien_trinh(i, n, ma)`: hàm báo tiến độ (thanh tiến trình trên web)."""
    dsm = du_lieu.danh_sach_ma_vn(san)
    if ds_ma:
        dsm = dsm[dsm["ma"].isin([m.upper() for m in ds_ma])]
    viec = list(dsm.itertuples(index=False))
    out = []
    with ThreadPoolExecutor(max_workers=so_luong) as ex:
        futs = [ex.submit(_mot_ma, x.ma, x.san, x.ten, gtgd_min) for x in viec]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            out.append(r)
            if tien_trinh:
                tien_trinh(i, len(futs), r.ma)
    return out


def _so(x, nd=2):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(x, nd)


def bang(ket_qua: list[KetQuaMa], tam: str = "D", von: float = 100e6) -> pd.DataFrame:
    """Bảng xếp hạng: Mua mạnh → Mua → Chờ về vùng mua → Theo dõi → Không mua; trong cùng mức xếp theo R:R."""
    rows = []
    for r in ket_qua:
        if not r.kn:
            continue
        kn = r.kn[tam]
        lai = K.ke_hoach_von(kn, von)
        rows.append({
            "Mã": r.ma, "Sàn": du_lieu.SAN.get(r.san, r.san), "Tên": r.ten,
            "Khuyến nghị": kn.muc, "Hạng": kn.hang, "Điểm": round(kn.diem),
            "Giá": kn.gia, "% phiên": _so(r.thay_doi * 100, 1),
            "Vùng mua": f"{kn.vung.thap:,.0f} – {kn.vung.cao:,.0f}" if kn.vung else "",
            "Giá mua": kn.gia_mua, "Cắt lỗ": kn.cat_lo, "Chốt lời": kn.chot_loi1, "Chốt lời 2": kn.chot_loi2,
            "R:R": _so(kn.rr, 2),
            "% lãi": _so(lai["tp1"]["pct"] * 100, 1) if lai.get("tp1") else None,
            "% lỗ": _so(lai["sl"]["pct"] * 100, 1) if lai.get("sl") else None,
            "Tiền lãi": _so(lai["tp1"]["lai"], 0) if lai.get("tp1") else None,
            "Tiền lỗ": _so(lai["sl"]["lai"], 0) if lai.get("sl") else None,
            "Số CP": lai["tp1"]["so_cp"] if lai.get("tp1") else None,
            "Cách vùng mua %": _so(kn.cach_vung_pct * 100, 1) if kn.cach_vung_pct is not None else None,
            "GTGD (tỷ)": _so(r.gtgd / 1e9, 1),
            "Lý do": " · ".join(kn.ly_do),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["_rr"] = df["R:R"].fillna(0)
    df = df.sort_values(["Hạng", "_rr", "Điểm"], ascending=False).drop(columns="_rr")
    return df.reset_index(drop=True)


def thong_ke(ket_qua: list[KetQuaMa]) -> dict:
    co = [r for r in ket_qua if r.kn]
    return {"tong": len(ket_qua), "phan_tich": len(co),
            "thanh_khoan_thap": sum(r.loi == "Thanh khoản thấp" for r in ket_qua),
            "loi": sum(bool(r.loi) and r.loi != "Thanh khoản thấp" for r in ket_qua),
            "tang": sum(r.kq.xu_huong == 1 for r in co),
            "giam": sum(r.kq.xu_huong == -1 for r in co)}


def ghi(thu_muc, ket_qua: list[KetQuaMa], von: float = 100e6) -> dict:
    """Ghi khuyen_nghi_D/W (.csv, .xlsx), khuyen_nghi.md và thi_truong.json (dùng cho trang demo)."""
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)
    luc = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")
    bangs = {tam: bang(ket_qua, tam, von) for tam in ("D", "W")}
    with pd.ExcelWriter(thu_muc / "khuyen_nghi.xlsx") as w:
        for tam, b in bangs.items():
            b.to_excel(w, sheet_name="Ngắn hạn (D)" if tam == "D" else "Trung hạn (W)", index=False)
    md = [f"# Khuyến nghị toàn thị trường – {luc}", ""]
    tk = thong_ke(ket_qua)
    md.append(f"Quét {tk['tong']} mã · phân tích {tk['phan_tich']} mã đủ thanh khoản · "
              f"{tk['tang']} mã xu hướng tăng, {tk['giam']} mã giảm.")
    for tam, b in bangs.items():
        md += ["", f"## {'Ngắn hạn – khung ngày (1–3 tháng)' if tam == 'D' else 'Trung hạn – khung tuần (3–9 tháng)'}", "",
               "| Mã | Sàn | Khuyến nghị | Giá | Vùng mua | Cắt lỗ | Chốt lời | R:R | % lãi |",
               "|---|---|---|---:|---|---:|---:|---:|---:|"]
        for _, x in b[b["Hạng"] >= 2].head(30).iterrows():
            md.append(f"| {x['Mã']} | {x['Sàn']} | {x['Khuyến nghị']} | {x['Giá']:,.0f} | {x['Vùng mua']} | "
                      f"{x['Cắt lỗ'] or 0:,.0f} | {x['Chốt lời'] or 0:,.0f} | {x['R:R'] or '–'} | {x['% lãi'] or '–'} |")
    md += ["", "> Công cụ chỉ hỗ trợ phân tích kỹ thuật, không phải lời khuyên đầu tư.", ""]
    (thu_muc / "khuyen_nghi.md").write_text("\n".join(md), encoding="utf-8")
    # giá 120 phiên gần nhất của các mã đáng chú ý (để vẽ biểu đồ nhỏ)
    chu_y = set()
    for b in bangs.values():
        if not b.empty:
            chu_y |= set(b[b["Hạng"] >= 2]["Mã"].head(60))
    gia = {}
    for r in ket_qua:
        if r.ma in chu_y and r.kq is not None:
            d = r.kq.frames["D"].iloc[-120:]
            gia[r.ma] = {"t": [x.strftime("%d/%m") for x in d.index], "c": [round(v, 2) for v in d["close"]]}
    data = {"luc": luc, "thong_ke": tk, "von": von, "gia": gia,
            "D": json.loads(bangs["D"].to_json(orient="records", force_ascii=False)),
            "W": json.loads(bangs["W"].to_json(orient="records", force_ascii=False))}
    (thu_muc / "thi_truong.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data
