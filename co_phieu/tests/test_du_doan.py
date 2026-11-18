"""Kiểm tra công cụ dự đoán bằng dữ liệu giả lập (không cần mạng)."""
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dudoan import bao_cao, cau_truc, chi_bao, du_lieu, fibo, phan_tich  # noqa: E402


def gia_gia_lap(xu_huong=1.0, n=300, seed=1, vol=True, freq="D"):
    """Giá đi theo sóng: xu hướng + dao động hình sin + nhiễu."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    base = 100 + xu_huong * 0.25 * t + 3 * np.sin(t / 6) + rng.normal(0, 0.4, n).cumsum() * 0.2
    close = base
    open_ = np.r_[base[0], base[:-1]] + rng.normal(0, 0.2, n)
    high = np.maximum(open_, close) + rng.uniform(0.1, 0.8, n)
    low = np.minimum(open_, close) - rng.uniform(0.1, 0.8, n)
    volume = rng.uniform(1e5, 2e5, n) if vol else np.zeros(n)
    idx = pd.date_range("2024-01-01", periods=n, freq=freq)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                         "volume": volume}, index=idx)


def test_chi_bao_trong_khoang():
    df = gia_gia_lap()
    s = chi_bao.stoch(df).dropna()
    assert s["k"].between(0, 100).all()
    m = chi_bao.mfi(df).dropna()
    assert m.between(0, 100).all()
    a = chi_bao.adx(df).dropna()
    assert a["adx"].between(0, 100).all()
    assert a["pdi"].iloc[-1] > a["mdi"].iloc[-1]          # xu hướng tăng: +DI > -DI
    assert chi_bao.macd(df)["macd"].iloc[-1] > 0


def test_mfi_khong_co_khoi_luong():
    df = gia_gia_lap(vol=False)
    assert chi_bao.mfi(df).isna().all()
    kq = phan_tich.phan_tich_khung(df, "4H")
    assert any("MFI" in g for g in kq.ghi_chu)


@pytest.mark.parametrize("chieu,mong_doi", [(1.0, 1), (-1.0, -1)])
def test_du_doan_theo_xu_huong(chieu, mong_doi):
    df = gia_gia_lap(chieu)
    kq = phan_tich.phan_tich_khung(df, "D")
    assert kq.xu_huong == mong_doi, [(v.ten, v.gia_tri, v.ly_do) for v in kq.votes]
    assert kq.cau_truc.trend == mong_doi


def test_di_ngang():
    rng = np.random.default_rng(3)
    n = 300
    t = np.arange(n)
    close = 100 + 4 * np.sin(t / 5) + rng.normal(0, 0.3, n)
    df = pd.DataFrame({"open": close + rng.normal(0, 0.3, n), "close": close,
                       "high": close + 1, "low": close - 1, "volume": 1e5},
                      index=pd.date_range("2024-01-01", periods=n))
    kq = phan_tich.phan_tich_khung(df, "D")
    assert abs(kq.diem) < 60


def test_fvg_va_order_block():
    # 30 nến đi ngang rồi một cú bật mạnh tạo khoảng trống giá
    rows = [(100, 101 - (i % 3) * 0.3, 99 + (i % 4) * 0.2, 100.2 if i % 2 else 99.8) for i in range(30)]
    rows += [(100, 100.5, 99, 99.2),           # nến giảm cuối trước bứt phá → OB tăng
             (99.3, 103, 99.2, 102.8),
             (103.5, 106, 103.4, 105.8),       # low 103.4 > high 101 hai nến trước → FVG
             (105.8, 107, 105.5, 106.5)]
    rows += [(106.5, 107.5, 105.8, 107) for _ in range(5)]
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    df["volume"] = 1.0
    st = cau_truc.analyze(df, k=2, atr_val=1.0)
    assert any(z.side == 1 for z in st.fvgs)
    assert any(e[2] == 1 for e in st.events)
    assert any(z.side == 1 and z.kind == "OB" for z in st.order_blocks)


def test_fibo_theo_tai_lieu():
    # Nhịp tăng 100 → 200, hồi về 161.8 (hồi 38,2%) → chốt lời 1.618
    p = fibo.plan(200, 100, 161.8, up=True)
    assert p.depth == pytest.approx(0.382, abs=1e-3)
    assert p.tp1 == pytest.approx(161.8 + 161.8)
    # Hồi 61,8% → 1.272
    p = fibo.plan(200, 100, 138.2, up=True)
    assert p.tp1 == pytest.approx(138.2 + 127.2)
    # Xu hướng giảm: 200 → 100, hồi lên 150 (50%) → 1.272, phụ 1.0
    p = fibo.plan(200, 100, 150, up=False)
    assert p.tp1 == pytest.approx(150 - 127.2) and p.tp2 == pytest.approx(50)
    assert fibo.retracement_levels(200, 100, True)[0.5] == 150


@pytest.mark.parametrize("ma,loai", [("FPT", "vn"), ("VNINDEX", "vn"), ("EURUSD", "fx"),
                                     ("XAUUSD", "fx"), ("AAPL", "intl"), ("us:IBM", "intl"),
                                     ("eur/usd", "fx"), ("vn:VNM", "vn")])
def test_phan_loai(ma, loai):
    assert du_lieu.phan_loai(ma)[0] == loai


def test_yahoo_symbol():
    assert du_lieu.yahoo_symbol("fx", "EURUSD") == "EURUSD=X"
    assert du_lieu.yahoo_symbol("fx", "XAUUSD") == "GC=F"
    assert du_lieu.yahoo_symbol("vn", "FPT") == "FPT.VN"
    assert du_lieu.yahoo_symbol("vn", "VN30") == "E1VFVN30.VN"


def test_doc_file_tieng_viet(tmp_path):
    df = gia_gia_lap(n=50)
    out = df.reset_index().rename(columns={"index": "Ngày", "open": "Mở", "high": "Cao",
                                           "low": "Thấp", "close": "Đóng", "volume": "KL"})
    out["Ngày"] = out["Ngày"].dt.strftime("%d/%m/%Y")
    p = tmp_path / "gia.csv"
    out.to_csv(p, index=False)
    back = du_lieu.doc_file(p)
    assert list(back.columns) == ["open", "high", "low", "close", "volume"]
    assert len(back) == 50 and back.index[1].day == 2


def test_doc_danh_sach(tmp_path):
    p = tmp_path / "ma.txt"
    p.write_text("# ghi chú\nFPT HPG\n\nEURUSD, XAUUSD  # vàng\n", encoding="utf-8")
    assert du_lieu.doc_danh_sach(p) == ["FPT", "HPG", "EURUSD", "XAUUSD"]


def test_tong_hop_va_bao_cao(tmp_path):
    df = gia_gia_lap(1.0)
    ds = [phan_tich.phan_tich_khung(du_lieu.resample(df, k), k) for k in ("M", "W")]
    ds.append(phan_tich.phan_tich_khung(df, "D"))
    kq = phan_tich.tong_hop("FPT", "vn", ds)
    assert kq.xu_huong == 1 and kq.chinh.khung == "D"
    tl = phan_tich.kiem_tra_qua_khu(df, "D", so_nen=40)
    assert tl["tin_hieu"] > 0
    path = bao_cao.ghi(tmp_path, [kq], {"FPT": df}, {"FPT": tl})
    assert path.exists()
    assert "FPT" in (tmp_path / "README.md").read_text(encoding="utf-8")
    assert (tmp_path / "FPT.html").read_text(encoding="utf-8").count("plotly") > 0
    assert (tmp_path / "tom_tat.xlsx").exists()
    assert "TĂNG" in bao_cao.van_ban(kq)


def test_cli_voi_file(tmp_path, capsys):
    import du_doan
    p = tmp_path / "gia.csv"
    gia_gia_lap(-1.0, n=300).reset_index(names="date").to_csv(p, index=False)
    rc = du_doan.main(["--file", str(p), "--ten", "ABC", "--bao-cao", "--thu-muc", str(tmp_path / "bc")])
    out = capsys.readouterr().out
    assert rc == 0 and "ABC" in out and "GIẢM" in out
    assert (tmp_path / "bc" / "ABC.html").exists()
