"""Kế hoạch rõ ràng (điểm mua / cắt lỗ / chốt lời / vì sao) và điểm mô hình thử nghiệm – không gọi mạng."""
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dudoan import khuyen_nghi as K, mo_hinh as M  # noqa: E402
from dudoan.quet import phan_tich_df  # noqa: E402
from test_du_doan import gia_gia_lap  # noqa: E402


@pytest.mark.parametrize("chieu", [1.0, -1.0])
def test_giai_thich_day_du(chieu):
    df = gia_gia_lap(chieu, n=300, seed=4, freq="B") * [300, 300, 300, 300, 1]   # giá luôn dương
    kq, kn = phan_tich_df("ABC", df)
    gt = K.giai_thich(kq, kn["D"], von=100e6)
    for k in ("trang_thai", "dieu_kien", "gia_mua", "cat_lo", "chot_loi", "vi_sao_mua", "vi_sao_cat_lo",
              "vi_sao_chot_loi", "vi_sao", "ky_vong", "tom_tat"):
        assert gt.get(k) not in (None, "", []), k
    assert gt["cat_lo"] < gt["gia_mua"] < gt["chot_loi"]
    assert gt["tien_lai"] > 0 > gt["tien_lo"]
    assert gt["vi_sao"][0].startswith("Xu hướng")
    assert gt["vao_lenh"] == (kn["D"].muc == "Mua")
    if not gt["vao_lenh"]:
        assert gt["trang_thai"] == "THAM KHẢO – CHƯA VÀO" and gt["dieu_kien"].startswith("Chỉ vào khi")
    assert "e+0" not in " ".join(gt["vi_sao"])          # không còn số dạng 1.38e+05


def test_vi_the_co_ly_do():
    df = gia_gia_lap(1.0, n=400, seed=2) * [300, 300, 300, 300, 1]
    kq, kn = phan_tich_df("ABC", df)
    v = K.danh_gia_vi_the(float(df.close.iloc[-50]), 1000, kq, kn["D"])
    assert v["goi_y"] and v["vi_sao"]


def test_diem_mo_hinh():
    df = gia_gia_lap(1.0, n=400, seed=3, freq="B") * [300, 300, 300, 300, 100]
    m = M.diem_mo_hinh(df)
    assert 0 <= m["diem"] <= 100 and 1 <= m["nhom"] <= 10
    assert -0.2 < m["vuot_tb_20"] < 0.2 and 0 <= m["ti_le_thang_20"] <= 1
    with pytest.raises(ValueError):
        M.diem_mo_hinh(df.iloc[:100])


def test_fibo_theo_song():
    """Hồi ít thì lên nhiều: sóng A→B, hồi về C; mục tiêu > giá vào; phá đáy A → đo sóng mới."""
    from dudoan import fibo as F
    assert F.ti_le_theo_hoi(0.3) == 1.618 and F.ti_le_theo_hoi(0.6) == 1.272 and F.ti_le_theo_hoi(0.8) == 1.0
    df = gia_gia_lap(1.0, n=400, seed=7, freq="B") * [300, 300, 300, 300, 1]
    for khung in ("W", "M"):
        x = F.muc_tieu_song(df, khung, float(df.close.iloc[-1]))
        if x:
            assert x["B"] > x["A"] and x["C"] >= x["A"] and x["chot_loi"] > df.close.iloc[-1] * 1.01
            assert x["ti_le"] in F.BAC_TL


def test_fibo_dai_han_chi_muc_1():
    """Cổ phiếu dài hạn: chỉ mức 1,0 (không nâng lên 1,618); lãi dự kiến dưới 10% → không vào."""
    from dudoan import fibo as F, khuyen_nghi as K
    df = gia_gia_lap(1.0, n=600, seed=7, freq="B") * [300, 300, 300, 300, 1]
    for khung in ("W", "M"):
        x = F.muc_tieu_song(df, khung, float(df.close.iloc[-1]), ti_le_co_dinh=1.0)
        if x:
            assert x["ti_le"] == 1.0 and abs(x["chot_loi"] - (x["C"] + x["B"] - x["A"])) < 1e-6
    assert K.LAI_FIBO_TL == 1.0 and K.LAI_TOI_THIEU == 0.10


def test_adx_tuan_tren_the_ke_hoach():
    from dudoan import khuyen_nghi as K
    from dudoan.quet import phan_tich_df
    df = gia_gia_lap(1.0, n=600, seed=4, freq="B") * [300, 300, 300, 300, 1]
    kq, kn = phan_tich_df("ABC", df)
    gt = K.giai_thich(kq, kn["W"], 1e8)
    assert gt["tam"] == "W" and gt["adx_tuan"] and gt["adx_tuan"]["dat"] == (
        gt["adx_tuan"]["adx"] >= 25 and gt["adx_tuan"]["pdi"] > gt["adx_tuan"]["mdi"])


def test_song_chat_khong_lay_dinh_dang_chay():
    """Sóng 'chặt': đỉnh B phải đã xác nhận, hồi ≥ 23,6% – giá đang lập đỉnh mới thì không có sóng (không mua đuổi)."""
    from dudoan import fibo as F
    idx = pd.bdate_range("2022-01-03", periods=900)
    c = np.r_[np.linspace(100, 50, 300), np.linspace(50, 150, 600)]     # giảm rồi tăng thẳng tới hôm nay
    df = pd.DataFrame({"open": c, "high": c * 1.005, "low": c * 0.995, "close": c, "volume": 1e6}, index=idx)
    assert F.muc_tieu_song(df, "M", float(c[-1]), ti_le_co_dinh=1.0, chat=True) is None
    assert F.muc_tieu_song(df, "W", float(c[-1]), ti_le_co_dinh=1.0, chat=True) is None
