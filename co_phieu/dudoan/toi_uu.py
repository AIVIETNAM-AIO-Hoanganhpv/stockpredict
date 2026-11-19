"""Tối ưu tham số tín hiệu – có kiểm tra ngoài mẫu (walk-forward).

B1. trich_xuat(): tại mỗi điểm thời gian (mỗi `buoc` phiên) của mỗi mã, CHỈ dùng dữ liệu đến hôm đó,
    lưu lại: phiếu từng chỉ báo (khung D, W), vùng mua, cắt lỗ/chốt lời mặc định, ATR, đáy gần nhất,
    các dấu hiệu đỉnh, sức khỏe tài chính.
B2. mo_phong(tham_so): giả lập giao dịch rất nhanh trên dữ liệu đã trích xuất.
B3. tim_kiem(): thử nhiều bộ tham số trên giai đoạn HUẤN LUYỆN, chọn bộ tốt nhất (đủ số lệnh),
    rồi chấm lại trên giai đoạn KIỂM TRA (chưa từng dùng để chọn).
"""
import itertools
import math
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from . import chi_bao, co_ban, du_lieu, khuyen_nghi as K, quet

PHI = (1 + K.PHI_MUA), (1 - K.PHI_BAN - K.THUE_BAN)
DAU_HIEU_DINH = {"fibo": "Fibonacci mở rộng", "stoch": "Stoch quá mua", "mfi": "MFI quá mua",
                 "phan_ky": "Phân kỳ giảm", "quet": "Quét thanh khoản", "cung": "vùng cung",
                 "choch": "CHoCH giảm", "nen": ("Nến", "Mây đen"), "nhip": "nhịp tăng"}
TEN_PHIEU = ["Đỉnh/đáy", "Vị thế giá/MA20", "MACD", "Heikin Ashi", "Stochastic", "MFI", "ADX",
             "SMC cấu trúc", "SMC vùng OB/FVG", "Quét thanh khoản", "ICT OTE", "ICT Premium/Discount"]


# ------------------------------------------------------------------------- B1: trích xuất
def _phieu(kqk):
    """{tên: (giá trị, trọng số)} của một khung."""
    out = {}
    for v in kqk.votes:
        out[v.ten] = (v.gia_tri, v.trong_so)
    return out


def trich_xuat_ma(ma, df, quy=None, ho_so=None, buoc=5, so_diem=180, giu=60, cua_so=1500, gtgd_min=0.0):
    """`so_diem=None`: toàn bộ lịch sử. `cua_so`: số phiên quá khứ dùng để phân tích tại mỗi điểm (giới hạn
    thời gian tính). `gtgd_min`: chỉ xét điểm có GTGD bình quân 20 phiên TẠI THỜI ĐIỂM ĐÓ ≥ ngưỡng (đồng)."""
    rows = []
    n = len(df)
    start = 260 if so_diem is None else max(260, n - giu - 1 - buoc * so_diem)
    adx = chi_bao.adx(df)["adx"].to_numpy()
    atr = chi_bao.atr(df).to_numpy()
    stoch = chi_bao.stoch(df)["k"].to_numpy()
    gtgd = (df["close"] * df["volume"]).rolling(20, min_periods=20).mean().to_numpy()
    for i in range(start, n - 2, buoc):
        if gtgd_min and not (gtgd[i] >= gtgd_min):
            continue
        try:
            kq, kn = quet.phan_tich_df(ma, df.iloc[max(0, i + 1 - cua_so): i + 1])
            dinh = K.tin_hieu_dinh(kq, "D")
        except Exception:
            continue
        kd = next((k for k in kq.khung if k.khung == "D"), None)
        kw = next((k for k in kq.khung if k.khung == "W"), None)
        if kd is None or not kd.votes:
            continue
        k = kn["D"]
        st = kd.cau_truc
        ls = [s.price for s in st.swings if s.kind == "L"] if st else []
        r = {"ma": ma, "i": i, "ngay": df.index[i], "gia": float(df["close"].iloc[i]), "gtgd": float(gtgd[i]),
             "atr": float(atr[i]), "adx": float(adx[i]), "stoch": float(stoch[i]),
             "diem_d": kd.diem, "xh_d": kd.xu_huong, "diem_w": kw.diem if kw else np.nan,
             "xh_w": kw.xu_huong if kw else 0, "muc": k.muc, "diem_kn": k.diem,
             "vung_thap": k.vung.thap if k.vung else np.nan, "vung_cao": k.vung.cao if k.vung else np.nan,
             "gia_mua": k.gia_mua or np.nan, "cat_lo": k.cat_lo or np.nan, "tp1": k.chot_loi1 or np.nan,
             "tp2": k.chot_loi2 or np.nan, "day_gan": ls[-1] if ls else np.nan,
             "dinh_muc": dinh.hang, "dinh_so": dinh.so_dau_hieu}
        for kk, tu in DAU_HIEU_DINH.items():
            tu = tu if isinstance(tu, tuple) else (tu,)
            r["dh_" + kk] = any(any(t in d for t in tu) for d in dinh.dau_hieu)
        pd_ = _phieu(kd)
        for t in TEN_PHIEU:
            v, w = pd_.get(t, (0.0, 0.0))
            r["v_" + t], r["w_" + t] = v, w
        pw = _phieu(kw) if kw else {}
        for t in TEN_PHIEU:
            v, w = pw.get(t, (0.0, 0.0))
            r["vw_" + t], r["ww_" + t] = v, w
        r["adx_w"] = np.nan
        if quy is not None and not quy.empty:
            try:
                sk = co_ban.suc_khoe(ma, ngay=df.index[i], gia=r["gia"], quy=quy,
                                     la_ngan_hang=bool((ho_so or {}).get("isBank")),
                                     so_cp=(ho_so or {}).get("issueShare"))
                r["suc_khoe"] = sk.tong if sk.du_lieu else np.nan
                r["dang_lo"] = bool(sk.du_lieu and (sk.chi_tiet.get("ln_ttm") or 0) < 0)
            except Exception:
                r["suc_khoe"], r["dang_lo"] = np.nan, False
        rows.append(r)
    return pd.DataFrame(rows)


def _tai(ma, so_nen=1300, lay_co_ban=True):
    try:
        df = du_lieu._vci(ma, "D", so_nen=so_nen)
    except Exception:
        return ma, None, None, None
    quy = hs = None
    if lay_co_ban:
        try:
            quy = co_ban.gan_gia_cong_bo(co_ban._chuoi_quy(ma), df)
            hs = co_ban.ho_so_raw(ma)
        except Exception:
            quy = hs = None
    return ma, df, quy, hs


def trich_xuat(ds_ma, so_tien_trinh=4, tien_trinh=None, thu_muc=None, so_nen=1300, **kw):
    """Trích xuất cho nhiều mã. `thu_muc`: lưu kết quả từng mã ngay khi xong (<mã>.pkl) – chạy lại sẽ bỏ
    qua mã đã có, nên bị gián đoạn vẫn làm tiếp được."""
    from pathlib import Path
    thu_muc = Path(thu_muc) if thu_muc else None
    if thu_muc:
        thu_muc.mkdir(parents=True, exist_ok=True)
    phan, gia = [], {}
    con_lai = []
    for m in ds_ma:
        if thu_muc and (thu_muc / f"{m}.pkl").exists():
            f_m, g_m = pd.read_pickle(thu_muc / f"{m}.pkl")
            if f_m is not None:
                phan.append(f_m)
                gia[m] = g_m
        else:
            con_lai.append(m)
    lo = 40                                       # tải & xử lý theo lô để không giữ quá nhiều dữ liệu
    xong = len(ds_ma) - len(con_lai)
    with ProcessPoolExecutor(so_tien_trinh) as ex:
        for b in range(0, len(con_lai), lo):
            with ThreadPoolExecutor(6) as tex:
                data = list(tex.map(lambda m: _tai(m, so_nen), con_lai[b:b + lo]))
            futs = {}
            for m, d, q, h in data:
                if d is None or len(d) < 300:
                    if thu_muc:
                        pd.to_pickle((None, None), thu_muc / f"{m}.pkl")
                    continue
                futs[ex.submit(trich_xuat_ma, m, d, q, h, **kw)] = (m, d[["open", "high", "low", "close"]].to_numpy(np.float32))
            for fu, (m, g_m) in futs.items():
                try:
                    f_m = fu.result()
                except Exception:
                    f_m = None
                if thu_muc:
                    pd.to_pickle((f_m, g_m), thu_muc / f"{m}.pkl")
                if f_m is not None and len(f_m):
                    phan.append(f_m)
                    gia[m] = g_m
            xong += len(data)
            if tien_trinh:
                tien_trinh(xong, len(ds_ma))
    return (pd.concat(phan, ignore_index=True) if phan else pd.DataFrame()), gia


# ------------------------------------------------------------------------- B2: mô phỏng
@dataclass(frozen=True)
class ThamSo:
    trong_so: str = "dong_luong"   # bộ trọng số chỉ báo: goc / xu_huong / dong_luong / smc
    nguong: float = 50.0           # điểm tối thiểu để vào lệnh
    loc_tuan: str = "tang"         # khong / diem_duong / tang
    loc_sk: float = 0.0            # sức khỏe tài chính tối thiểu (0 = không lọc); luôn bỏ DN lỗ nếu > 0
    vao: str = "ngay"              # vung: cần giá trong vùng mua · ngay: mua ngay khi đủ điểm
    stoch_max: float = 100.0       # bỏ qua khi Stoch ≥ ngưỡng (quá mua)
    sl: str = "vung_0.5"           # vung_k: dưới vùng mua k ATR · day_k: dưới đáy gần nhất k ATR · atr_k: giá − k ATR
    tp: str = "r_3"                # fibo / r_k (k lần rủi ro) / khong (chỉ thoát theo thời gian/trailing)
    trailing: float = 0.0          # dời cắt lỗ theo giá cao nhất − k ATR (0 = không)
    giu: int = 60                  # số phiên giữ tối đa
    thoat_dinh: int = 0            # thoát khi có ≥ N dấu hiệu đỉnh (0 = không)


BO_TRONG_SO = {
    "goc": None,
    "xu_huong": {"Đỉnh/đáy": 3, "Vị thế giá/MA20": 2, "MACD": 2, "ADX": 1.5, "SMC cấu trúc": 2.5,
                 "Stochastic": 0.5, "MFI": 0.5, "Heikin Ashi": 0.5},
    "dong_luong": K.TRONG_SO,
    "smc": {"SMC cấu trúc": 3, "SMC vùng OB/FVG": 2, "Quét thanh khoản": 1.5, "ICT OTE": 1.5,
            "ICT Premium/Discount": 1, "Đỉnh/đáy": 1.5},
}


def tinh_diem(f: pd.DataFrame, bo: str, khung="v_") -> np.ndarray:
    """Tính lại điểm khung D (hoặc W) với bộ trọng số khác (chỉ các phiếu đã có)."""
    if BO_TRONG_SO.get(bo) is None:
        return f["diem_d"].to_numpy() if khung == "v_" else f["diem_w"].to_numpy()
    tu, mau = np.zeros(len(f)), np.zeros(len(f))
    ws = khung.replace("v", "w")
    for t in TEN_PHIEU:
        w_goc = f[ws + t].to_numpy()
        w = np.where(w_goc > 0, BO_TRONG_SO[bo].get(t, 0.0), 0.0)
        tu += f[khung + t].to_numpy() * w
        mau += w
    d = np.where(mau > 0, 100 * tu / np.where(mau > 0, mau, 1), 0)
    return np.where(f["adx"].to_numpy() < 20, d * 0.7, d)


def _lenh(g, i0, vao, sl, tp, trailing, atr, het, dinh_tai):
    """Giả lập 1 lệnh từ phiên i0 (đã khớp giá vao). Trả về (lãi ròng, số phiên, lý do thoát)."""
    o, h, l, c = g[:, 0], g[:, 1], g[:, 2], g[:, 3]
    cao = vao
    for j in range(i0, het + 1):
        if trailing > 0:
            sl = max(sl, cao - trailing * atr)
        if l[j] <= sl:
            ra = min(o[j], sl) if j > i0 else sl
            return ra * PHI[1] / (vao * PHI[0]) - 1, j - i0 + 1, "cắt lỗ"
        if tp and h[j] >= tp:
            ra = max(o[j], tp) if j > i0 else tp
            return ra * PHI[1] / (vao * PHI[0]) - 1, j - i0 + 1, "chốt lời"
        cao = max(cao, h[j])
        if dinh_tai and j in dinh_tai and j > i0:
            return c[j] * PHI[1] / (vao * PHI[0]) - 1, j - i0 + 1, "đỉnh"
    return c[het] * PHI[1] / (vao * PHI[0]) - 1, het - i0 + 1, "hết hạn"


def mo_phong(f: pd.DataFrame, gia: dict, p: ThamSo, cache_diem: dict | None = None) -> pd.DataFrame:
    key = p.trong_so
    if cache_diem is not None and key in cache_diem:
        dd, dw = cache_diem[key]
    else:
        dd, dw = tinh_diem(f, key, "v_"), tinh_diem(f, key, "vw_")
        if cache_diem is not None:
            cache_diem[key] = (dd, dw)
    diem = (2 * dd + np.nan_to_num(dw, nan=0)) / 3
    ok = (diem > p.nguong) & (dd > 0) & (f["stoch"].to_numpy() < p.stoch_max)
    if p.loc_tuan == "diem_duong":
        ok &= np.nan_to_num(dw, nan=0) > 0
    elif p.loc_tuan == "tang":
        ok &= f["xh_w"].to_numpy() == 1
    if p.loc_sk > 0 and "suc_khoe" in f:
        ok &= (f["suc_khoe"].fillna(0).to_numpy() >= p.loc_sk) & ~f["dang_lo"].fillna(False).to_numpy().astype(bool)
    if p.vao == "vung":
        ok &= f["gia"].to_numpy() <= f["vung_cao"].to_numpy() + 0.1 * f["atr"].to_numpy()
    out = []
    dinh_idx = {}
    if p.thoat_dinh:
        for ma, g in f[f["dinh_so"] >= p.thoat_dinh].groupby("ma"):
            dinh_idx[ma] = set(g["i"].to_numpy())
    ban_toi = {}                       # không mở lệnh mới khi lệnh trước của cùng mã chưa đóng
    for r in f[ok].itertuples(index=False):
        g = gia.get(r.ma)
        if g is None or r.i + 2 >= len(g) or r.i < ban_toi.get(r.ma, -1):
            continue
        vao = g[r.i + 1, 0]
        atr = r.atr
        loai, k = p.sl.split("_")
        k = float(k)
        if loai == "vung" and not math.isnan(r.vung_thap):
            sl = r.vung_thap - k * atr
        elif loai == "day" and not math.isnan(r.day_gan) and r.day_gan < vao:
            sl = r.day_gan - k * atr
        else:
            sl = vao - max(k, 1.0) * atr
        if not sl < vao:
            continue
        if p.tp == "fibo":
            tp = r.tp1 if not math.isnan(r.tp1) and r.tp1 > vao else vao + 2 * (vao - sl)
        elif p.tp.startswith("r_"):
            tp = vao + float(p.tp[2:]) * (vao - sl)
        else:
            tp = None
        het = min(r.i + p.giu, len(g) - 1)
        lai, ngay, ly_do = _lenh(g, r.i + 1, vao, sl, tp, p.trailing, atr, het, dinh_idx.get(r.ma))
        ban_toi[r.ma] = r.i + ngay
        out.append((r.ma, r.ngay, lai, ngay, ly_do))
    return pd.DataFrame(out, columns=["ma", "ngay", "lai", "ngay_giu", "ly_do"])


def tom_tat(l: pd.DataFrame) -> dict:
    if l.empty:
        return {"so_lenh": 0, "lai_tb": np.nan, "thang": np.nan, "lai_tv": np.nan, "lo_max": np.nan}
    return {"so_lenh": len(l), "lai_tb": l["lai"].mean(), "thang": (l["lai"] > 0).mean(),
            "lai_tv": l["lai"].median(), "lo_max": l["lai"].min(), "giu_tb": l["ngay_giu"].mean(),
            "lai_moi_phien": l["lai"].sum() / max(1, l["ngay_giu"].sum())}


def moc_mua_giu(f: pd.DataFrame, gia: dict, giu=60) -> dict:
    lai = []
    for r in f.itertuples(index=False):
        g = gia.get(r.ma)
        if g is not None and r.i + giu < len(g):
            lai.append(g[r.i + giu, 3] * PHI[1] / (g[r.i + 1, 0] * PHI[0]) - 1)
    a = np.array(lai)
    return {"so": len(a), "lai_tb": float(a.mean()) if len(a) else np.nan, "thang": float((a > 0).mean()) if len(a) else np.nan,
            "lai_moi_phien": float(a.mean() / giu) if len(a) else np.nan}


# ------------------------------------------------------------------------- B3: tìm kiếm
LUOI = {
    "trong_so": ["goc", "xu_huong", "dong_luong", "smc"],
    "nguong": [20, 35, 50],
    "loc_tuan": ["khong", "diem_duong", "tang"],
    "loc_sk": [0.0, 3.5],
    "vao": ["vung", "ngay"],
    "stoch_max": [100.0, 85.0],
    "sl": ["vung_0.5", "vung_1.5", "day_0.5", "atr_2", "atr_3"],
    "tp": ["fibo", "r_2", "r_3", "khong"],
    "trailing": [0.0, 3.0],
    "giu": [30, 60],
    "thoat_dinh": [0, 4],
}


def tim_kiem(f: pd.DataFrame, gia: dict, ngay_chia, so_lenh_min=100, luoi=LUOI, tien_trinh=None):
    """Thử mọi tổ hợp trên giai đoạn huấn luyện (trước ngay_chia). Trả về bảng kết quả xếp theo lãi TB."""
    ngay_chia = pd.Timestamp(ngay_chia)
    f_hl = f[f["ngay"] < ngay_chia].reset_index(drop=True)
    cache = {}
    keys = list(luoi)
    combos = list(itertools.product(*[luoi[k] for k in keys]))
    rows = []
    for j, vals in enumerate(combos, 1):
        p = ThamSo(**dict(zip(keys, vals)))
        if p.tp == "khong" and p.trailing == 0 and p.thoat_dinh == 0 and p.giu == 60:
            pass
        l = mo_phong(f_hl, gia, p, cache)
        t = tom_tat(l)
        rows.append({**asdict(p), **t})
        if tien_trinh and j % 200 == 0:
            tien_trinh(j, len(combos))
    kq = pd.DataFrame(rows)
    kq = kq[kq["so_lenh"] >= so_lenh_min].sort_values("lai_tb", ascending=False).reset_index(drop=True)
    return kq


def kiem_tra(f, gia, p: ThamSo, ngay_chia):
    ngay_chia = pd.Timestamp(ngay_chia)
    out = {}
    for ten, phan in (("huan_luyen", f[f["ngay"] < ngay_chia]), ("kiem_tra", f[f["ngay"] >= ngay_chia])):
        phan = phan.reset_index(drop=True)
        out[ten] = {"tin_hieu": tom_tat(mo_phong(phan, gia, p)), "mua_giu": moc_mua_giu(phan, gia, p.giu),
                    "mua_giu_60": moc_mua_giu(phan, gia, 60)}
    return out
