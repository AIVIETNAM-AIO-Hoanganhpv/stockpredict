"""Tải dữ liệu giá: Yahoo Finance (forex, cổ phiếu quốc tế, cổ phiếu VN đuôi .VN),
vnstock (cổ phiếu VN, nếu đã cài) hoặc file CSV/Excel tự tải.

Kết quả luôn là DataFrame cột open, high, low, close, volume; index là thời gian.
"""
import datetime as dt
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
YAHOO_DAC_BIET = {"XAUUSD": "GC=F", "XAGUSD": "SI=F"}


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
    if len(up) == 6 and up[:3] in TIEN_TE and up[3:] in TIEN_TE:
        return "fx", up
    if up in CHI_SO_VN or (len(up) == 3 and up.isalpha()):
        return "vn", up
    return "intl", up


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


def yahoo_symbol(loai: str, ma: str) -> str:
    if loai == "fx":
        return YAHOO_DAC_BIET.get(ma, f"{ma}=X")
    if loai == "vn":
        return {"VN30": "E1VFVN30.VN"}.get(ma, f"{ma}.VN")   # VN30 → quỹ ETF mô phỏng VN30
    return ma


_CACHE: dict = {}


def tai(ma: str, khung: str) -> pd.DataFrame:
    """Tải dữ liệu cho một mã và một khung. Cổ phiếu VN: thử vnstock trước, rồi Yahoo.
    Khung W/M được dựng lại từ dữ liệu ngày để giá giữa các khung luôn khớp nhau."""
    if khung in ("W", "M"):
        return resample(tai(ma, "D"), khung)
    key = (ma.upper(), khung)
    if key not in _CACHE:
        _CACHE[key] = _tai(ma, khung)
    return _CACHE[key]


def _tai(ma: str, khung: str) -> pd.DataFrame:
    loai, ma = phan_loai(ma)
    loi = []
    if loai == "vn" and khung in ("D", "W", "M"):
        try:
            return _vnstock(ma, khung)
        except Exception as e:
            loi.append(str(e))
    if loai == "vn" and ma in CHI_SO_VN and ma != "VN30":
        raise RuntimeError(f"Chỉ số {ma} cần thư viện vnstock (py -m pip install vnstock). " + " | ".join(loi))
    try:
        return _yahoo(yahoo_symbol(loai, ma), khung)
    except Exception as e:
        loi.append(str(e))
    raise RuntimeError(f"Không tải được {ma} khung {khung}: " + " | ".join(loi))
