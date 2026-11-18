"""Kiểm tra web app Streamlit bằng dữ liệu giả lập (không cần mạng)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pd = pytest.importorskip("pandas")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from streamlit.testing.v1 import AppTest  # noqa: E402

from dudoan import du_lieu  # noqa: E402
from test_du_doan import gia_gia_lap  # noqa: E402


@pytest.fixture
def gia_gia(monkeypatch):
    def fake(ma, khung):
        loai, ma = du_lieu.phan_loai(ma)
        if ma == "LOI":
            raise RuntimeError("không có dữ liệu")
        freq = {"15m": "15min", "1H": "h", "4H": "4h"}.get(khung, "D")
        return gia_gia_lap(1.0 if hash(ma) % 2 else -1.0, n=600 if khung == "D" else 300, freq=freq)
    monkeypatch.setattr(du_lieu, "_tai", fake)
    du_lieu._CACHE.clear()


def test_tra_cuu_va_danh_sach(gia_gia):
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    assert not at.exception, at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "FPT" in md and ("Tăng" in md or "Giảm" in md or "Đi ngang" in md)
    assert len(at.tabs) == 2
    assert len(at.dataframe) == 1                       # bảng danh sách theo dõi

    at.text_input[0].set_value("EURUSD")
    at.button[0].click().run()                            # nút "Phân tích" của form
    assert not at.exception, at.exception
    assert any("EURUSD" in m.value for m in at.markdown)


def test_ma_loi_khong_lam_hong_app(gia_gia):
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    at.text_input[0].set_value("LOI")
    at.button[0].click().run()
    assert not at.exception, at.exception
    assert any("Không có dữ liệu" in m.value for m in at.markdown)
