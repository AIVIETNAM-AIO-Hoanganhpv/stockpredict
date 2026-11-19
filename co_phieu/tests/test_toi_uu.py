"""Kiểm tra module tối ưu tham số (dữ liệu giả lập, không cần mạng)."""
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dudoan import toi_uu as T  # noqa: E402
from test_khuyen_nghi import gia_vn  # noqa: E402


@pytest.fixture(scope="module")
def du_lieu():
    df = gia_vn(1.0, n=520)
    f = T.trich_xuat_ma("AAA", df, buoc=10, so_diem=20)
    return f, {"AAA": df[["open", "high", "low", "close"]].to_numpy(float)}


def test_trich_xuat_du_cot(du_lieu):
    f, _ = du_lieu
    assert len(f) >= 10 and f["i"].is_monotonic_increasing
    assert {"diem_d", "diem_w", "vung_thap", "atr", "dinh_so", "dh_stoch", "v_MACD", "w_MACD"} <= set(f.columns)


def test_tinh_lai_diem_goc_khop(du_lieu):
    f, _ = du_lieu
    assert np.allclose(T.tinh_diem(f, "goc"), f["diem_d"])
    d = T.tinh_diem(f, "xu_huong")
    assert d.shape == (len(f),) and np.all(np.abs(d) <= 100)


def test_mo_phong_cac_bien_the(du_lieu):
    f, g = du_lieu
    for p in (T.ThamSo(), T.ThamSo(vao="ngay", sl="atr_3", tp="khong", trailing=3.0, giu=30),
              T.ThamSo(trong_so="smc", sl="day_0.5", tp="r_2", thoat_dinh=4, nguong=0)):
        l = T.mo_phong(f, g, p)
        t = T.tom_tat(l)
        if t["so_lenh"]:
            assert (l["ngay_giu"] <= p.giu + 1).all() and l["lai"].gt(-1).all()
            # không mở lệnh chồng lệnh trên cùng một mã
            assert l["ngay"].is_monotonic_increasing


def test_lenh_trailing_va_cat_lo():
    g = np.array([[100, 101, 99, 100], [100, 110, 99, 109], [109, 112, 104, 105], [105, 106, 90, 95.0]])
    lai, n, ly_do = T._lenh(g, 1, 100, 95, None, 2.0, 3.0, 3, None)
    assert ly_do == "cắt lỗ" and n == 2 and lai > 0          # trailing dời lên 112 − 6 = 106 → chốt ở 106
    lai, n, ly_do = T._lenh(g, 1, 100, 95, 111, 0.0, 3.0, 3, None)
    assert ly_do == "chốt lời"


def test_moc_mua_giu(du_lieu):
    f, g = du_lieu
    m = T.moc_mua_giu(f, g, 20)
    assert m["so"] > 0 and m["lai_tb"] > 0                   # giá giả lập đi lên
