"""Quét toàn thị trường chứng khoán VN (HOSE, HNX, UPCoM): khuyến nghị mua, tín hiệu bán ở đỉnh,
sức mạnh ngành và xếp hạng."""
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
    nganh: str = "Khác"
    hieu_suat_20: float = 0.0   # % thay đổi 20 phiên
    dinh: dict = None           # {"D": TinHieuDinh, "W": TinHieuDinh}


def phan_tich_df(ma: str, df: pd.DataFrame, loai: str = "vn"):
    """Phân tích đủ M/W/D từ dữ liệu ngày, trả về (KetQua, {tầm: KhuyenNghi})."""
    frames = {"M": du_lieu.resample(df, "M"), "W": du_lieu.resample(df, "W"), "D": df.iloc[-600:]}
    ds = [phan_tich.phan_tich_khung(f, k) for k, f in frames.items()]
    kq = phan_tich.tong_hop(ma, loai, ds)
    kq.frames = frames
    return kq, {tam: K.khuyen_nghi(kq, tam, loai) for tam in ("D", "W")}


def _mot_ma(ma, san, ten, gtgd_min, nganh="Khác"):
    r = KetQuaMa(ma, san, ten, nganh=nganh or "Khác")
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
            r.dinh = {tam: K.tin_hieu_dinh(r.kq, tam) for tam in ("D", "W")}
            if len(df) > 21:
                r.hieu_suat_20 = float(df["close"].iloc[-1] / df["close"].iloc[-21] - 1)
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
        futs = [ex.submit(_mot_ma, x.ma, x.san, x.ten, gtgd_min, getattr(x, "nganh", "Khác")) for x in viec]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            out.append(r)
            if tien_trinh:
                tien_trinh(i, len(futs), r.ma)
    ap_dung_nganh(out)
    return out


# ------------------------------------------------------------------------- ngành
def suc_manh_nganh(ket_qua: list[KetQuaMa], tam: str = "D") -> pd.DataFrame:
    """Xếp hạng ngành: % mã tăng/giảm, điểm TB, hiệu suất 20 phiên, số mã Mua/Bán, dòng tiền."""
    rows = {}
    for r in ket_qua:
        if not r.kn:
            continue
        g = rows.setdefault(r.nganh, {"diem": [], "tang": 0, "giam": 0, "hs": [], "mua": 0, "ban": 0, "gtgd": 0.0})
        g["diem"].append(r.kn[tam].diem)
        g["tang"] += r.kq.xu_huong == 1
        g["giam"] += r.kq.xu_huong == -1
        g["hs"].append(r.hieu_suat_20)
        g["mua"] += r.kn[tam].hang >= 3
        g["ban"] += bool(r.dinh) and r.dinh[tam].hang >= 2
        g["gtgd"] += r.gtgd
    out = []
    for ten, g in rows.items():
        n = len(g["diem"])
        diem_tb = sum(g["diem"]) / n
        hs = float(pd.Series(g["hs"]).median())
        pt, pg = g["tang"] / n, g["giam"] / n
        out.append({"Ngành": ten, "Số mã": n, "% mã tăng": round(pt * 100), "% mã giảm": round(pg * 100),
                    "Điểm TB": round(diem_tb, 1), "Hiệu suất 20 phiên %": round(hs * 100, 1),
                    "Số mã Mua": g["mua"], "Số mã Bán": g["ban"], "GTGD (tỷ)": round(g["gtgd"] / 1e9),
                    "Sức mạnh": round(0.5 * diem_tb + 30 * (pt - pg) + 100 * hs, 1)})
    df = pd.DataFrame(out)
    if df.empty:
        return df
    df = df.sort_values("Sức mạnh", ascending=False).reset_index(drop=True)
    n = len(df)
    df["Xếp loại"] = ["Mạnh" if i < n / 3 else ("Yếu" if i >= 2 * n / 3 else "Trung bình") for i in range(n)]
    df.insert(0, "Hạng", range(1, n + 1))
    return df


def ap_dung_nganh(ket_qua: list[KetQuaMa]):
    """Ưu tiên mã thuộc ngành mạnh: +10 điểm (ngành yếu −10). Ngành yếu: hạ 'Mua mạnh' xuống 'Mua'."""
    for tam in ("D", "W"):
        sm = suc_manh_nganh(ket_qua, tam)
        if sm.empty:
            continue
        loai = dict(zip(sm["Ngành"], sm["Xếp loại"]))
        for r in ket_qua:
            if not r.kn:
                continue
            kn = r.kn[tam]
            xl = loai.get(r.nganh, "Trung bình")
            kn.nganh_xep_loai = xl
            if xl == "Mạnh":
                kn.diem = round(kn.diem + 10, 1)
                kn.ly_do.append(f"Ngành {r.nganh} đang mạnh (+10 điểm).")
            elif xl == "Yếu":
                kn.diem = round(kn.diem - 10, 1)
                kn.ly_do.append(f"Ngành {r.nganh} đang yếu (−10 điểm).")
                if kn.muc == "Mua mạnh":
                    kn.muc = "Mua"
                    kn.ly_do.append("Hạ từ 'Mua mạnh' xuống 'Mua' vì ngành yếu.")


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
            "Mã": r.ma, "Sàn": du_lieu.SAN.get(r.san, r.san), "Tên": r.ten, "Ngành": r.nganh,
            "Ngành mạnh/yếu": getattr(kn, "nganh_xep_loai", ""),
            "Khuyến nghị": kn.muc, "Hạng": kn.hang, "Điểm": round(kn.diem),
            "Tín hiệu đỉnh": r.dinh[tam].muc if r.dinh else "",
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
    df["_ng"] = df["Ngành mạnh/yếu"].map({"Mạnh": 1, "Yếu": -1}).fillna(0)
    df = df.sort_values(["Hạng", "_ng", "_rr", "Điểm"], ascending=False).drop(columns=["_rr", "_ng"])
    return df.reset_index(drop=True)


def bang_ban(ket_qua: list[KetQuaMa], tam: str = "D") -> pd.DataFrame:
    """Bảng 'Nên bán ở đỉnh': Bán mạnh → Chốt lời dần → Theo dõi đỉnh (bỏ mã chưa có đỉnh)."""
    rows = []
    for r in ket_qua:
        if not r.dinh:
            continue
        t = r.dinh[tam]
        if t.hang == 0:
            continue
        rows.append({
            "Mã": r.ma, "Sàn": du_lieu.SAN.get(r.san, r.san), "Tên": r.ten, "Ngành": r.nganh,
            "Tín hiệu": t.muc, "Hạng": t.hang, "Số dấu hiệu": t.so_dau_hieu, "Giá": t.gia,
            "% phiên": _so(r.thay_doi * 100, 1), "% 20 phiên": _so(r.hieu_suat_20 * 100, 1),
            "Vùng bán": f"{t.vung_ban[0]:,.0f} – {t.vung_ban[1]:,.0f}" if t.vung_ban else "",
            "Giá bán": t.gia_ban, "Đỉnh gần nhất": t.gia_dinh, "GTGD (tỷ)": _so(r.gtgd / 1e9, 1),
            "Dấu hiệu": " · ".join(t.dau_hieu),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["Hạng", "Số dấu hiệu", "GTGD (tỷ)"], ascending=False).reset_index(drop=True)


def thong_ke(ket_qua: list[KetQuaMa]) -> dict:
    co = [r for r in ket_qua if r.kn]
    return {"tong": len(ket_qua), "phan_tich": len(co),
            "thanh_khoan_thap": sum(r.loi == "Thanh khoản thấp" for r in ket_qua),
            "loi": sum(bool(r.loi) and r.loi != "Thanh khoản thấp" for r in ket_qua),
            "tang": sum(r.kq.xu_huong == 1 for r in co),
            "giam": sum(r.kq.xu_huong == -1 for r in co),
            "ban": sum(bool(r.dinh) and r.dinh["D"].hang >= 2 for r in co)}


def ghi(thu_muc, ket_qua: list[KetQuaMa], von: float = 100e6) -> dict:
    """Ghi khuyen_nghi_D/W (.csv, .xlsx), khuyen_nghi.md và thi_truong.json (dùng cho trang demo)."""
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)
    luc = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")
    bangs = {tam: bang(ket_qua, tam, von) for tam in ("D", "W")}
    bans = {tam: bang_ban(ket_qua, tam) for tam in ("D", "W")}
    nganhs = {tam: suc_manh_nganh(ket_qua, tam) for tam in ("D", "W")}
    with pd.ExcelWriter(thu_muc / "khuyen_nghi.xlsx") as w:
        for tam, b in bangs.items():
            b.to_excel(w, sheet_name="Mua ngắn hạn (D)" if tam == "D" else "Mua trung hạn (W)", index=False)
        for tam, b in bans.items():
            b.to_excel(w, sheet_name="Bán đỉnh (D)" if tam == "D" else "Bán đỉnh (W)", index=False)
        nganhs["D"].to_excel(w, sheet_name="Sức mạnh ngành", index=False)
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
    for tam, b in bans.items():
        md += ["", f"## Nên bán ở đỉnh – {'khung ngày' if tam == 'D' else 'khung tuần'}", "",
               "| Mã | Ngành | Tín hiệu | Giá | Vùng bán | Dấu hiệu |", "|---|---|---|---:|---|---|"]
        for _, x in (b[b["Hạng"] >= 2].head(30).iterrows() if not b.empty else []):
            md.append(f"| {x['Mã']} | {x['Ngành']} | {x['Tín hiệu']} | {x['Giá']:,.0f} | {x['Vùng bán']} | "
                      f"{x['Dấu hiệu']} |")
    ng = nganhs["D"]
    if not ng.empty:
        md += ["", "## Sức mạnh ngành", "", "| # | Ngành | Xếp loại | % mã tăng | Hiệu suất 20 phiên | Mua | Bán |",
               "|---:|---|---|---:|---:|---:|---:|"]
        for _, x in ng.iterrows():
            md.append(f"| {x['Hạng']} | {x['Ngành']} | {x['Xếp loại']} | {x['% mã tăng']}% | "
                      f"{x['Hiệu suất 20 phiên %']:+.1f}% | {x['Số mã Mua']} | {x['Số mã Bán']} |")
    md += ["", "> Công cụ chỉ hỗ trợ phân tích kỹ thuật, không phải lời khuyên đầu tư.", ""]
    (thu_muc / "khuyen_nghi.md").write_text("\n".join(md), encoding="utf-8")
    # giá 120 phiên gần nhất của các mã đáng chú ý (để vẽ biểu đồ nhỏ)
    chu_y = set()
    for b in bangs.values():
        if not b.empty:
            chu_y |= set(b[b["Hạng"] >= 2]["Mã"].head(60))
    for b in bans.values():
        if not b.empty:
            chu_y |= set(b["Mã"].head(40))
    gia = {}
    for r in ket_qua:
        if r.ma in chu_y and r.kq is not None:
            d = r.kq.frames["D"].iloc[-120:]
            gia[r.ma] = {"t": [x.strftime("%d/%m") for x in d.index], "c": [round(v, 2) for v in d["close"]]}
    data = {"luc": luc, "thong_ke": tk, "von": von, "gia": gia,
            **{tam: json.loads(bangs[tam].to_json(orient="records", force_ascii=False)) for tam in ("D", "W")},
            **{f"ban_{tam}": json.loads(bans[tam].to_json(orient="records", force_ascii=False)) for tam in ("D", "W")},
            **{f"nganh_{tam}": json.loads(nganhs[tam].to_json(orient="records", force_ascii=False))
               for tam in ("D", "W")}}
    (thu_muc / "thi_truong.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data
