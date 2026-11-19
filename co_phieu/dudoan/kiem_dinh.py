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

from . import du_lieu, khuyen_nghi as K, quet

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


def kiem_dinh_ma(ma: str, df: pd.DataFrame, buoc: int = 5, so_diem: int = 100, giu: int = 60) -> dict:
    o, h, l, c = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    n = len(df)
    out = {"ma": ma, "mua": [], "cho": [], "ban": [], "theo_doi_dinh": [], "goc": [], "khong_mua": []}
    start = max(260, n - giu - 1 - buoc * so_diem)
    for i in range(start, n - giu - 1, buoc):
        try:
            kq, kn = quet.phan_tich_df(ma, df.iloc[: i + 1])
            dinh = K.tin_hieu_dinh(kq, "D")
        except Exception:
            continue
        r20, r60 = c[i + 20] / c[i] - 1, c[i + 60] / c[i] - 1
        out["goc"].append((r20, r60, c[i + 60] * CHI_PHI[1] / (o[i + 1] * CHI_PHI[0]) - 1))
        k = kn["D"]
        if k.muc in ("Mua", "Mua mạnh") and k.cat_lo and k.chot_loi1:
            vao = o[i + 1]
            if k.cat_lo < vao < k.chot_loi1:
                lai, kqua, ngay = _giao_dich(o, h, l, c, i + 1, vao, k.cat_lo, k.chot_loi1, i + giu)
                out["mua"].append((k.muc, lai, kqua, ngay, r20))
        elif k.muc == "Chờ về vùng mua" and k.gia_mua and k.cat_lo and k.chot_loi1:
            for j in range(i + 1, min(i + 21, n - 1)):
                if l[j] <= k.gia_mua:
                    vao = min(o[j], k.gia_mua)
                    lai, kqua, ngay = _giao_dich(o, h, l, c, j, vao, k.cat_lo, k.chot_loi1, min(j + giu, n - 1))
                    out["cho"].append((lai, kqua, ngay))
                    break
        elif k.muc == "Không mua":
            out["khong_mua"].append(r20)
        if dinh.hang >= 2:
            out["ban"].append((dinh.muc, r20, c[i + 10] / c[i] - 1, float(h[i + 1:i + 21].max() / c[i] - 1)))
        elif dinh.hang == 1:
            out["theo_doi_dinh"].append(r20)
    return out


def _tai(ma):
    try:
        return ma, du_lieu._vci(ma, "D")
    except Exception:
        return ma, None


def _tom_tat_lenh(ds):
    if not ds:
        return {"so_lenh": 0}
    lai = np.array([x[-4] if len(x) == 5 else x[0] for x in ds])
    kq = [x[-3] if len(x) == 5 else x[1] for x in ds]
    return {"so_lenh": len(ds), "ti_le_thang": float((lai > 0).mean()), "lai_tb": float(lai.mean()),
            "lai_trung_vi": float(np.median(lai)), "cham_tp": kq.count("chốt lời") / len(ds),
            "cham_sl": kq.count("cắt lỗ") / len(ds), "het_han": kq.count("hết hạn") / len(ds),
            "ngay_giu_tb": float(np.mean([x[-2] if len(x) == 5 else x[2] for x in ds]))}


def tong_hop(ket_qua: list[dict]) -> dict:
    mua = [x for r in ket_qua for x in r["mua"]]
    goc = np.array([x for r in ket_qua for x in r["goc"]])
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
    return res


def chay(ds_ma: list[str], buoc: int = 5, so_diem: int = 100, so_tien_trinh: int = 4, tien_trinh=None) -> dict:
    with ThreadPoolExecutor(6) as ex:
        data = [(m, d) for m, d in ex.map(_tai, ds_ma) if d is not None and len(d) > 400]
    ket_qua = []
    with ProcessPoolExecutor(so_tien_trinh) as ex:
        futs = [ex.submit(kiem_dinh_ma, m, d, buoc, so_diem) for m, d in data]
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
