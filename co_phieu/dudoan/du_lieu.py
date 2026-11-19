"""Tải dữ liệu giá:
  • Vietcap (trading.vietcap.com.vn) – cổ phiếu & chỉ số VN, toàn bộ HOSE/HNX/UPCoM (giá đã điều chỉnh)
  • VNDirect (dchart-api.vndirect.com.vn) – dự phòng khi Vietcap chặn (VD: Streamlit Cloud)
  • vnstock (nếu đã cài) – dự phòng cho cổ phiếu VN
  • Yahoo Finance – forex, vàng, cổ phiếu quốc tế (và dự phòng cho cổ phiếu VN, đuôi .VN)
  • file CSV/Excel tự tải.

Kết quả luôn là DataFrame cột open, high, low, close, volume; index là thời gian.
"""
import datetime as dt
import gzip
import json
import re
import time
import urllib.request
from pathlib import Path

import pandas as pd

TIEN_TE = {"USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "CNY", "SGD", "HKD", "VND",
           "XAU", "XAG"}
CHI_SO_VN = {"VNINDEX", "VN30", "HNXINDEX", "HNX30", "UPCOMINDEX", "HNX", "UPCOM"}

# Khung theo tài liệu LEVEL 1 (+15m cho forex theo ICT), xếp từ lớn đến nhỏ
KHUNG = {
    "vn": ["M", "W", "D"],
    "intl": ["M", "W", "D"],
    "fx": ["W", "D", "4H", "1H", "15m"],
}

# Hàng hoá trên Yahoo (giá vàng/bạc giao ngay không ổn định → dùng hợp đồng tương lai)
YAHOO_DAC_BIET = {"XAUUSD": "GC=F", "XAGUSD": "SI=F",
                  # dầu thô (hợp đồng tương lai): WTI và Brent – gõ tên nào cũng được
                  "USOIL": "CL=F", "WTI": "CL=F", "XTIUSD": "CL=F", "UKOIL": "BZ=F", "BRENT": "BZ=F", "XBRUSD": "BZ=F",
                  "GOLD": "GC=F", "SILVER": "SI=F"}
# Tiền mã hoá: BTCUSD / BTCUSDT / BTC → BTC-USD trên Yahoo
CRYPTO = ("BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "TRX", "TON", "AVAX", "LINK", "DOT", "LTC", "SHIB")
for _c in CRYPTO:
    for _k in (_c + "USD", _c + "USDT"):
        YAHOO_DAC_BIET[_k] = _c + "-USD"
# Mã VN có số/chữ dài: chứng chỉ quỹ ETF (E1VFVN30, FUEVFVND…), chứng quyền (CFPT2501…)
_MAU_VN_KHAC = re.compile(r"^(E1VF[A-Z0-9]+|FUE[A-Z0-9]+|C[A-Z]{3}\d{4})$")


def phan_loai(ma: str) -> tuple[str, str]:
    """Trả về (loại, mã chuẩn). Loại: 'vn', 'fx', 'intl'.

    Có thể ghi rõ tiền tố: vn:FPT, fx:EURUSD, us:AAPL (hoặc yf:^GSPC).
    Tự đoán: cặp 6 chữ cái từ mã tiền tệ → fx; chỉ số VN hoặc mã 3 chữ cái → vn; còn lại → intl.
    """
    ma = ma.strip()
    if ":" in ma:
        pre, rest = ma.split(":", 1)
        pre = pre.lower()
        return ({"vn": "vn", "fx": "fx"}.get(pre, "intl"), rest.strip().upper())
    up = ma.upper().replace("/", "")
    if up in YAHOO_DAC_BIET:                       # vàng, bạc, dầu → như forex (có khung 4H/1H/15m)
        return "fx", up
    if len(up) == 6 and up[:3] in TIEN_TE and up[3:] in TIEN_TE:
        return "fx", up
    if up in CHI_SO_VN or up in _ma_vn() or _MAU_VN_KHAC.match(up):                # mọi mã đang niêm yết (kể cả mã có số: NT2, PC1, C69…)
        return "vn", up
    if len(up) == 3 and up.isalpha() and not _ma_vn():  # chưa có danh sách mã → đoán theo 3 chữ cái
        return "vn", up
    return "intl", up


_MA_VN: set | None = None


def _ma_vn() -> set:
    """Tập mã cổ phiếu VN đang niêm yết (từ du_lieu_ma/ma_vn.csv)."""
    global _MA_VN
    if _MA_VN is None:
        try:
            _MA_VN = set(pd.read_csv(FILE_MA, dtype=str)["ma"].str.upper())
        except Exception:
            _MA_VN = set()
    return _MA_VN


def doc_danh_sach(path) -> list[str]:
    """Đọc ma.txt: mỗi dòng một mã, dòng bắt đầu bằng # là ghi chú."""
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.extend(x for x in line.replace(",", " ").split() if x)
    return out


def _doc_ngay(col: pd.Series) -> pd.Series:
    """Ngày dạng 2024-01-31 (ISO) hoặc 31/01/2024 (kiểu Việt Nam)."""
    if pd.api.types.is_datetime64_any_dtype(col):
        d = col
    else:
        d = pd.to_datetime(col, errors="coerce", format="ISO8601")
        if d.isna().mean() > 0.2:
            d = pd.to_datetime(col, errors="coerce", dayfirst=True)
    if getattr(d.dt, "tz", None) is not None:
        d = d.dt.tz_convert("UTC").dt.tz_localize(None)
    return d


def _chuan_hoa(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1) if df.columns.nlevels > 1 else df
    ten = {
        "time": "date", "datetime": "date", "ngay": "date", "ngày": "date", "date": "date",
        "open": "open", "mo": "open", "mở": "open", "giá mở cửa": "open",
        "high": "high", "cao": "high", "cao nhất": "high", "giá cao nhất": "high",
        "low": "low", "thap": "low", "thấp": "low", "thấp nhất": "low", "giá thấp nhất": "low",
        "close": "close", "dong": "close", "đóng": "close", "đóng cửa": "close",
        "giá đóng cửa": "close", "adj close": "adj_close",
        "volume": "volume", "kl": "volume", "khối lượng": "volume", "khoi luong": "volume",
    }
    df = df.rename(columns=lambda c: ten.get(str(c).strip().lower(), str(c).strip().lower()))
    if "date" in df.columns:
        df["date"] = _doc_ngay(df["date"])
        df = df.dropna(subset=["date"]).set_index("date")
    if "volume" not in df.columns:
        df["volume"] = 0.0
    df = df[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["close"]).sort_index()
    return df[~df.index.duplicated(keep="last")]


def resample(df: pd.DataFrame, khung: str) -> pd.DataFrame:
    rule = {"4H": "4h", "W": "W-FRI", "M": "ME"}[khung]
    out = df.resample(rule).agg({"open": "first", "high": "max", "low": "min",
                                 "close": "last", "volume": "sum"})
    return out.dropna(subset=["close"])


def doc_file(path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        raw = pd.read_excel(path)
    else:
        raw = pd.read_csv(path, sep=None, engine="python")
    return _chuan_hoa(raw)


# ----------------------------------------------------------------------------------------
def _yahoo(sym: str, khung: str) -> pd.DataFrame:
    import yfinance as yf
    cfg = {"15m": ("15m", "60d"), "1H": ("60m", "730d"), "4H": ("60m", "730d"),
           "D": ("1d", "10y"), "W": ("1wk", "10y"), "M": ("1mo", "max")}[khung]
    raw = yf.download(sym, interval=cfg[0], period=cfg[1], progress=False, auto_adjust=False,
                      threads=False)
    if raw is None or raw.empty:
        raise RuntimeError(f"Yahoo không có dữ liệu cho {sym}")
    df = _chuan_hoa(raw.reset_index())
    if khung == "4H":
        df = resample(df, "4H")
    return df if khung == "D" else df.iloc[-1500:]


def _vnstock(ma: str, khung: str) -> pd.DataFrame:
    from vnstock import Vnstock  # thư viện tuỳ chọn: py -m pip install vnstock
    end = dt.date.today()
    start = end - dt.timedelta(days=10 * 365)
    last_err = None
    for src in ("VCI", "TCBS"):
        try:
            q = Vnstock().stock(symbol=ma, source=src).quote
            raw = q.history(start=start.isoformat(), end=end.isoformat(), interval="1D")
            df = _chuan_hoa(raw)
            return df if khung == "D" else resample(df, khung)
        except Exception as e:  # thử nguồn tiếp theo
            last_err = e
    raise RuntimeError(f"vnstock lỗi: {last_err}")


# ------------------------------------------------------------------------- Vietcap
VCI_API = "https://trading.vietcap.com.vn/api/"
VCI_KHUNG = {"D": "ONE_DAY", "1H": "ONE_HOUR", "15m": "ONE_MINUTE"}
SAN = {"HSX": "HOSE", "HNX": "HNX", "UPCOM": "UPCoM"}
FILE_MA = Path(__file__).resolve().parent.parent / "du_lieu_ma" / "ma_vn.csv"

# Ngành cấp 2 theo chuẩn ICB (mã icbCode2 của Vietcap)
NGANH = {
    "0500": "Dầu khí", "1300": "Hóa chất", "1700": "Tài nguyên cơ bản", "2300": "Xây dựng & Vật liệu",
    "2700": "Hàng & Dịch vụ công nghiệp", "3300": "Ô tô & Phụ tùng", "3500": "Thực phẩm & Đồ uống",
    "3700": "Hàng cá nhân & Gia dụng", "4500": "Y tế", "5300": "Bán lẻ", "5500": "Truyền thông",
    "5700": "Du lịch & Giải trí", "6500": "Viễn thông", "7500": "Tiện ích (điện, nước, khí)",
    "8300": "Ngân hàng", "8500": "Bảo hiểm", "8600": "Bất động sản", "8700": "Dịch vụ tài chính",
    "9500": "Công nghệ thông tin",
}


def _vci_goi(duong_dan: str, body: dict | None = None, timeout: int = 30):
    req = urllib.request.Request(
        VCI_API + duong_dan, data=json.dumps(body).encode() if body is not None else None,
        method="POST" if body is not None else "GET",
        headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
    return json.loads(raw)


def _vci(ma: str, khung: str = "D", so_nen: int = 1300) -> pd.DataFrame:
    """Giá một mã từ Vietcap (mỗi lần gọi chỉ được 1 mã)."""
    res = _vci_goi("chart/OHLCChart/gap-chart", {
        "timeFrame": VCI_KHUNG[khung], "symbols": [ma],
        "to": int(time.time()) + 86400, "countBack": so_nen})
    if not res or not res[0].get("c"):
        raise RuntimeError(f"Vietcap không có dữ liệu cho {ma}")
    x = res[0]
    df = pd.DataFrame({"open": x["o"], "high": x["h"], "low": x["l"], "close": x["c"],
                       "volume": x["v"]},
                      index=pd.to_datetime([int(t) for t in x["t"]], unit="s"))
    if khung == "D":
        df.index = df.index.normalize()
    df = df.apply(pd.to_numeric, errors="coerce").dropna(subset=["close"]).sort_index()
    return df[~df.index.duplicated(keep="last")]


def danh_sach_ma_vn(san=("HSX", "HNX", "UPCOM"), lam_moi: bool = False) -> pd.DataFrame:
    """Toàn bộ cổ phiếu đang niêm yết: cột ma, san, ten, nganh. Lưu sẵn vào du_lieu_ma/ma_vn.csv
    để vẫn dùng được khi mất mạng."""
    df = None
    if lam_moi or not FILE_MA.exists():
        try:
            raw = _vci_goi("price/symbols/getAll")
            df = pd.DataFrame([{"ma": x["symbol"], "san": x["board"],
                                "ten": x.get("organShortName") or x.get("organName") or "",
                                "nganh": NGANH.get(str(x.get("icbCode2") or ""), "Khác")}
                               for x in raw if x.get("type") == "STOCK"
                               and x.get("board") in SAN and len(x.get("symbol", "")) == 3])
            df = df.sort_values(["san", "ma"]).reset_index(drop=True)
            FILE_MA.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(FILE_MA, index=False, encoding="utf-8")
        except Exception:
            df = None
    if df is None:
        df = pd.read_csv(FILE_MA, encoding="utf-8", dtype=str)
    if "nganh" not in df.columns:
        df["nganh"] = "Khác"
    return df[df["san"].isin(san)].reset_index(drop=True)


_SAN_CUA: dict = {}


def san_cua(ma: str) -> str:
    """Sàn niêm yết của mã VN (HSX / HNX / UPCOM), theo du_lieu_ma/ma_vn.csv; '' nếu không rõ."""
    if not _SAN_CUA and FILE_MA.exists():
        try:
            d = pd.read_csv(FILE_MA, encoding="utf-8", dtype=str)
            _SAN_CUA.update(zip(d["ma"], d["san"]))
        except Exception:
            pass
    return _SAN_CUA.get(ma.upper(), "")


def yahoo_symbol(loai: str, ma: str) -> str:
    if loai == "fx":
        return YAHOO_DAC_BIET.get(ma, f"{ma}=X")
    if loai == "vn":
        return {"VN30": "E1VFVN30.VN"}.get(ma, f"{ma}.VN")   # VN30 → quỹ ETF mô phỏng VN30
    return ma


# ------------------------------------------------------------------------- VNDirect (dự phòng)
VND_API = "https://dchart-api.vndirect.com.vn/dchart/history"
VND_KHUNG = {"D": ("D", 86400 * 1.6), "1H": ("60", 3600 * 6), "15m": ("15", 900 * 20)}


def _vnd(ma: str, khung: str = "D", so_nen: int = 1300) -> pd.DataFrame:
    """Giá một mã từ VNDirect – dùng khi Vietcap chặn (VD: máy chủ Streamlit Cloud bị 403).
    VNDirect tính giá cổ phiếu theo nghìn đồng → nhân 1000 cho khớp Vietcap (chỉ số giữ nguyên)."""
    res, giay = VND_KHUNG[khung]
    den = int(time.time()) + 86400
    ten = {"HNXINDEX": "HNX", "UPCOMINDEX": "UPCOM"}.get(ma, ma)
    url = f"{VND_API}?resolution={res}&symbol={ten}&from={int(den - so_nen * giay)}&to={den}"
    req = urllib.request.Request(url, headers={"Accept": "*/*", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    try:
        x = json.loads(raw)
    except ValueError:
        raise RuntimeError(f"VNDirect trả về dữ liệu lạ cho {ma}") from None
    if x.get("s") != "ok" or not x.get("c"):
        raise RuntimeError(f"VNDirect không có dữ liệu cho {ma}")
    df = pd.DataFrame({"open": x["o"], "high": x["h"], "low": x["l"], "close": x["c"], "volume": x["v"]},
                      index=pd.to_datetime([int(t) for t in x["t"]], unit="s"))
    if khung == "D":
        df.index = df.index.normalize()
    df = df.apply(pd.to_numeric, errors="coerce").dropna(subset=["close"]).sort_index()
    if ma not in CHI_SO_VN:
        df[["open", "high", "low", "close"]] = (df[["open", "high", "low", "close"]] * 1000).round(0)
    return df[~df.index.duplicated(keep="last")].iloc[-so_nen:]


_CACHE: dict = {}
HAN_CACHE = 300          # giây: dữ liệu tải về được dùng lại trong 5 phút


def tai(ma: str, khung: str) -> pd.DataFrame:
    """Tải dữ liệu cho một mã và một khung. Cổ phiếu VN: Vietcap → VNDirect → vnstock → Yahoo.
    Khung W/M được dựng lại từ dữ liệu ngày để giá giữa các khung luôn khớp nhau."""
    if khung in ("W", "M"):
        return resample(tai(ma, "D"), khung)
    key = (ma.upper(), khung)
    now = time.monotonic()
    if key not in _CACHE or now - _CACHE[key][0] > HAN_CACHE:
        _CACHE[key] = (now, _tai(ma, khung))
    return _CACHE[key][1]


def _tai(ma: str, khung: str) -> pd.DataFrame:
    loai, ma = phan_loai(ma)
    loi = []
    if loai == "vn":
        try:
            return _vci(ma, khung)
        except Exception as e:
            loi.append(f"Vietcap: {e}")
        try:
            return _vnd(ma, khung)
        except Exception as e:
            loi.append(f"VNDirect: {e}")
        if khung == "D":
            try:
                return _vnstock(ma, khung)
            except Exception as e:
                loi.append(f"vnstock: {e}")
        if ma in CHI_SO_VN and ma != "VN30":
            raise RuntimeError(f"Không tải được chỉ số {ma}: " + " | ".join(loi))
    try:
        return _yahoo(yahoo_symbol(loai, ma), khung)
    except Exception as e:
        loi.append(str(e))
    raise RuntimeError(f"Không tải được {ma} khung {khung}: " + " | ".join(loi))
