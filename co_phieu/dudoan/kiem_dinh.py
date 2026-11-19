"""Kiểm định (backtest) độ chính xác tín hiệu Mua và Bán ở đỉnh trên dữ liệu quá khứ.

Tại mỗi điểm thời gian i (cách nhau `buoc` phiên), công cụ CHỈ được thấy dữ liệu đến hết phiên i,
rồi so tín hiệu với diễn biến giá sau đó:
  • Mua / Mua mạnh: mua giá mở cửa phiên i+1, thoát khi chạm cắt lỗ (ưu tiên nếu cùng phiên chạm cả hai),
    chạm chốt lời, hoặc hết `giu` phiên. Lãi đã trừ phí mua 0,15%, phí bán 0,15%, thuế 0,1%.
  • Chờ về vùng mua: đặt lệnh chờ ở giá mua đề xuất trong 20 phiên; khớp thì xử lý như trên.
  • Bán ở đỉnh (Chốt lời dần / Bán mạnh): "đúng" nếu giá 20 phiên sau thấp hơn giá lúc báo.
  • Mốc so sánh: mua bất kỳ lúc nào (cùng các điểm thời gian) và giữ 20 / 60 phiên.
Lưu ý: chỉ dùng các mã đang niêm yết & đủ thanh khoản hôm nay (thiên lệch sống sót).
"""
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from . import co_ban, du_lieu, khuyen_nghi as K, quet

CHI_PHI = (1 + K.PHI_MUA), (1 - K.PHI_BAN - K.THUE_BAN)


def _giao_dich(o, h, l, c, j0, gia_vao, sl, tp, het):
    """Giả lập 1 lệnh mua từ phiên j0 (đã khớp ở gia_vao). Trả về (lãi ròng, kết quả, số phiên giữ)."""
    for j in range(j0, het + 1):
        if l[j] <= sl:
            ra, kq = min(o[j], sl) if j > j0 else sl, "cắt lỗ"
            return ra * CHI_PHI[1] / (gia_vao * CHI_PHI[0]) - 1, kq, j - j0
        if h[j] >= tp:
            ra = max(o[j], tp) if j > j0 else tp
            return ra * CHI_PHI[1] / (gia_vao * CHI_PHI[0]) - 1, "chốt lời", j - j0
    return c[het] * CHI_PHI[1] / (gia_vao * CHI_PHI[0]) - 1, "hết hạn", het - j0


def kiem_dinh_ma(ma: str, df: pd.DataFrame, buoc: int = 5, so_diem: int = 100, giu: int = 60,
                 quy: pd.DataFrame | None = None, ho_so: dict | None = None) -> dict:
    """`quy`, `ho_so`: dữ liệu BCTC quý & hồ sơ (nếu có) để chấm sức khỏe tài chính TẠI từng thời điểm."""
    o, h, l, c = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    n = len(df)
    out = {"ma": ma, "mua": [], "cho": [], "ban": [], "theo_doi_dinh": [], "goc": [], "khong_mua": [], "timing": []}
    start = max(260, n - giu - 1 - buoc * so_diem)
    for i in range(start, n - giu - 1, buoc):
        try:
            kq, kn = quet.phan_tich_df(ma, df.iloc[: i + 1])
            dinh = K.tin_hieu_dinh(kq, "D")
        except Exception:
            continue
        sk = None
        if quy is not None and not quy.empty:
            try:
                s_ = co_ban.suc_khoe(ma, ngay=df.index[i], gia=c[i], quy=quy,
                                     la_ngan_hang=bool((ho_so or {}).get("isBank")),
                                     so_cp=(ho_so or {}).get("issueShare"))
                sk = (s_.tong, bool(s_.chi_tiet.get("ln_ttm") is not None and s_.chi_tiet["ln_ttm"] < 0)) \
                    if s_.du_lieu else None
            except Exception:
                sk = None
        r20, r60 = c[i + 20] / c[i] - 1, c[i + 60] / c[i] - 1
        out["goc"].append((r20, r60, c[i + 60] * CHI_PHI[1] / (o[i + 1] * CHI_PHI[0]) - 1, sk))
        k = kn["D"]
        if k.muc in ("Mua", "Mua mạnh") and k.cat_lo and k.chot_loi1:
            vao = o[i + 1]
            if k.cat_lo < vao < k.chot_loi1:
                lai, kqua, ngay = _giao_dich(o, h, l, c, i + 1, vao, k.cat_lo, k.chot_loi1, i + giu)
                out["mua"].append((k.muc, lai, kqua, ngay, r20, sk))
                tg = k.thoi_gian
                if tg is not None and tg.thuong is not None:
                    out["timing"].append((tg.som, tg.thuong, tg.muon, tg.fibo, ngay + 1, kqua))
        elif k.muc == "Chờ về vùng mua" and k.gia_mua and k.cat_lo and k.chot_loi1:
            for j in range(i + 1, min(i + 21, n - 1)):
                if l[j] <= k.gia_mua:
                    vao = min(o[j], k.gia_mua)
                    lai, kqua, ngay = _giao_dich(o, h, l, c, j, vao, k.cat_lo, k.chot_loi1, min(j + giu, n - 1))
                    out["cho"].append((lai, kqua, ngay, sk))
                    break
        elif k.muc == "Không mua":
            out["khong_mua"].append(r20)
        if dinh.hang >= 2:
            out["ban"].append((dinh.muc, r20, c[i + 10] / c[i] - 1, float(h[i + 1:i + 21].max() / c[i] - 1), sk))
        elif dinh.hang == 1:
            out["theo_doi_dinh"].append(r20)
    return out


def _tai(ma, lay_co_ban=True):
    try:
        df = du_lieu._vci(ma, "D")
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


def _lenh(x):
    """Chuẩn hoá: (lãi, kết quả, số phiên, sức khỏe) cho cả lệnh Mua (6 phần tử) và lệnh chờ (4)."""
    return (x[1], x[2], x[3], x[5]) if len(x) == 6 else (x[0], x[1], x[2], x[3])


def _tom_tat_lenh(ds):
    if not ds:
        return {"so_lenh": 0}
    ds = [_lenh(x) for x in ds]
    lai = np.array([x[0] for x in ds])
    kq = [x[1] for x in ds]
    return {"so_lenh": len(ds), "ti_le_thang": float((lai > 0).mean()), "lai_tb": float(lai.mean()),
            "lai_trung_vi": float(np.median(lai)), "cham_tp": kq.count("chốt lời") / len(ds),
            "cham_sl": kq.count("cắt lỗ") / len(ds), "het_han": kq.count("hết hạn") / len(ds),
            "ngay_giu_tb": float(np.mean([x[2] for x in ds]))}


NHOM_SK = [("Sức khỏe ≥ 4 & đang lãi", lambda sk: sk and not sk[1] and sk[0] >= 4),
           ("Sức khỏe 3 – 3,9", lambda sk: sk and not sk[1] and 3 <= sk[0] < 4),
           ("Sức khỏe < 3 hoặc đang lỗ", lambda sk: sk and (sk[1] or sk[0] < 3)),
           ("Không đủ dữ liệu BCTC", lambda sk: sk is None)]


def tong_hop(ket_qua: list[dict]) -> dict:
    mua = [x for r in ket_qua for x in r["mua"]]
    goc = np.array([x[:3] for r in ket_qua for x in r["goc"]], dtype=float).reshape(-1, 3)
    ban = [x for r in ket_qua for x in r["ban"]]
    td = np.array([x for r in ket_qua for x in r["theo_doi_dinh"]])
    km = np.array([x for r in ket_qua for x in r["khong_mua"]])
    res = {
        "so_ma": len(ket_qua), "so_diem": int(len(goc)),
        "goc": {"r20_tb": float(goc[:, 0].mean()), "ti_le_tang_20": float((goc[:, 0] > 0).mean()),
                "mua_giu_60_tb": float(goc[:, 2].mean()), "ti_le_lai_giu_60": float((goc[:, 2] > 0).mean())}
        if len(goc) else {},
        "mua": _tom_tat_lenh(mua),
        "mua_manh": _tom_tat_lenh([x for x in mua if x[0] == "Mua mạnh"]),
        "mua_thuong": _tom_tat_lenh([x for x in mua if x[0] == "Mua"]),
        "cho": _tom_tat_lenh([x for r in ket_qua for x in r["cho"]]),
        "khong_mua": {"so": int(len(km)), "r20_tb": float(km.mean()) if len(km) else None,
                      "ti_le_tang_20": float((km > 0).mean()) if len(km) else None},
    }
    for ten, loc in (("ban", lambda x: True), ("ban_manh", lambda x: x[0] == "Bán mạnh"),
                     ("chot_loi_dan", lambda x: x[0] == "Chốt lời dần")):
        ds = [x for x in ban if loc(x)]
        if ds:
            r20 = np.array([x[1] for x in ds])
            res[ten] = {"so": len(ds), "ti_le_dung_20": float((r20 < 0).mean()), "r20_tb": float(r20.mean()),
                        "r10_tb": float(np.mean([x[2] for x in ds])),
                        "con_tang_them_tb": float(np.mean([x[3] for x in ds]))}
        else:
            res[ten] = {"so": 0}
    res["theo_doi_dinh"] = {"so": int(len(td)), "ti_le_dung_20": float((td < 0).mean()) if len(td) else None,
                            "r20_tb": float(td.mean()) if len(td) else None}
    # Timing: lệnh chạm chốt lời có nằm trong khoảng ngày dự kiến không
    tm = [x for r in ket_qua for x in r.get("timing", []) if x[5] == "chốt lời"]
    if tm:
        that = np.array([x[4] for x in tm], float)
        som, thuong, muon = (np.array([x[j] for x in tm], float) for j in (0, 1, 2))
        fibo = [x[3] for x in tm]
        f_gan = np.array([min(f, key=lambda v: abs(v - a)) if f else np.nan for f, a in zip(fibo, that)], float)
        f_1 = np.array([f[1] if f else np.nan for f in fibo], float)
        res["timing"] = {
            "so": len(tm), "phien_thuc_te_tv": float(np.median(that)),
            "toc_do_trong_khoang": float(((that >= np.floor(som)) & (that <= np.ceil(muon))).mean()),
            "toc_do_sai_so_tv": float(np.median(np.abs(that - thuong))),
            "fibo1_sai_so_tv": float(np.nanmedian(np.abs(that - f_1))),
            "fibo_khoang": float(np.nanmean((that >= np.floor([f[0] if f else np.nan for f in fibo]))
                                            & (that <= np.ceil([f[2] if f else np.nan for f in fibo])))),
            "fibo_gan_nhat_sai_so_tv": float(np.nanmedian(np.abs(that - f_gan))),
        }
    # Phân theo sức khỏe tài chính tại thời điểm báo tín hiệu
    cho = [x for r in ket_qua for x in r["cho"]]
    goc_all = [x for r in ket_qua for x in r["goc"]]
    res["theo_suc_khoe"] = []
    for ten, loc in NHOM_SK:
        g = [x for x in goc_all if loc(x[3] if len(x) > 3 else None)]
        b = [x for x in ban if loc(x[4] if len(x) > 4 else None)]
        rb = np.array([x[1] for x in b])
        res["theo_suc_khoe"].append({
            "nhom": ten,
            "mua": _tom_tat_lenh([x for x in mua if loc(x[5])]),
            "cho": _tom_tat_lenh([x for x in cho if loc(x[3])]),
            "goc_giu_60": float(np.mean([x[2] for x in g])) if g else None,
            "goc_so": len(g),
            "ban_so": len(b), "ban_dung": float((rb < 0).mean()) if len(b) else None,
        })
    return res


def chay(ds_ma: list[str], buoc: int = 5, so_diem: int = 100, so_tien_trinh: int = 4, tien_trinh=None) -> dict:
    with ThreadPoolExecutor(6) as ex:
        data = [x for x in ex.map(_tai, ds_ma) if x[1] is not None and len(x[1]) > 400]
    ket_qua = []
    with ProcessPoolExecutor(so_tien_trinh) as ex:
        futs = [ex.submit(kiem_dinh_ma, m, d, buoc, so_diem, 60, q, h) for m, d, q, h in data]
        for i, f in enumerate(futs, 1):
            try:
                ket_qua.append(f.result())
            except Exception:
                pass
            if tien_trinh:
                tien_trinh(i, len(futs))
    return {"tong": tong_hop(ket_qua), "chi_tiet": ket_qua}


def _p(x):
    return "–" if x is None else f"{x * 100:+.1f}%"


def _pp(x):
    return "–" if x is None else f"{x * 100:.0f}%"


def markdown(t: dict, luc: str) -> str:
    g = t["goc"]
    dong = [f"# Kiểm định tín hiệu trên dữ liệu quá khứ – {luc}", "",
            f"{t['so_ma']} mã đủ thanh khoản, {t['so_diem']:,} điểm thời gian (mỗi 5 phiên, ~2 năm gần nhất). "
            "Chỉ dùng dữ liệu đến thời điểm báo tín hiệu.", "",
            "## Mốc so sánh (mua bất kỳ lúc nào)",
            f"- Giá tăng sau 20 phiên: {_pp(g.get('ti_le_tang_20'))} số lần, thay đổi TB {_p(g.get('r20_tb'))}",
            f"- Mua rồi giữ 60 phiên (sau phí): lãi {_pp(g.get('ti_le_lai_giu_60'))} số lần, TB {_p(g.get('mua_giu_60_tb'))}",
            "", "## Tín hiệu MUA (ngắn hạn, khung ngày)",
            "| Loại | Số lệnh | Tỉ lệ thắng | Lãi TB/lệnh | Trung vị | Chạm chốt lời | Chạm cắt lỗ | Hết 60 phiên | Giữ TB |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for ten, k in (("Mua mạnh", "mua_manh"), ("Mua", "mua_thuong"), ("Tất cả Mua", "mua"),
                   ("Chờ về vùng mua (lệnh chờ khớp)", "cho")):
        x = t[k]
        if x["so_lenh"]:
            dong.append(f"| {ten} | {x['so_lenh']} | {_pp(x['ti_le_thang'])} | {_p(x['lai_tb'])} | "
                        f"{_p(x['lai_trung_vi'])} | {_pp(x['cham_tp'])} | {_pp(x['cham_sl'])} | "
                        f"{_pp(x['het_han'])} | {x['ngay_giu_tb']:.0f} phiên |")
        else:
            dong.append(f"| {ten} | 0 | – | – | – | – | – | – | – |")
    km = t["khong_mua"]
    dong += ["", f"Khi báo **Không mua** ({km['so']:,} lần): giá tăng sau 20 phiên {_pp(km['ti_le_tang_20'])} số lần, "
             f"TB {_p(km['r20_tb'])}.", "",
             "## Tín hiệu BÁN Ở ĐỈNH (khung ngày)",
             "| Loại | Số lần | Đúng (giá thấp hơn sau 20 phiên) | Thay đổi TB 10 phiên | 20 phiên | Còn tăng thêm tối đa TB |",
             "|---|---:|---:|---:|---:|---:|"]
    for ten, k in (("Bán mạnh", "ban_manh"), ("Chốt lời dần", "chot_loi_dan"), ("Tất cả", "ban")):
        x = t[k]
        if x["so"]:
            dong.append(f"| {ten} | {x['so']} | {_pp(x['ti_le_dung_20'])} | {_p(x['r10_tb'])} | {_p(x['r20_tb'])} | "
                        f"{_p(x['con_tang_them_tb'])} |")
        else:
            dong.append(f"| {ten} | 0 | – | – | – | – |")
    if t.get("theo_suc_khoe"):
        dong += ["", "## Kết hợp sức khỏe tài chính (chấm TẠI thời điểm báo, chỉ dùng BCTC đã công bố)",
                 "| Nhóm | Mua bất kỳ, giữ 60 phiên | Tín hiệu Mua: số lệnh | thắng | lãi TB | Lệnh chờ: số | thắng | lãi TB | Bán ở đỉnh: số | đúng |",
                 "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for x in t["theo_suc_khoe"]:
            m, c_ = x["mua"], x["cho"]
            dong.append(f"| {x['nhom']} | {_p(x['goc_giu_60'])} ({x['goc_so']:,}) | {m['so_lenh']} | "
                        f"{_pp(m.get('ti_le_thang'))} | {_p(m.get('lai_tb'))} | {c_['so_lenh']} | "
                        f"{_pp(c_.get('ti_le_thang'))} | {_p(c_.get('lai_tb'))} | {x['ban_so']} | {_pp(x['ban_dung'])} |")
    if t.get("timing"):
        x = t["timing"]
        dong += ["", "## Timing – dự kiến ngày chốt lời (các lệnh Mua chạm chốt lời)",
                 f"- Số lệnh: {x['so']}, thực tế trung vị {x['phien_thuc_te_tv']:.0f} phiên.",
                 f"- **Theo tốc độ nhịp cũ**: {_pp(x['toc_do_trong_khoang'])} lệnh chạm chốt lời trong khoảng sớm–muộn; "
                 f"sai số trung vị so với mốc 'thường' {x['toc_do_sai_so_tv']:.0f} phiên.",
                 f"- **Theo Fibonacci thời gian**: {_pp(x['fibo_khoang'])} lệnh trong khoảng 0.618–1.618; "
                 f"sai số trung vị với mốc 1.0: {x['fibo1_sai_so_tv']:.0f} phiên."]
    td = t["theo_doi_dinh"]
    dong += ["", f"Theo dõi đỉnh ({td['so']} lần): đúng {_pp(td['ti_le_dung_20'])}, TB 20 phiên {_p(td['r20_tb'])}.",
             "", "> Lưu ý: chỉ gồm các mã còn niêm yết và đủ thanh khoản hôm nay (thiên lệch sống sót); "
             "kết quả quá khứ không đảm bảo tương lai.", ""]
    return "\n".join(dong)


def ghi(thu_muc, res: dict, luc: str):
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)
    (thu_muc / "kiem_dinh.md").write_text(markdown(res["tong"], luc), encoding="utf-8")
    (thu_muc / "kiem_dinh.json").write_text(json.dumps(res["tong"], ensure_ascii=False, indent=1), encoding="utf-8")
