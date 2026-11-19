"""Khuyến nghị theo ngày: lưu bản khuyến nghị mỗi ngày, xem lại theo ngày kèm hiệu quả đến nay,
so sánh với phiên trước, và lịch sự kiện / ngày chốt lời dự kiến sắp tới.

Mỗi ngày lưu một file nhỏ bao_cao/lich_su/<YYYY-MM-DD>.json (chỉ các mã đáng chú ý).
"""
import datetime as dt
import json
from pathlib import Path

import pandas as pd

THU_MUC = Path(__file__).resolve().parent.parent / "bao_cao" / "lich_su"
COT_MUA = ["Mã", "Sàn", "Ngành", "Khuyến nghị", "Hạng", "Điểm", "Giá", "Vùng mua", "Giá mua", "Cắt lỗ", "Chốt lời",
           "R:R", "Dự kiến chốt lời", "Số phiên dự kiến", "Sức khỏe"]
COT_BAN = ["Mã", "Sàn", "Ngành", "Tín hiệu", "Hạng", "Số dấu hiệu", "Giá", "Vùng bán", "Giá bán"]


def _gon(rows, cot, loc):
    return [{c: r.get(c) for c in cot if c in r} for r in rows if loc(r)]


def luu_ngay(data: dict, ngay: str | None = None, thu_muc=None) -> Path | None:
    """Lưu bản gọn của kết quả quét (dict từ quet.ghi). `ngay` mặc định: hôm nay (giờ VN)."""
    thu_muc = Path(thu_muc or THU_MUC)
    ngay = ngay or dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).strftime("%Y-%m-%d")
    ban = {"ngay": ngay, "luc": data.get("luc"), "thong_ke": data.get("thong_ke")}
    for tam in ("D", "W"):
        ban[f"mua_{tam}"] = _gon(data.get(tam, []), COT_MUA, lambda r: (r.get("Hạng") or 0) >= 2)
        ban[f"ban_{tam}"] = _gon(data.get(f"ban_{tam}", []), COT_BAN, lambda r: (r.get("Hạng") or 0) >= 1)
    try:
        thu_muc.mkdir(parents=True, exist_ok=True)
        p = thu_muc / f"{ngay}.json"
        p.write_text(json.dumps(ban, ensure_ascii=False), encoding="utf-8")
        return p
    except OSError:
        return None


def ds_ngay(thu_muc=None) -> list[str]:
    thu_muc = Path(thu_muc or THU_MUC)
    return sorted((p.stem for p in thu_muc.glob("????-??-??.json")), reverse=True) if thu_muc.exists() else []


def doc_ngay(ngay: str, thu_muc=None) -> dict:
    return json.loads((Path(thu_muc or THU_MUC) / f"{ngay}.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------- hiệu quả đến nay
def hieu_qua_mua(rows: list, ngay: str, lay_gia) -> pd.DataFrame:
    """Với mỗi khuyến nghị mua của ngày `ngay`: đã khớp chưa (giá về giá mua), rồi chạm chốt lời / cắt lỗ
    trước, hay đang lãi/lỗ bao nhiêu. `lay_gia(ma)` → DataFrame giá ngày (open/high/low/close)."""
    out = []
    moc = pd.Timestamp(ngay)
    for r in rows:
        ma, gm, sl, tp = r["Mã"], r.get("Giá mua"), r.get("Cắt lỗ"), r.get("Chốt lời")
        dong = {**r, "Trạng thái": "Không có dữ liệu", "Lãi/lỗ %": None, "Ngày khớp": None, "Ngày đóng": None}
        try:
            df = lay_gia(ma)
            sau = df[df.index > moc]
        except Exception:
            out.append(dong)
            continue
        if not gm or sau.empty:
            dong["Trạng thái"] = "Chưa có phiên mới" if sau is not None and sau.empty else "–"
            out.append(dong)
            continue
        khop = sau[sau["low"] <= gm]
        if khop.empty:
            dong["Trạng thái"] = "Chưa khớp (giá chưa về vùng mua)"
            dong["Lãi/lỗ %"] = None
            out.append(dong)
            continue
        ngay_khop = khop.index[0]
        vao = min(float(sau.loc[ngay_khop, "open"]), gm)
        dong["Ngày khớp"] = ngay_khop.strftime("%d/%m/%Y")
        tiep = sau[sau.index >= ngay_khop]
        for d, x in tiep.iterrows():
            if sl and x["low"] <= sl:
                dong.update({"Trạng thái": "Đã cắt lỗ", "Lãi/lỗ %": round((sl / vao - 1) * 100, 1),
                             "Ngày đóng": d.strftime("%d/%m/%Y")})
                break
            if tp and x["high"] >= tp:
                dong.update({"Trạng thái": "Đã chạm chốt lời", "Lãi/lỗ %": round((tp / vao - 1) * 100, 1),
                             "Ngày đóng": d.strftime("%d/%m/%Y")})
                break
        else:
            dong.update({"Trạng thái": "Đang giữ", "Lãi/lỗ %": round((float(tiep["close"].iloc[-1]) / vao - 1) * 100, 1)})
        out.append(dong)
    return pd.DataFrame(out)


def hieu_qua_ban(rows: list, ngay: str, lay_gia) -> pd.DataFrame:
    """Khuyến nghị bán ở đỉnh: giá thay đổi bao nhiêu từ hôm đó (âm = bán đúng)."""
    out = []
    moc = pd.Timestamp(ngay)
    for r in rows:
        dong = {**r, "Thay đổi từ hôm đó %": None, "Đánh giá": "–"}
        try:
            df = lay_gia(r["Mã"])
            sau = df[df.index > moc]
            if not sau.empty and r.get("Giá"):
                thay = float(sau["close"].iloc[-1]) / r["Giá"] - 1
                dong["Thay đổi từ hôm đó %"] = round(thay * 100, 1)
                dong["Đánh giá"] = "Bán đúng (giá giảm)" if thay < 0 else "Giá vẫn tăng"
        except Exception:
            pass
        out.append(dong)
    return pd.DataFrame(out)


# ------------------------------------------------------------------------- so sánh
def so_sanh(moi: dict, cu: dict, tam: str = "D") -> dict:
    """Mã mới vào / bị loại khỏi danh sách Mua (Mua mạnh + Mua) và Bán ở đỉnh (Chốt lời dần + Bán mạnh)."""
    def tap(ds, hang_min):
        return {r["Mã"]: r for r in ds if (r.get("Hạng") or 0) >= hang_min}
    out = {}
    for ten, k, h in (("mua", f"mua_{tam}", 3), ("cho", f"mua_{tam}", 2), ("ban", f"ban_{tam}", 2)):
        a, b = tap(moi.get(k, []), h), tap(cu.get(k, []), h)
        if ten == "cho":
            a = {m: r for m, r in a.items() if r.get("Hạng") == 2}
            b = {m: r for m, r in b.items() if r.get("Hạng") == 2}
        out[ten] = {"moi_vao": [a[m] for m in sorted(set(a) - set(b))],
                    "bi_loai": [b[m] for m in sorted(set(b) - set(a))],
                    "giu_nguyen": sorted(set(a) & set(b))}
    return out


# ------------------------------------------------------------------------- lịch sắp tới
def lich_sap_toi(ds_ma: list, bang_mua: list | None = None, so_ngay: int = 60, su_kien_ma=None) -> pd.DataFrame:
    """Lịch các ngày sắp tới: sự kiện doanh nghiệp (cổ tức, ĐHCĐ, phát hành…) của các mã trong `ds_ma`
    và ngày dự kiến chốt lời của các khuyến nghị mua. `su_kien_ma(ma)` → DataFrame (Ngày, Loại, Nội dung)."""
    hom_nay = pd.Timestamp.now().normalize()
    den = hom_nay + pd.Timedelta(days=so_ngay)
    rows = []
    if su_kien_ma is None:
        from .co_ban import su_kien as su_kien_ma
    for ma in dict.fromkeys(ds_ma):
        try:
            sk = su_kien_ma(ma)
        except Exception:
            continue
        for _, x in sk.iterrows():
            d = pd.to_datetime(x["Ngày"], errors="coerce")
            if pd.notna(d) and hom_nay <= d <= den and x["Loại"] not in ("Giao dịch nội bộ",):
                rows.append({"Ngày": d, "Mã": ma, "Loại": x["Loại"], "Nội dung": x["Nội dung"]})
    for r in bang_mua or []:
        d = pd.to_datetime(r.get("Dự kiến chốt lời"), dayfirst=True, errors="coerce")
        if pd.notna(d) and hom_nay <= d <= den:
            rows.append({"Ngày": d, "Mã": r["Mã"], "Loại": "Dự kiến chốt lời",
                         "Nội dung": f"{r.get('Khuyến nghị')} · mua {r.get('Giá mua') or 0:,.0f} → chốt lời "
                                     f"{r.get('Chốt lời') or 0:,.0f}"})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values(["Ngày", "Mã"]).reset_index(drop=True)
    thu = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
    df.insert(1, "Thứ", [thu[d.weekday()] for d in df["Ngày"]])
    df["Ngày"] = df["Ngày"].dt.strftime("%d/%m/%Y")
    return df
