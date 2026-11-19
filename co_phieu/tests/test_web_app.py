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


def nut(at, nhan):
    return next(b for b in at.button if nhan in b.label)


def test_tra_cuu_va_danh_sach(gia_gia):
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    assert not at.exception, at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "FPT" in md and ("Tăng" in md or "Giảm" in md or "Đi ngang" in md)
    assert len(at.tabs) == 4
    assert len(at.dataframe) >= 2                       # danh mục + danh sách theo dõi

    at.text_input[0].set_value("EURUSD")
    nut(at, "Phân tích").click().run()
    assert not at.exception, at.exception
    assert any("EURUSD" in m.value for m in at.markdown)


def test_ma_loi_khong_lam_hong_app(gia_gia):
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    at.text_input[0].set_value("LOI")
    nut(at, "Phân tích").click().run()
    assert not at.exception, at.exception
    assert any("Không có dữ liệu" in m.value for m in at.markdown)



def test_quet_thi_truong_tren_web(gia_gia, monkeypatch):
    ds = pd.DataFrame({"ma": ["AAA", "BBB"], "san": ["HSX", "HNX"], "ten": ["A", "B"],
                       "nganh": ["Ngân hàng", "Bất động sản"]})
    monkeypatch.setattr(du_lieu, "danh_sach_ma_vn", lambda san=None, lam_moi=False: ds[ds.san.isin(san)])

    def fake_vci(ma, khung="D", so_nen=1300):
        df = gia_gia_lap(1.0 if ma == "AAA" else -0.3, n=900)
        df.index = pd.date_range(end=pd.Timestamp.now().normalize(), periods=len(df))
        return df * [250, 250, 250, 250, 1e4]
    monkeypatch.setattr(du_lieu, "_vci", fake_vci)
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    nut(at, "Quét toàn thị trường").click().run()
    assert not at.exception, at.exception
    assert any("quét 2 mã" in c.value for c in at.caption)
    for che_do in ("🔴 Bán ở đỉnh", "🏭 Sức mạnh ngành"):
        at.radio(key="xem").set_value(che_do).run()
        assert not at.exception, (che_do, at.exception)
    assert any("Ngân hàng" in str(df.value) for df in at.dataframe)


def test_tra_cuu_ma_trung_danh_sach_theo_doi(gia_gia):
    """Mã vừa tra cứu vừa có trong tab Theo dõi → không được trùng ID biểu đồ."""
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    at.text_input[0].set_value("VNINDEX")
    nut(at, "Phân tích").click().run()
    assert not at.exception, at.exception
