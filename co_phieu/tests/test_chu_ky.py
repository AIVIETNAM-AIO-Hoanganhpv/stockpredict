"""Pha thị trường (chu kỳ), dài hạn, LEVEL 1 và bộ lọc pha – dữ liệu giả lập, không gọi mạng."""
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dudoan import chu_ky as CK, khuyen_nghi as K, level1 as L1  # noqa: E402
from dudoan.quet import phan_tich_df  # noqa: E402
from test_du_doan import gia_gia_lap  # noqa: E402


def _thi_truong(chieu, n=400, so=40):
    """`so` mã cùng xu hướng đều `chieu` (%/phiên ×0,3), nhiễu nhỏ, GTGD đủ lớn."""
    ds = {}
    idx = pd.bdate_range(end="2026-11-18", periods=n)
    for k in range(so):
        rng = np.random.default_rng(k)
        c = 20000 * np.exp(np.cumsum(0.003 * chieu + rng.normal(0, 0.004, n)))
        ds[f"M{k:02d}"] = pd.DataFrame({"open": c * 0.998, "high": c * 1.01, "low": c * 0.99, "close": c,
                                        "volume": 1e6}, index=idx)
    return ds


def test_pha_tang_va_giam():
    nganh = {m: ("A" if i % 2 else "B") for i, m in enumerate(_thi_truong(1.0))}
    tang = CK.danh_gia(_thi_truong(1.0), nganh)
    giam = CK.danh_gia(_thi_truong(-0.6, n=300), nganh)
    assert tang["pha"] in CK.PHA_TOT and tang["nen_cam_co_phieu"]
    assert giam["pha"] in ("Giảm", "Phân phối") and not giam["nen_cam_co_phieu"]
    assert len(tang["lich_su"]) > 100 and {"t", "I", "pha"} <= set(tang["lich_su"][0])
    assert tang["nganh_top2"] and set(tang["nganh_top2"]) <= {"A", "B"}
    assert tang["dai_han"] and all("MA10 tháng" in x for x in tang["dai_han"])


def test_vi_mo_xau():
    ngay = pd.bdate_range("2024-01-01", "2024-12-31")
    tnx = pd.Series(np.r_[np.full(120, 4.0), np.linspace(4.0, 6.5, len(ngay) - 120)], index=ngay)
    x = CK.vi_mo_xau(tnx, ngay)
    assert not x.iloc[:60].any() and x.iloc[-5:].all()
    assert not CK.vi_mo_xau(None, ngay).any()


def test_dai_han_ma():
    tang = gia_gia_lap(1.0, n=400, seed=2, freq="B") * [300, 300, 300, 300, 1]
    x = CK.dai_han_ma(tang)
    assert x["du_lieu"] and x["tren_ma10"] and x["trang_thai"].startswith("Giữ")


def test_ap_pha_chuyen_mua_thanh_cho():
    df = gia_gia_lap(1.0, n=400, seed=3, freq="B") * [300, 300, 300, 300, 1]
    kq, kn = phan_tich_df("ABC", df)
    k = kn["D"]
    k.muc = "Mua"
    K.ap_pha(k, {"nen_cam_co_phieu": False, "pha": "Giảm"})
    assert k.muc == "Theo dõi" and k.muc_goc == "Mua" and "GIẢM" in k.ly_do[-1]
    gt = K.giai_thich(kq, k, 1e8)
    assert "thị trường chung" in gt["dieu_kien"]
    k2 = kn["W"]
    m0 = k2.muc
    K.ap_pha(k2, {"nen_cam_co_phieu": True, "pha": "Tăng"})
    assert k2.muc == m0


@pytest.mark.parametrize("khung", ["D", "W", "M"])
def test_level1_trang_thai(khung):
    df = gia_gia_lap(1.0, n=1300, seed=5, freq="B") * [300, 300, 300, 300, 1]
    t = L1.trang_thai(df, khung, 1e9)
    assert t["khung"] == khung and t["trang_thai"]
    if t["co_lenh"]:
        assert t["cat_lo"] < t["vao"] and t["cp_vi_the"] % 100 == 0 and t["nhip"] >= 1


def test_level1_nen_tuan_chi_lay_nen_da_xong():
    df = gia_gia_lap(1.0, n=300, seed=1, freq="B")
    df.index = pd.bdate_range(end="2026-11-18", periods=300)       # thứ Tư → tuần chưa xong
    w = L1.nen_khung(df, "W")
    assert w.index[-1] < pd.Timestamp("2026-11-18")


def test_level1_khoi_luong_dung_cong_thuc():
    # tài khoản 1 tỷ, khung D 5% chia 10 mã = 5 triệu; vị thế 30% = 1,5 triệu; vào 20.000, cắt lỗ 19.000 → 1.500 CP
    vung = 1e9 * 0.05 / 10 * L1.he_so_nhip(1, True)
    assert int(0.3 * vung / (20000 - 19000) // 100 * 100) == 1500
    assert L1.he_so_nhip(3, True) == 0.6 and L1.he_so_nhip(1, False) == 0.3
