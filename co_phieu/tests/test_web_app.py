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
    assert {"🏠 Hôm nay", "🔍 Tra cứu mã", "💼 Danh mục của tôi", "🧰 Nâng cao"} <= {t.label for t in at.tabs}
    assert any(x in md for x in ("NÊN MUA", "KHÔNG MUA", "CHỜ", "CHƯA NÊN MUA"))   # thẻ kết luận rõ ràng
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


def test_tra_cuu_doanh_nghiep_fpt(gia_gia):
    """FPT có dữ liệu doanh nghiệp mẫu → mục Doanh nghiệp (hồ sơ, chỉ số, BCTC) và Tin tức."""
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    assert not at.exception, at.exception
    nhan = [t.label for t in at.tabs]
    assert {"📈 Biểu đồ", "🏢 Doanh nghiệp", "📰 Tin tức", "🔬 Chi tiết chỉ báo"} <= set(nhan)
    assert any("Báo cáo tài chính" in e.label for e in at.expander)
    assert any("Lịch sử trả cổ tức" in e.label for e in at.expander)
    assert any("Công ty con" in e.label for e in at.expander)
    md = " ".join(m.value for m in at.markdown)
    assert "Công ty Cổ phần FPT" in md and "Sức khỏe tài chính" in md
    assert any("CTCK" in i.value for i in at.info)
    # đổi sang báo cáo quý, cân đối kế toán
    at.radio(key="bctc_ky_tra_cuu_FPT").set_value("Quý").run()
    at.selectbox(key="bctc_phan_tra_cuu_FPT").set_value("cdkt").run()
    assert not at.exception, at.exception


def test_bo_loc_sau_khi_quet(gia_gia, monkeypatch):
    ds = pd.DataFrame({"ma": ["AAA", "FPT"], "san": ["HSX", "HSX"], "ten": ["A", "FPT"],
                       "nganh": ["Ngân hàng", "Công nghệ thông tin"]})
    monkeypatch.setattr(du_lieu, "danh_sach_ma_vn", lambda san=None, lam_moi=False: ds[ds.san.isin(san)])

    def fake_vci(ma, khung="D", so_nen=1300):
        df = gia_gia_lap(1.0, n=900)
        df.index = pd.date_range(end=pd.Timestamp.now().normalize(), periods=len(df))
        return df * [250, 250, 250, 250, 1e4]
    monkeypatch.setattr(du_lieu, "_vci", fake_vci)
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    nut(at, "Quét toàn thị trường").click().run()
    assert not at.exception, at.exception
    at.radio(key="nang_cao").set_value("🔎 Bộ lọc cơ bản").run()
    at.slider[0].set_value(1.0).run()
    assert not at.exception, at.exception
    assert any(m.label == "Số mã đạt" for m in at.metric)


def test_tin_thi_truong_loc(gia_gia):
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    at.radio(key="nang_cao").set_value("📰 Tin thị trường").run()
    md = " ".join(m.value for m in at.markdown)
    assert "news.google.com" in md or "cafef" in md.lower()
    at.text_input(key="tin_tk").set_value("FPT").run()
    at.checkbox(key="tin_ma").check().run()
    assert not at.exception, at.exception


def test_tin_kinh_te_va_chu_de(gia_gia):
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=120).run()
    at.radio(key="nang_cao").set_value("📰 Tin thị trường").run()
    for nhom in ("Kinh tế trong nước", "Kinh tế thế giới", "Chủ đề vĩ mô"):
        at.radio(key="tin_nhom").set_value(nhom).run()
        assert not at.exception, (nhom, at.exception)
    at.radio(key="tin_cd").set_value("Giá vàng").run()
    assert not at.exception, at.exception


def test_tab_theo_ngay(gia_gia):
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=180).run()
    assert not at.exception, at.exception
    at.radio(key="nang_cao").set_value("📅 Khuyến nghị theo ngày").run()
    assert not at.exception, at.exception
    if LS_CO_BAN():
        for che_do in ("🔁 Thay đổi so với phiên trước", "🗓 Lịch sắp tới", "📜 Lịch sử khuyến nghị"):
            at.radio(key="xem_ngay").set_value(che_do).run()
            assert not at.exception, (che_do, at.exception)


def LS_CO_BAN():
    import os
    from dudoan import lich_su
    return bool(lich_su.ds_ngay(Path(os.environ["CO_PHIEU_BAO_CAO"]) / "lich_su"))


def test_nguon_doanh_nghiep_loi_khong_lam_dung_app(gia_gia, monkeypatch):
    """Như trên Streamlit Cloud: API doanh nghiệp trả 403 → chỉ báo trong mục đó, app vẫn chạy."""
    import urllib.error
    from dudoan import co_ban

    def loi(duong_dan):
        raise urllib.error.HTTPError(duong_dan, 403, "Forbidden", {}, None)
    monkeypatch.setattr(co_ban, "_goi", loi)
    co_ban._bo_nho.clear()
    import streamlit as st
    st.cache_data.clear()            # bỏ kết quả đã lưu tạm từ các test trước
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=180).run()
    assert not at.exception, at.exception
    assert any("mã lỗi 403" in i.value for i in at.info)


def test_doanh_nghiep_du_phong_vndirect(gia_gia, monkeypatch):
    """Vietcap chặn (403) nhưng VNDirect trả lời → hiện bản tóm tắt doanh nghiệp + chỉ số từ VNDirect."""
    import urllib.error
    from dudoan import co_ban

    def goi(duong_dan):
        if "vndirect" not in duong_dan:
            raise urllib.error.HTTPError(duong_dan, 403, "Forbidden", {}, None)
        if "company_profiles" in duong_dan:
            return [{"vnName": "CTCP FPT (VND)", "floor": "HOSE", "foundDate": "2002-05-13", "vnSummary": "Giới thiệu"}]
        return [{"ratioCode": "PRICE_TO_EARNINGS", "value": 8.6, "reportDate": "2026-11-18"},
                {"ratioCode": "ROAE_TR_AVG5Q", "value": 0.24, "reportDate": "2026-09-30"}]
    monkeypatch.setattr(co_ban, "_goi", goi)
    co_ban._bo_nho.clear()
    import streamlit as st
    st.cache_data.clear()            # bỏ kết quả đã lưu tạm từ các test trước
    at = AppTest.from_file(str(ROOT / "web_app.py"), default_timeout=180).run()
    assert not at.exception, at.exception
    assert any("CTCP FPT (VND)" in m.value for m in at.markdown)
    assert any(m.label == "P/E" and m.value == "8.6" for m in at.metric)
    assert any("VNDirect" in c.value for c in at.caption)
