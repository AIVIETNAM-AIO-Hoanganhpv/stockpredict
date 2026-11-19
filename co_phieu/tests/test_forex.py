"""Forex: pip, giá trị pip, lot theo % rủi ro (công thức cBot của người dùng) – không gọi mạng."""
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dudoan import du_lieu, forex as F  # noqa: E402


def test_thong_so():
    assert F.thong_so("EURUSD").pip == 0.0001 and F.thong_so("EURUSD").lot == 100_000
    assert F.thong_so("USDJPY").pip == 0.01
    assert F.thong_so("XAUUSD").lot == 100 and F.thong_so("XAUUSD").pip == 0.01
    assert F.thong_so("BTCUSD").loai == "crypto"


def test_gia_tri_pip():
    assert F.gia_tri_pip_lot("EURUSD", 1.10) == pytest.approx(10.0)          # 10 USD/pip/lot
    assert F.gia_tri_pip_lot("USDJPY", 150.0) == pytest.approx(1000 / 150)   # ≈ 6,67 USD
    assert F.gia_tri_pip_lot("XAUUSD", 3700) == pytest.approx(1.0)           # 0,01 × 100 oz


def test_gia_tri_pip_cap_cheo(monkeypatch):
    def tai(ma, khung):
        assert ma in ("JPYUSD", "USDJPY")
        if ma == "JPYUSD":
            raise RuntimeError("không có")
        return pd.DataFrame({"close": [150.0]})
    monkeypatch.setattr(du_lieu, "tai", tai)
    assert F.gia_tri_pip_lot("GBPJPY", 200.0) == pytest.approx(1000 / 150)


def test_khoi_luong_giong_cbot():
    # 10.000 USD, rủi ro 1% = 100 USD, SL 20 pip EURUSD (10 USD/pip/lot) → 0,5 lot
    k = F.khoi_luong("EURUSD", 1.10, 0.0020, 10_000, 1.0)
    assert k["lot"] == pytest.approx(0.5) and k["rui_ro_thuc"] == pytest.approx(100)
    # trần rủi ro 50 USD → 0,25 lot
    assert F.khoi_luong("EURUSD", 1.10, 0.0020, 10_000, 1.0, rui_ro_toi_da_usd=50)["lot"] == pytest.approx(0.25)
    # làm tròn XUỐNG: 100 / (30 × 10) = 0,333 → 0,33
    assert F.khoi_luong("EURUSD", 1.10, 0.0030, 10_000, 1.0)["lot"] == pytest.approx(0.33)
    # vàng: SL 50 USD/oz = 5000 pip × 1 USD → 0,02 lot
    assert F.khoi_luong("XAUUSD", 3700, 50.0, 10_000, 1.0)["lot"] == pytest.approx(0.02)
    # lot tối thiểu vượt rủi ro → cảnh báo bỏ lệnh
    k = F.khoi_luong("XAUUSD", 3700, 200.0, 1_000, 1.0)
    assert k["lot"] == 0.01 and k["vuot_gioi_han"] and "BỎ LỆNH" in k["canh_bao"]
