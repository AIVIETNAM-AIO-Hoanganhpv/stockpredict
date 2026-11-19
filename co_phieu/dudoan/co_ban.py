"""Thông tin doanh nghiệp & báo cáo tài chính (nguồn: Vietcap IQ).

  • Hồ sơ: tên, ngành, vốn hóa, giới thiệu, sở hữu nước ngoài/nhà nước, khuyến nghị của CTCK.
  • Cổ đông lớn & ban lãnh đạo.
  • Báo cáo tài chính: Kết quả kinh doanh, Cân đối kế toán, Lưu chuyển tiền tệ (năm & quý).
  • Chỉ số: P/E, P/B, ROE, ROA, biên lợi nhuận, nợ/vốn chủ, cổ tức…
  • Điểm sức khỏe tài chính 1–5 sao: Tăng trưởng, Sinh lời, An toàn tài chính, Định giá.

Điểm sức khỏe được tính TẠI MỘT THỜI ĐIỂM, chỉ dùng các báo cáo đã công bố trước thời điểm đó
(theo ngày công bố), nên dùng được cho backtest mà không "nhìn trước tương lai".
"""
import html
import json
import math
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import du_lieu

API = "company/{ma}"
URL = "https://trading.vietcap.com.vn/api/iq-insight-service/v1/"
THU_MUC_CACHE = Path(__file__).resolve().parent.parent / "du_lieu_ma" / "cache"
HAN_CACHE = 12 * 3600          # giây: báo cáo tài chính ít thay đổi trong ngày

PHAN = {"kqkd": "INCOME_STATEMENT", "cdkt": "BALANCE_SHEET", "lctt": "CASH_FLOW"}
TEN_PHAN = {"kqkd": "Kết quả kinh doanh", "cdkt": "Cân đối kế toán", "lctt": "Lưu chuyển tiền tệ"}

# Chỉ tiêu chính (thử lần lượt – mỗi loại hình doanh nghiệp dùng mã khác nhau)
DOANH_THU = ["isa3", "isb38", "isi103", "isa1"]     # DN thường/CTCK · ngân hàng · bảo hiểm
LOI_NHUAN = ["isa22", "isa20"]                      # LN của cổ đông công ty mẹ · LNST
VON_CHU = ["bsa78"]
TONG_TS = ["bsa53"]
VAY = ["bsa56", "bsa71"]                            # vay ngắn hạn + dài hạn

_khoa = threading.Lock()
_bo_nho: dict = {}


# ------------------------------------------------------------------------- tải & cache
def _goi(duong_dan: str):
    """Gọi API Vietcap (đường dẫn tương đối) hoặc một URL đầy đủ (VD: CafeF)."""
    import gzip
    import urllib.request
    url = duong_dan if duong_dan.startswith("http") else URL + duong_dan
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    d = json.loads(raw)
    if not d.get("successful", d.get("Success", True)):
        raise RuntimeError(d.get("msg") or d.get("Message") or "Nguồn dữ liệu báo lỗi")
    return d.get("data", d.get("Data"))


def _lay(ma: str, loai: str, duong_dan: str):
    """Tải có cache: bộ nhớ (12 giờ) + file trong du_lieu_ma/cache (dùng lại khi mất mạng)."""
    key = (ma, loai)
    now = time.time()
    with _khoa:
        if key in _bo_nho and now - _bo_nho[key][0] < HAN_CACHE:
            return _bo_nho[key][1]
    f = THU_MUC_CACHE / f"{ma}_{loai}.json"
    try:
        if f.exists() and now - f.stat().st_mtime < HAN_CACHE:
            data = json.loads(f.read_text(encoding="utf-8"))
        else:
            data = _goi(duong_dan)
            try:
                THU_MUC_CACHE.mkdir(parents=True, exist_ok=True)
                f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            except OSError:
                pass
    except Exception:
        if f.exists():                              # mất mạng → dùng bản cũ
            data = json.loads(f.read_text(encoding="utf-8"))
        else:
            raise
    with _khoa:
        _bo_nho[key] = (now, data)
    return data


def ho_so_raw(ma):
    return _lay(ma, "hoso", f"company/{ma}") or {}


def bctc_raw(ma, phan):
    return _lay(ma, phan, f"company/{ma}/financial-statement?section={PHAN[phan]}") or {}


def metrics_raw(ma):
    return _lay(ma, "metrics", f"company/{ma}/financial-statement/metrics") or {}


def chi_so_raw(ma):
    return _lay(ma, "chiso", f"company/{ma}/statistics-financial") or []


def co_dong_raw(ma):
    return _lay(ma, "codong", f"company/{ma}/shareholder") or []


# ------------------------------------------------------------------------- hồ sơ
def _lam_sach(s) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", " ", str(s or "")))
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


XEP_HANG_CTCK = {"BUY": "MUA", "OUTPERFORM": "KHẢ QUAN", "HOLD": "NẮM GIỮ", "NEUTRAL": "TRUNG LẬP",
                 "UNDERPERFORM": "KÉM KHẢ QUAN", "SELL": "BÁN"}


def ho_so(ma: str) -> dict:
    d = ho_so_raw(ma)
    if not d:
        return {}
    return {
        "ma": ma, "ten": d.get("viOrganName") or d.get("enOrganName") or ma,
        "ten_ngan": d.get("viOrganShortName") or ma, "nganh": d.get("sectorVn") or "",
        "gia": d.get("currentPrice"), "von_hoa": d.get("marketCap"),
        "so_cp": d.get("issueShare") or d.get("numberOfSharesMktCap"),
        "ngay_niem_yet": (d.get("listingDate") or "")[:10], "gia_chao_san": d.get("firstPrice"),
        "gioi_thieu": _lam_sach(d.get("profile")),
        "nuoc_ngoai": d.get("foreignerPercentage"), "room_nuoc_ngoai": d.get("maximumForeignPercentage"),
        "nha_nuoc": d.get("statePercentage"), "free_float": d.get("freeFloatPercentage"),
        "cao_52t": d.get("highestPrice1Year"), "thap_52t": d.get("lowestPrice1Year"),
        "gtgd_tb_1t": d.get("averageMatchValue1Month"), "la_ngan_hang": bool(d.get("isBank")),
        "ctck": {"xep_hang": XEP_HANG_CTCK.get(str(d.get("rating") or "").upper(), d.get("rating")),
                 "ngay": d.get("ratingAsOf"), "gia_muc_tieu": d.get("targetPrice"),
                 "tiem_nang": d.get("upsideToTargetPercent"), "chuyen_vien": d.get("analyst"),
                 "nguon": "Vietcap Securities"} if d.get("rating") else None,
    }


def co_dong(ma: str, so: int = 10) -> pd.DataFrame:
    rows = [{"Cổ đông": x.get("ownerName"), "Chức vụ": x.get("positionName") or "",
             "Loại": {"INDIVIDUAL": "Cá nhân", "CORPORATE": "Tổ chức"}.get(x.get("ownerType"), x.get("ownerType")),
             "Số CP": x.get("quantity"), "Tỷ lệ %": round((x.get("percentage") or 0) * 100, 2),
             "Cập nhật": (x.get("publicDate") or "")[:10]} for x in co_dong_raw(ma)]
    df = pd.DataFrame(rows)
    return df.sort_values("Tỷ lệ %", ascending=False).head(so).reset_index(drop=True) if not df.empty else df


# ------------------------------------------------------------------------- sự kiện, cổ tức, nội bộ, công ty con
CAFEF = "https://cafef.vn/du-lieu/Ajax/PageNew/"
LOAI_SU_KIEN = {"DIV": "Cổ tức tiền mặt", "ISS": "Phát hành cổ phiếu", "AGME": "Đại hội cổ đông thường niên",
                "EGME": "Đại hội cổ đông bất thường", "AIS": "Niêm yết bổ sung", "DDIND": "Giao dịch nội bộ",
                "DDINS": "Giao dịch cổ đông lớn", "DDRP": "Giao dịch người liên quan", "MOVE": "Chuyển sàn",
                "NLIS": "Niêm yết mới", "SUSP": "Tạm ngừng giao dịch", "OTHE": "Khác"}


def su_kien_raw(ma):
    den = pd.Timestamp.now() + pd.Timedelta(days=180)
    return _lay(ma, "sukien", f"events?ticker={ma}&fromDate=20100101&toDate={den:%Y%m%d}&page=0&size=200") or {}


def tin_dn_raw(ma):
    den = pd.Timestamp.now() + pd.Timedelta(days=1)
    return _lay(ma, "tin", f"news?ticker={ma}&fromDate=20200101&toDate={den:%Y%m%d}&page=0&size=30") or {}


def noi_bo_raw(ma):
    return _lay(ma, "noibo", f"company/{ma}/insider-transaction") or {}


def cong_ty_con_raw(ma):
    return _lay(ma, "ctycon", f"{CAFEF}GetDataSubsidiaries.ashx?Symbol={ma.lower()}") or {}


def _ds(raw):
    return raw.get("content", []) if isinstance(raw, dict) else (raw or [])


def su_kien(ma: str, so: int = 30, loai: tuple | None = None) -> pd.DataFrame:
    """Sự kiện doanh nghiệp (mới nhất trước): cổ tức, phát hành, ĐHCĐ, niêm yết bổ sung…"""
    rows = []
    gioi_han = f"{pd.Timestamp.now() + pd.Timedelta(days=366):%Y-%m-%d}"     # bỏ ngày sai của nguồn (VD: 2031)
    for x in _ds(su_kien_raw(ma)):
        if loai and x.get("eventCode") not in loai:
            continue
        if (x.get("displayDate1") or "")[:10] > gioi_han:
            continue
        rows.append({"Ngày": (x.get("displayDate1") or x.get("publicDate") or "")[:10],
                     "Loại": LOAI_SU_KIEN.get(x.get("eventCode"), x.get("eventNameVi") or x.get("eventCode")),
                     "Nội dung": x.get("eventTitleVi") or x.get("eventNameVi") or ""})
    df = pd.DataFrame(rows)
    return df.sort_values("Ngày", ascending=False).head(so).reset_index(drop=True) if not df.empty else df


def lich_su_co_tuc(ma: str, so: int = 20) -> pd.DataFrame:
    """Lịch sử trả cổ tức: ngày GDKHQ, năm tài chính, tỷ lệ (% mệnh giá 10.000đ), tiền mặt / cổ phiếu."""
    rows = []
    for x in _ds(su_kien_raw(ma)):
        code, title = x.get("eventCode"), x.get("eventTitleVi") or ""
        if code == "DIV":
            loai = "Tiền mặt"
            ty_le = (x.get("valuePerShare") or 0) / 10_000 * 100 or (x.get("exerciseRatio") or 0) * 100
        elif code == "ISS" and ("thưởng" in title.lower() or "cổ tức" in title.lower()):
            loai, ty_le = "Cổ phiếu", (x.get("exerciseRatio") or 0) * 100
        else:
            continue
        nam = re.search(r"(?:Đợt\s*\d+\s*)?(20\d\d)", title)
        rows.append({"Ngày GDKHQ": (x.get("displayDate1") or "")[:10], "Năm": nam.group(1) if nam else "",
                     "Cổ tức %": round(ty_le, 2), "Loại": loai,
                     "Tiền/CP (đ)": x.get("valuePerShare") if code == "DIV" else None, "Nội dung": title})
    df = pd.DataFrame(rows)
    return df.sort_values("Ngày GDKHQ", ascending=False).head(so).reset_index(drop=True) if not df.empty else df


def giao_dich_noi_bo(ma: str, so: int = 20) -> pd.DataFrame:
    rows = []
    for x in _ds(noi_bo_raw(ma)):
        rows.append({"Ngày": (x.get("startDate") or x.get("displayDate1") or "")[:10],
                     "Người giao dịch": x.get("traderNameVi") or "",
                     "Chức vụ": x.get("traderPositionVi") or x.get("roleNameVi") or "",
                     "Loại": x.get("actionTypeVi") or "", "Đăng ký": x.get("shareRegister"),
                     "Thực hiện": x.get("shareAcquire"), "Sở hữu sau GD": x.get("shareAfterTrade"),
                     "Trạng thái": x.get("tradeStatusVi") or "",
                     "Người liên quan": x.get("relativeNameVi") if x.get("relativeNameVi") != x.get("traderNameVi") else ""})
    df = pd.DataFrame(rows)
    return df.sort_values("Ngày", ascending=False).head(so).reset_index(drop=True) if not df.empty else df


def ban_lanh_dao(ma: str) -> pd.DataFrame:
    """HĐQT, Ban giám đốc… (theo danh sách cổ đông có chức vụ)."""
    rows = [{"Họ tên": x.get("ownerName"), "Chức vụ": x.get("positionName"),
             "Số CP": x.get("quantity"), "Tỷ lệ %": round((x.get("percentage") or 0) * 100, 3)}
            for x in co_dong_raw(ma) if x.get("positionName")]
    return pd.DataFrame(rows)


def cong_ty_con(ma: str) -> pd.DataFrame:
    """Công ty con & liên kết (nguồn CafeF): tên, vốn điều lệ, tỷ lệ sở hữu."""
    raw = cong_ty_con_raw(ma)
    ds = raw.get("Subsidiaries", []) if isinstance(raw, dict) else []
    rows = []
    for x in ds:
        tl = x.get("OwnershipRate")
        rows.append({"Công ty": x.get("Name"), "Vốn điều lệ (tỷ)": x.get("TotalCapital"),
                     "Vốn góp (tỷ)": x.get("SharedCapital"),
                     "Sở hữu %": round(tl, 2) if tl is not None and tl <= 100 else None,
                     "Loại": "Công ty con" if tl is not None and 50 < tl <= 100 else "Liên kết",
                     "Ghi chú": x.get("Note") or ""})
    df = pd.DataFrame(rows)
    return df.sort_values("Sở hữu %", ascending=False, na_position="last").reset_index(drop=True) if not df.empty else df


def tin_doanh_nghiep(ma: str, so: int = 20) -> list[dict]:
    """Tin của doanh nghiệp (Vietcap): tiêu đề, ngày, tóm tắt."""
    out = []
    for x in _ds(tin_dn_raw(ma))[:so]:
        tom_tat = _lam_sach(x.get("newsShortContent") or x.get("newsFullContent") or "")[:400]
        out.append({"tieu_de": x.get("newsTitle") or "", "ngay": (x.get("publicDate") or "")[:16].replace("T", " "),
                    "nguon": x.get("newsSource") or "Vietcap", "link": x.get("newsSourceLink") or "",
                    "tom_tat": tom_tat})
    return out


# ------------------------------------------------------------------------- báo cáo tài chính
def _ky(r, quy: bool) -> str:
    return f"Q{r['lengthReport']}/{r['yearReport']}" if quy else str(r["yearReport"])


def bang_bctc(ma: str, phan: str = "kqkd", quy: bool = False, so_ky: int | None = None) -> pd.DataFrame:
    """Bảng báo cáo: dòng = chỉ tiêu (có thụt lề theo cấp), cột = kỳ (cũ → mới). Đơn vị: tỷ đồng."""
    so_ky = so_ky or (8 if quy else 5)
    raw = bctc_raw(ma, phan)
    recs = sorted(raw.get("quarters" if quy else "years") or [], key=lambda r: (r["yearReport"], r["lengthReport"]))
    recs = recs[-so_ky:]
    chi_tieu = [x for x in metrics_raw(ma).get(PHAN[phan], []) if x.get("field")]
    rows = []
    for ct in chi_tieu:
        vals = [r.get(ct["field"]) for r in recs]
        if all(v is None or v == 0 for v in vals):
            continue
        dong = {"Chỉ tiêu": ("   " * (ct.get("level", 1) - 1)) + ct["titleVi"], "_ma": ct["field"]}
        laeps = "cổ phiếu" in ct["titleVi"].lower() and "VND" in ct["titleVi"]
        for r, v in zip(recs, vals):
            dong[_ky(r, quy)] = None if v is None else (round(v) if laeps else round(v / 1e9, 1))
        rows.append(dong)
    return pd.DataFrame(rows)


def _chuoi_quy(ma: str) -> pd.DataFrame:
    """Dữ liệu quý: doanh thu, LN, vốn chủ, tổng TS, vay, ngày công bố (dùng tính chỉ số theo thời điểm)."""
    kq = {(r["yearReport"], r["lengthReport"]): r for r in bctc_raw(ma, "kqkd").get("quarters") or []}
    cd = {(r["yearReport"], r["lengthReport"]): r for r in bctc_raw(ma, "cdkt").get("quarters") or []}

    def lay(r, ds, bo_so_0=False):
        for f in ds:
            if r and r.get(f) is not None and not (bo_so_0 and r[f] == 0):
                return float(r[f])
        return None
    rows = []
    for k in sorted(kq):
        r, b = kq[k], cd.get(k)
        nam, q = k
        cuoi_quy = pd.Timestamp(year=nam, month=3 * q, day=1) + pd.offsets.MonthEnd(0)
        cong_bo = pd.to_datetime(r.get("publicDate") or (b or {}).get("publicDate"), errors="coerce")
        if pd.isna(cong_bo):
            cong_bo = cuoi_quy + pd.Timedelta(days=45)
        vay = [lay(b, [f]) for f in VAY]
        rows.append({"ky": f"Q{q}/{nam}", "cuoi_quy": cuoi_quy, "cong_bo": cong_bo.tz_localize(None) if cong_bo.tzinfo else cong_bo,
                     "dt": lay(r, DOANH_THU, bo_so_0=True), "ln": lay(r, LOI_NHUAN), "von_chu": lay(b, VON_CHU),
                     "tong_ts": lay(b, TONG_TS),
                     "vay": sum(v for v in vay if v) if any(v is not None for v in vay) else None})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------- chỉ số (nguồn Vietcap)
CHI_SO = [("pe", "P/E", "x"), ("pb", "P/B", "x"), ("ps", "P/S", "x"), ("evToEbitda", "EV/EBITDA", "x"),
          ("roe", "ROE", "%"), ("roa", "ROA", "%"), ("grossMargin", "Biên LN gộp", "%"),
          ("afterTaxProfitMargin", "Biên LN ròng", "%"), ("debtToEquity", "Nợ vay/Vốn chủ", "x"),
          ("currentRatio", "Thanh toán hiện hành", "x"), ("dividendYield", "Tỷ suất cổ tức", "%"),
          ("netInterestMargin", "NIM (ngân hàng)", "%"), ("npl", "Nợ xấu NPL (ngân hàng)", "%"),
          ("casaRatio", "CASA (ngân hàng)", "%")]


def bang_chi_so(ma: str, quy: bool = True, so_ky: int | None = None) -> pd.DataFrame:
    """Chỉ số tài chính: quý (luỹ kế 4 quý – TTM) hoặc năm."""
    so_ky = so_ky or (8 if quy else 5)
    ds = [x for x in chi_so_raw(ma) if (x.get("ratioType") == "RATIO_TTM") == quy]
    ds = sorted(ds, key=lambda x: (int(x["year"]), x["quarter"]))[-so_ky:]
    rows = []
    for k, ten, dv in CHI_SO:
        vals = [x.get(k) for x in ds]
        if all(v in (None, 0) for v in vals):
            continue
        dong = {"Chỉ số": ten}
        for x, v in zip(ds, vals):
            cot = f"Q{x['quarter']}/{x['year']}" if quy else str(x["year"])
            dong[cot] = None if v is None else round(v * 100, 1) if dv == "%" else round(v, 2)
        rows.append(dong)
    return pd.DataFrame(rows)


def chi_so_moi_nhat(ma: str) -> dict:
    ds = sorted([x for x in chi_so_raw(ma) if x.get("ratioType") == "RATIO_TTM"],
                key=lambda x: (int(x["year"]), x["quarter"]))
    if not ds:
        return {}
    x = ds[-1]
    return {"ky": f"Q{x['quarter']}/{x['year']}", **{k: x.get(k) for k, _, _ in CHI_SO},
            "pe_lich_su": [d.get("pe") for d in ds[-20:] if d.get("pe")]}


# ------------------------------------------------------------------------- sức khỏe tài chính
@dataclass
class SucKhoe:
    tang_truong: float = 3.0
    sinh_loi: float = 3.0
    an_toan: float = 3.0
    dinh_gia: float = 3.0
    chi_tiet: dict = field(default_factory=dict)
    ly_do: list = field(default_factory=list)
    du_lieu: bool = True

    @property
    def tong(self) -> float:
        return round((self.tang_truong + self.sinh_loi + self.an_toan + self.dinh_gia) / 4, 1)


def _sao(x, nguong, tang=True):
    """Đổi giá trị thành 1–5 sao theo 4 ngưỡng (tăng dần nếu tang=True)."""
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return 3.0
    n = sum(x >= t for t in nguong) if tang else sum(x <= t for t in nguong)
    return float(1 + n)


def _tang(a, b):
    if a is None or b is None or b == 0:
        return None
    return (a - b) / abs(b)


def suc_khoe(ma: str, ngay=None, gia: float | None = None, quy: pd.DataFrame | None = None,
             la_ngan_hang: bool | None = None, so_cp: float | None = None) -> SucKhoe:
    """Chấm sao TẠI ngày `ngay` (mặc định: hôm nay) – chỉ dùng báo cáo đã công bố trước ngày đó.
    • Tăng trưởng: LN & doanh thu 4 quý gần nhất so với 4 quý trước đó.
    • Sinh lời: ROE (LN 4 quý / vốn chủ bình quân).
    • An toàn: nợ vay / vốn chủ (ngân hàng: vốn chủ / tổng tài sản).
    • Định giá: P/E hiện tại so với P/E của chính mã đó trong 3 năm (rẻ hơn lịch sử → nhiều sao)."""
    sk = SucKhoe()
    try:
        quy = _chuoi_quy(ma) if quy is None else quy
    except Exception as e:
        sk.du_lieu, sk.ly_do = False, [f"Không tải được báo cáo tài chính: {e}"]
        return sk
    ngay = pd.Timestamp(ngay) if ngay is not None else pd.Timestamp.now()
    q = quy[quy["cong_bo"] <= ngay].reset_index(drop=True) if not quy.empty else quy
    if len(q) < 8:
        sk.du_lieu, sk.ly_do = False, ["Chưa đủ 8 quý báo cáo đã công bố."]
        return sk
    if la_ngan_hang is None or so_cp is None:
        hs = ho_so_raw(ma)
        la_ngan_hang = bool(hs.get("isBank")) if la_ngan_hang is None else la_ngan_hang
        so_cp = so_cp or hs.get("issueShare") or hs.get("numberOfSharesMktCap")

    def ttm(cot, cuoi):
        v = q[cot].iloc[cuoi - 4:cuoi] if cuoi - 4 >= 0 else q[cot].iloc[:0]
        return float(v.sum()) if len(v) == 4 and v.notna().all() else None
    n = len(q)
    ln, ln_truoc = ttm("ln", n), ttm("ln", n - 4)
    dt, dt_truoc = ttm("dt", n), ttm("dt", n - 4)
    g_ln, g_dt = _tang(ln, ln_truoc), _tang(dt, dt_truoc)
    von = q["von_chu"].iloc[-1]
    von_tb = pd.Series([von, q["von_chu"].iloc[-5]]).mean()
    roe = ln / von_tb if ln is not None and von_tb and von_tb > 0 else None

    # Tăng trưởng
    s_ln = _sao(g_ln, [-0.2, 0.0, 0.1, 0.25])
    s_dt = _sao(g_dt, [-0.2, 0.0, 0.1, 0.25])
    sk.tang_truong = round((s_ln * 2 + s_dt) / 3)
    # Sinh lời
    sk.sinh_loi = _sao(roe, [0.05, 0.10, 0.15, 0.20])
    if ln is not None and ln < 0:
        sk.sinh_loi = 1.0
        sk.ly_do.append("Doanh nghiệp đang LỖ (4 quý gần nhất).")
    # An toàn tài chính
    if la_ngan_hang:
        ty_le = von / q["tong_ts"].iloc[-1] if q["tong_ts"].iloc[-1] else None
        sk.an_toan = _sao(ty_le, [0.05, 0.07, 0.09, 0.11])
        sk.chi_tiet["von_chu_tong_ts"] = ty_le
    else:
        no = q["vay"].iloc[-1] / von if von and von > 0 and q["vay"].iloc[-1] is not None else None
        sk.an_toan = _sao(no, [2.0, 1.5, 1.0, 0.5], tang=False) if von and von > 0 else 1.0
        sk.chi_tiet["no_vay_von_chu"] = no
    # Định giá: P/E so với lịch sử của chính mã
    pe = None
    if gia and so_cp and ln and ln > 0:
        pe = gia / (ln / so_cp)
        lich_su = []
        for i in range(max(8, n - 12), n):
            l_i = ttm("ln", i + 1)
            g_i = q["gia_cong_bo"].iloc[i] if "gia_cong_bo" in q and pd.notna(q["gia_cong_bo"].iloc[i]) else None
            if l_i and l_i > 0 and g_i:
                lich_su.append(g_i / (l_i / so_cp))
        if len(lich_su) >= 4:
            pct = sum(x < pe for x in lich_su) / len(lich_su)
            sk.dinh_gia = _sao(pct, [0.2, 0.4, 0.6, 0.8], tang=False)
            sk.chi_tiet["pe_phan_vi_3n"] = pct
        else:
            sk.dinh_gia = _sao(pe, [8, 12, 18, 25], tang=False)
    elif ln is not None and ln <= 0:
        sk.dinh_gia = 1.0
    sk.chi_tiet.update({"ln_ttm": ln, "tang_ln": g_ln, "dt_ttm": dt, "tang_dt": g_dt, "roe": roe, "pe": pe,
                        "ky_moi_nhat": q["ky"].iloc[-1]})
    if g_ln is not None:
        sk.ly_do.append(f"LN 4 quý {'tăng' if g_ln >= 0 else 'giảm'} {abs(g_ln):.0%} so với cùng kỳ.")
    if roe is not None:
        sk.ly_do.append(f"ROE {roe:.1%}.")
    return sk


def gan_gia_cong_bo(quy: pd.DataFrame, df_gia: pd.DataFrame) -> pd.DataFrame:
    """Thêm cột giá đóng cửa tại ngày công bố mỗi quý (để tính P/E lịch sử)."""
    if quy.empty or df_gia is None or df_gia.empty:
        return quy
    c = df_gia["close"]
    quy = quy.copy()
    quy["gia_cong_bo"] = [float(c.loc[:d].iloc[-1]) if len(c.loc[:d]) else None for d in quy["cong_bo"]]
    return quy


def suc_khoe_hien_tai(ma: str, df_gia: pd.DataFrame | None = None) -> SucKhoe:
    """Điểm sức khỏe hôm nay (dùng giá hiện tại & P/E lịch sử theo giá ngày công bố)."""
    try:
        quy = _chuoi_quy(ma)
        if df_gia is None:
            df_gia = du_lieu.tai(ma, "D")
        quy = gan_gia_cong_bo(quy, df_gia)
        gia = float(df_gia["close"].iloc[-1])
    except Exception as e:
        return SucKhoe(du_lieu=False, ly_do=[f"Không tải được dữ liệu: {e}"])
    return suc_khoe(ma, gia=gia, quy=quy)


def tom_tat_co_ban(ma: str, df_gia: pd.DataFrame | None = None) -> dict:
    """Một dòng số liệu cơ bản cho bảng lọc / xếp hạng."""
    out = {"P/E": None, "P/B": None, "ROE %": None, "Tăng LN %": None, "Tăng DT %": None, "Nợ/VCSH": None,
           "Cổ tức %": None, "Sức khỏe": None, "★ Tăng trưởng": None, "★ Sinh lời": None, "★ An toàn": None,
           "★ Định giá": None, "Đang lỗ": None, "CTCK": None, "Giá mục tiêu": None}
    try:
        cs = chi_so_moi_nhat(ma)
        hs = ho_so(ma)
    except Exception:
        return out
    sk = suc_khoe_hien_tai(ma, df_gia)
    ct = sk.chi_tiet
    r = lambda x, k=1: None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(x, k)  # noqa: E731
    out.update({
        "P/E": r(cs.get("pe")), "P/B": r(cs.get("pb"), 2), "ROE %": r((cs.get("roe") or 0) * 100) if cs.get("roe") else None,
        "Tăng LN %": r(ct["tang_ln"] * 100) if ct.get("tang_ln") is not None else None,
        "Tăng DT %": r(ct["tang_dt"] * 100) if ct.get("tang_dt") is not None else None,
        "Nợ/VCSH": r(cs.get("debtToEquity"), 2),
        "Cổ tức %": r((cs.get("dividendYield") or 0) * 100) if cs.get("dividendYield") else None,
        "Sức khỏe": sk.tong if sk.du_lieu else None,
        "★ Tăng trưởng": sk.tang_truong if sk.du_lieu else None, "★ Sinh lời": sk.sinh_loi if sk.du_lieu else None,
        "★ An toàn": sk.an_toan if sk.du_lieu else None, "★ Định giá": sk.dinh_gia if sk.du_lieu else None,
        "Đang lỗ": bool(ct.get("ln_ttm") is not None and ct["ln_ttm"] < 0),
        "CTCK": (hs.get("ctck") or {}).get("xep_hang"), "Giá mục tiêu": (hs.get("ctck") or {}).get("gia_muc_tieu"),
    })
    return out


def dieu_chinh_khuyen_nghi(kn, co_ban: dict):
    """Cộng/trừ điểm xếp hạng theo cơ bản: sức khỏe ≥ 4 → +10; ≤ 2 → −10; đang lỗ → −15.
    Chỉ ảnh hưởng thứ tự xếp hạng, KHÔNG đổi mức khuyến nghị (lọc sức khỏe không cải thiện backtest 20 năm)."""
    sk = co_ban.get("Sức khỏe")
    if co_ban.get("Đang lỗ"):
        kn.diem = round(kn.diem - 15, 1)
        kn.ly_do.append("Doanh nghiệp đang lỗ (−15 điểm, chỉ ảnh hưởng xếp hạng).")
    elif sk is not None and sk >= 4:
        kn.diem = round(kn.diem + 10, 1)
        kn.ly_do.append(f"Sức khỏe tài chính tốt {sk}/5 (+10 điểm).")
    elif sk is not None and sk <= 2:
        kn.diem = round(kn.diem - 10, 1)
        kn.ly_do.append(f"Sức khỏe tài chính yếu {sk}/5 (−10 điểm).")
    return kn


def xuat_excel(ma: str, duong_dan) -> Path:
    """Xuất hồ sơ, BCTC (năm & quý), chỉ số, cổ đông ra Excel."""
    duong_dan = Path(duong_dan)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    hs = ho_so(ma)
    with pd.ExcelWriter(duong_dan) as w:
        pd.DataFrame([{"Mục": k, "Giá trị": v} for k, v in hs.items() if k not in ("ctck",)]
                     + ([{"Mục": f"CTCK – {k}", "Giá trị": v} for k, v in (hs.get("ctck") or {}).items()])
                     ).to_excel(w, sheet_name="Hồ sơ", index=False)
        for phan in ("kqkd", "cdkt", "lctt"):
            for quy in (False, True):
                b = bang_bctc(ma, phan, quy)
                if not b.empty:
                    b.drop(columns="_ma").to_excel(w, sheet_name=f"{TEN_PHAN[phan][:20]} ({'quý' if quy else 'năm'})",
                                                   index=False)
        for quy in (False, True):
            b = bang_chi_so(ma, quy)
            if not b.empty:
                b.to_excel(w, sheet_name=f"Chỉ số ({'quý' if quy else 'năm'})", index=False)
        for ten, ham in (("Cổ đông lớn", lambda: co_dong(ma, 30)), ("Ban lãnh đạo", lambda: ban_lanh_dao(ma)),
                         ("Công ty con & liên kết", lambda: cong_ty_con(ma)), ("Lịch sử cổ tức", lambda: lich_su_co_tuc(ma, 50)),
                         ("Sự kiện", lambda: su_kien(ma, 100)), ("Giao dịch nội bộ", lambda: giao_dich_noi_bo(ma, 100))):
            try:
                b = ham()
            except Exception:
                continue
            if not b.empty:
                b.to_excel(w, sheet_name=ten[:31], index=False)
    return duong_dan


# ------------------------------------------------------------------ dự phòng VNDirect (khi Vietcap chặn, VD: Streamlit Cloud)
VND_FINFO = "https://api-finfo.vndirect.com.vn/v4/"
VND_CHI_SO = {"MARKETCAP": "von_hoa", "PRICE_TO_EARNINGS": "pe", "PRICE_TO_BOOK": "pb", "ROAE_TR_AVG5Q": "roe",
              "ROAA_TR_AVG5Q": "roa", "EPS_TR": "eps", "BVPS_CR": "bvps", "DIVIDEND_YIELD": "co_tuc", "BETA": "beta"}


def tom_tat_vnd(ma: str) -> dict:
    """Hồ sơ + chỉ số chính từ VNDirect: dùng khi nguồn chính (Vietcap) không truy cập được."""
    ma = ma.upper()
    ho_so = (_goi(f"{VND_FINFO}company_profiles?q=code:{ma}") or [{}])[0]
    try:
        cs = _goi(f"{VND_FINFO}ratios/latest?filter=ratioCode:{','.join(VND_CHI_SO)}&where=code:{ma}"
                  "&order=reportDate&fields=ratioCode,value,reportDate") or []
    except Exception:
        cs = []
    if not ho_so and not cs:
        raise RuntimeError(f"VNDirect không có dữ liệu cho {ma}")
    out = {"ten": ho_so.get("vnName") or ma, "san": ho_so.get("floor"), "thanh_lap": ho_so.get("foundDate"),
           "dia_chi": ho_so.get("vnAddress"), "website": ho_so.get("website"), "nhan_vien": ho_so.get("employees"),
           "gioi_thieu": ho_so.get("vnSummary"), "nguon": "VNDirect"}
    for x in cs:
        k = VND_CHI_SO.get(x.get("ratioCode"))
        if k and x.get("value") is not None:
            out[k] = float(x["value"])
            out["ngay_chi_so"] = max(out.get("ngay_chi_so", ""), x.get("reportDate") or "")
    return out
