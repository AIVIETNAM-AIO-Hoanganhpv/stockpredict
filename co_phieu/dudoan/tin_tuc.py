"""Tin tức thị trường, kinh tế trong nước & thế giới, doanh nghiệp.

Nguồn: Google News (theo mã / tên công ty / chủ đề vĩ mô), RSS CafeF, Vietstock, VnExpress Kinh doanh,
BBC Business, MarketWatch,
tin doanh nghiệp từ Vietcap. Tự gắn mã cổ phiếu được nhắc trong tiêu đề và đánh dấu tin
Tích cực / Tiêu cực theo từ khóa (chỉ là gợi ý, có thể sai).
"""
import email.utils
import html
import re
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import pandas as pd

RSS = {
    "CafeF": "https://cafef.vn/thi-truong-chung-khoan.rss",
    "Vietstock": "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
    "VnExpress": "https://vnexpress.net/rss/kinh-doanh.rss",
}
# Tin kinh tế theo nhóm (RSS công khai)
NHOM = {
    "Chứng khoán": RSS,
    "Kinh tế trong nước": {
        "CafeF Vĩ mô": "https://cafef.vn/vi-mo-dau-tu.rss",
        "CafeF Ngân hàng": "https://cafef.vn/tai-chinh-ngan-hang.rss",
        "Vietstock Vĩ mô": "https://vietstock.vn/761/kinh-te/vi-mo.rss",
        "Vietstock Kinh tế": "https://vietstock.vn/768/kinh-te/kinh-te-dau-tu.rss",
    },
    "Kinh tế thế giới": {
        "CafeF Quốc tế": "https://cafef.vn/tai-chinh-quoc-te.rss",
        "Vietstock Quốc tế": "https://vietstock.vn/772/the-gioi/tai-chinh-quoc-te.rss",
        "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    },
}
TIENG_ANH = {"BBC Business", "MarketWatch"}
# Chủ đề vĩ mô theo dõi qua Google News
CHU_DE = {"Lãi suất": "lãi suất ngân hàng", "Tỷ giá USD": "tỷ giá USD VND", "Fed": "Fed lãi suất",
          "Giá vàng": "giá vàng", "Giá dầu": "giá dầu thế giới", "Xuất nhập khẩu": "xuất khẩu Việt Nam",
          "Lạm phát (CPI)": "lạm phát CPI Việt Nam", "Đầu tư công": "giải ngân đầu tư công"}
GOOGLE = "https://news.google.com/rss/search?q={q}&hl=vi&gl=VN&ceid=VN:vi"
HAN_CACHE = 15 * 60                     # tin tức: dùng lại trong 15 phút

TU_TOT = ["lãi kỷ lục", "lợi nhuận tăng", "lãi tăng", "doanh thu tăng", "tăng trưởng", "vượt kế hoạch", "hoàn thành kế hoạch",
          "trúng thầu", "ký hợp đồng", "hợp đồng lớn", "đăng ký mua", "mua vào", "gom", "chia cổ tức", "cổ tức",
          "cổ phiếu thưởng", "tăng vốn", "mở rộng", "khả quan", "bứt phá", "tăng trần", "kỷ lục", "nâng hạng",
          "nâng mục tiêu", "khuyến nghị mua", "lãi ròng", "phục hồi", "thoát lỗ", "lãi lớn", "mua ròng",
          "tăng vọt", "đột biến tăng", "vượt đỉnh", "lập đỉnh", "tăng mạnh", "khởi sắc"]
TU_XAU = ["thua lỗ", "lỗ ròng", "báo lỗ", "lỗ lũy kế", "lợi nhuận giảm", "lãi giảm", "doanh thu giảm", "giảm sâu",
          "bị phạt", "xử phạt", "vi phạm", "đăng ký bán", "bán ra", "bán giải chấp", "giải chấp", "khởi tố",
          "bắt tạm giam", "điều tra", "cảnh báo", "hạn chế giao dịch", "đình chỉ", "hủy niêm yết", "nợ xấu",
          "chậm trả", "lao dốc", "giảm sàn", "sụt giảm", "âm vốn", "ý kiến ngoại trừ", "kiểm soát đặc biệt",
          "bán tháo", "thoái vốn", "từ nhiệm", "lỗ", "bán ròng", "thủng đáy", "về đáy", "chạm đáy", "chịu áp lực",
          "giảm mạnh", "trôi", "rơi", "mất mốc", "hạ mục tiêu", "khuyến nghị bán", "phá sản", "tạm dừng"]
# từ in hoa 3 chữ cái hay gặp nhưng KHÔNG phải mã cổ phiếu
KHONG_PHAI_MA = {"CEO", "GDP", "USD", "VND", "FDI", "ETF", "IPO", "CPI", "FED", "SBV", "NHNN", "BĐS", "TTCK", "HĐQT",
                 "ĐHĐCĐ", "UBCK", "AI", "EU", "UAE", "TPP", "WTO", "IMF", "ADB", "PMI", "VAT", "KRX", "MSCI",
                 "FTSE", "NAV", "EPS", "ROE", "P/E", "OTC", "THE", "AND", "FOR", "CTCK", "VNI", "HCM", "TPHCM", "BOT"}

TU_TOT_EN = ["surge", "surges", "soar", "soars", "record high", "beats", "beat expectations", "rally", "rallies", "jumps",
             "gains", "rises", "growth", "upgrade", "boost", "rebound", "strong"]
TU_XAU_EN = ["plunge", "plunges", "slump", "slumps", "recession", "layoffs", "cuts jobs", "misses", "falls", "fall",
             "drops", "tumbles", "crash", "downgrade", "warning", "default", "bankruptcy", "inflation fears", "tariff", "war"]

_khoa = threading.Lock()
_cache: dict = {}


@dataclass
class Tin:
    tieu_de: str
    link: str
    nguon: str
    thoi_gian: pd.Timestamp | None
    tom_tat: str = ""
    ma: list = field(default_factory=list)
    cam_xuc: int = 0               # +1 tích cực, -1 tiêu cực, 0 trung tính

    @property
    def nhan(self):
        return {1: "Tích cực", -1: "Tiêu cực", 0: "Trung tính"}[self.cam_xuc]


def _tai(url: str) -> bytes:
    now = time.time()
    with _khoa:
        if url in _cache and now - _cache[url][0] < HAN_CACHE:
            return _cache[url][1]
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                               "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    with _khoa:
        _cache[url] = (now, raw)
    return raw


def _sach(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()


def cam_xuc(tieu_de: str, tom_tat: str = "", tieng_anh: bool = False) -> int:
    """Đếm từ khóa tốt/xấu trong tiêu đề (trọng số 2) và tóm tắt (trọng số 1)."""
    tot, xau = (TU_TOT_EN, TU_XAU_EN) if tieng_anh else (TU_TOT, TU_XAU)

    def dem(txt, ds):
        t = f" {txt.lower()} "
        return sum(1 for w in ds if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", t))
    diem = 2 * (dem(tieu_de, tot) - dem(tieu_de, xau)) + dem(tom_tat, tot) - dem(tom_tat, xau)
    return 1 if diem > 0 else (-1 if diem < 0 else 0)


_DS_MA: set | None = None


def danh_sach_ma() -> set:
    global _DS_MA
    if _DS_MA is None:
        try:
            from .du_lieu import FILE_MA
            _DS_MA = set(pd.read_csv(FILE_MA, dtype=str)["ma"])
        except Exception:
            _DS_MA = set()
    return _DS_MA


_TEN_MA: list | None = None
TU_CHUNG = {"công ty", "tập đoàn", "ngân hàng", "chứng khoán", "xây dựng", "đầu tư", "thương mại", "dịch vụ",
            "phát triển", "sản xuất", "cổ phần", "bất động sản", "thủy sản", "điện lực", "vận tải"}


def _ten_ma() -> list:
    """(tên ngắn công ty, mã) – chỉ tên đủ đặc trưng (≥ 5 ký tự, không phải cụm từ chung)."""
    global _TEN_MA
    if _TEN_MA is None:
        try:
            from .du_lieu import FILE_MA
            d = pd.read_csv(FILE_MA, dtype=str).dropna(subset=["ten"])
            _TEN_MA = [(t.strip(), m) for t, m in zip(d["ten"], d["ma"])
                       if len(t.strip()) >= 5 and t.strip().lower() not in TU_CHUNG and not t.strip().isupper()]
            _TEN_MA.sort(key=lambda x: -len(x[0]))
        except Exception:
            _TEN_MA = []
    return _TEN_MA


def tim_ma(txt: str) -> list[str]:
    """Mã cổ phiếu được nhắc trong câu: viết thẳng mã (FPT, HPG) hoặc tên công ty (Hòa Phát, Vietcombank)."""
    ds = danh_sach_ma()
    out = []
    for m in re.findall(r"(?<![A-Za-zÀ-ỹ0-9])([A-Z][A-Z0-9]{2})(?![A-Za-zÀ-ỹ0-9])", txt or ""):
        if m in ds and m not in KHONG_PHAI_MA and m not in out:
            out.append(m)
    for ten, m in _ten_ma():
        if m not in out and re.search(rf"(?<![\wÀ-ỹ]){re.escape(ten)}(?![\wÀ-ỹ])", txt or ""):
            out.append(m)
    return out


def doc_rss(raw: bytes, nguon: str) -> list[Tin]:
    root = ET.fromstring(raw)
    out = []
    for it in root.iter("item"):
        tieu_de = _sach(it.findtext("title") or "")
        nguon_tin = nguon
        src = it.find("source")
        if src is not None and src.text:                       # Google News: "Tiêu đề - Báo X"
            nguon_tin = src.text.strip()
            tieu_de = re.sub(rf"\s+-\s+{re.escape(nguon_tin)}$", "", tieu_de)
        tom_tat = _sach(it.findtext("description") or "")
        if nguon == "Google News":
            tom_tat = ""                                        # mô tả của Google chỉ lặp lại tiêu đề
        try:
            tg = pd.Timestamp(email.utils.parsedate_to_datetime(it.findtext("pubDate"))).tz_convert("Asia/Ho_Chi_Minh")
        except Exception:
            tg = None
        anh = nguon in TIENG_ANH
        out.append(Tin(tieu_de, (it.findtext("link") or "").strip(), nguon_tin, tg, tom_tat[:300],
                       [] if anh else tim_ma(tieu_de), cam_xuc(tieu_de, tom_tat, anh)))
    return out


def tin_thi_truong(nguon: list[str] | None = None, nhom: str = "Chứng khoán") -> list[Tin]:
    """Tin mới nhất của một nhóm (Chứng khoán / Kinh tế trong nước / Kinh tế thế giới), mới → cũ, bỏ trùng."""
    ds = []
    for ten, url in NHOM.get(nhom, RSS).items():
        if nguon and ten not in nguon:
            continue
        try:
            ds += doc_rss(_tai(url), ten)
        except Exception:
            continue
    return _gop(ds)


def tin_chu_de(chu_de: str, so: int = 30) -> list[Tin]:
    """Tin theo chủ đề vĩ mô (Google News): lãi suất, tỷ giá, Fed, giá vàng, giá dầu…"""
    q = CHU_DE.get(chu_de, chu_de)
    try:
        ds = doc_rss(_tai(GOOGLE.format(q=urllib.parse.quote(q))), "Google News")
    except Exception:
        return []
    return _gop(ds)[:so]


def tin_theo_ma(ma: str, ten_cong_ty: str | None = None, so: int = 20) -> list[Tin]:
    """Tin theo mã từ Google News (tìm "<mã> cổ phiếu" và tên công ty); giữ tin có nhắc đến mã/tên."""
    ds = []
    truy_van = [f'"{ma}" cổ phiếu']
    if ten_cong_ty:
        truy_van.append(f'"{ten_cong_ty}"')
    for q in truy_van:
        try:
            ds += doc_rss(_tai(GOOGLE.format(q=urllib.parse.quote(q))), "Google News")
        except Exception:
            continue
    ten = (ten_cong_ty or "").lower()
    ds = [t for t in ds if ma in t.ma or re.search(rf"\b{ma}\b", t.tieu_de) or (ten and ten in t.tieu_de.lower())]
    for t in ds:
        if ma not in t.ma:
            t.ma.insert(0, ma)
    return _gop(ds)[:so]


def _gop(ds: list[Tin]) -> list[Tin]:
    thay, out = set(), []
    for t in sorted(ds, key=lambda x: x.thoi_gian or pd.Timestamp(0, tz="Asia/Ho_Chi_Minh"), reverse=True):
        k = re.sub(r"\W+", "", t.tieu_de.lower())[:80]
        if k and k not in thay:
            thay.add(k)
            out.append(t)
    return out


def bang(ds: list[Tin]) -> pd.DataFrame:
    return pd.DataFrame([{"Thời gian": t.thoi_gian.strftime("%d/%m %H:%M") if t.thoi_gian is not None else "",
                          "Tin": t.tieu_de, "Đánh giá": t.nhan, "Mã": " ".join(t.ma), "Nguồn": t.nguon,
                          "Link": t.link} for t in ds])
