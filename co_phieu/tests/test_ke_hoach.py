"""Kế hoạch rõ ràng (điểm mua / cắt lỗ / chốt lời / vì sao) và điểm mô hình thử nghiệm – không gọi mạng."""
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
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
