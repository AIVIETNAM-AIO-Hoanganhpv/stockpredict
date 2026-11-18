"""Kiểm tra điểm mua, khuyến nghị, tính lãi, danh mục và quét thị trường (dữ liệu giả lập)."""
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dudoan import du_lieu, khuyen_nghi as K, quet  # noqa: E402
from test_du_doan import gia_gia_lap  # noqa: E402


def gia_vn(chieu=1.0, n=900, seed=1):
    df = gia_gia_lap(chieu, n=n, seed=seed)
    return df * [250, 250, 250, 250, 1]          # giá kiểu VN (hàng chục nghìn đồng)


def test_tinh_lai_co_phi_va_thue():
    r = K.tinh_lai(100_000_000, 20_000, 22_000)
    assert r["so_cp"] == 4900                       # lô 100, đã tính phí mua
    assert r["tien_mua"] == pytest.approx(4900 * 20_000 * 1.0015)
    assert r["tien_ban"] == pytest.approx(4900 * 22_000 * (1 - 0.0015 - 0.001))
    assert 0.09 < r["pct"] < 0.1
    assert K.tinh_lai(1_000_000, 20_000, 22_000)["so_cp"] == 0      # không đủ 1 lô


def test_lam_tron_buoc_gia():
    assert K.lam_tron(9_987, "vn") == 9_980
    assert K.lam_tron(23_480, "vn") == 23_450
    assert K.lam_tron(65_430, "vn") == 65_400
    assert K.lam_tron(1.23456, "fx") == 1.23456


def test_khuyen_nghi_xu_huong_tang_va_giam():
    up, _ = quet.phan_tich_df("AAA", gia_vn(1.0))[1], None
    down = quet.phan_tich_df("BBB", gia_vn(-0.3, seed=2))[1]
    for tam in ("D", "W"):
        kn = up[tam]
        assert kn.muc in ("Mua mạnh", "Mua", "Chờ về vùng mua", "Theo dõi"), kn.ly_do
        if kn.gia_mua:
            assert kn.cat_lo < kn.gia_mua < kn.chot_loi1
            assert kn.gia_mua <= kn.gia + 1e-6
            assert kn.gia_mua % 10 == 0                 # làm tròn bước giá
        assert down[tam].muc == "Không mua"


def test_vung_mua_hop_luu():
    kq, kn = quet.phan_tich_df("AAA", gia_vn(1.0))
    v = kn["D"].vung
    assert v is not None and v.thap < v.cao and len(v.ly_do) >= 2
    assert v.thap <= kn["D"].gia


def test_danh_gia_vi_the():
    kq, kn = quet.phan_tich_df("AAA", gia_vn(1.0))
    gia = kq.khung[-1].gia
    lai = K.danh_gia_vi_the(gia * 0.8, 1000, kq, kn["D"])
    assert lai["lai"] > 0 and lai["goi_y"] in ("Giữ", "Chốt lời một phần", "Theo dõi")
    kq2, kn2 = quet.phan_tich_df("BBB", gia_vn(-0.3, seed=2))
    lo = K.danh_gia_vi_the(kq2.khung[-1].gia * 1.3, 1000, kq2, kn2["D"])
    assert lo["lai"] < 0 and lo["goi_y"] in ("Cắt lỗ", "Bán – thủng hỗ trợ", "Cân nhắc bán")


@pytest.fixture
def thi_truong_gia(monkeypatch, tmp_path):
    ds = pd.DataFrame({"ma": ["AAA", "BBB", "CCC", "DDD"], "san": ["HSX", "HNX", "UPCOM", "HSX"],
                       "ten": ["A", "B", "C", "D"]})
    monkeypatch.setattr(du_lieu, "danh_sach_ma_vn", lambda san=None, lam_moi=False: ds[ds.san.isin(san)])

    def fake(ma, khung="D", so_nen=1300):
        if ma == "DDD":
            raise RuntimeError("lỗi mạng")
        df = gia_vn(1.0 if ma != "BBB" else -0.3, seed=ord(ma[0]))
        df.index = pd.date_range(end=pd.Timestamp.now().normalize(), periods=len(df))
        if ma == "CCC":
            df["volume"] = 10.0                         # thanh khoản thấp
        return df
    monkeypatch.setattr(du_lieu, "_vci", fake)
    return tmp_path


def test_quet_va_ghi(thi_truong_gia):
    kq = quet.quet(gtgd_min=1e6, so_luong=2)
    tk = quet.thong_ke(kq)
    assert tk == {"tong": 4, "phan_tich": 2, "thanh_khoan_thap": 1, "loi": 1, "tang": tk["tang"], "giam": tk["giam"]}
    b = quet.bang(kq, "D", von=50e6)
    assert list(b["Mã"])[-1] == "BBB"                 # "Không mua" xếp cuối
    assert b["Hạng"].is_monotonic_decreasing
    data = quet.ghi(thi_truong_gia, kq)
    assert (thi_truong_gia / "khuyen_nghi.xlsx").exists()
    assert (thi_truong_gia / "thi_truong.json").exists() and len(data["D"]) == 2


def test_cli_quet(thi_truong_gia, capsys):
    import du_doan
    rc = du_doan.main(["--quet-thi-truong", "--gtgd", "0.001", "--thu-muc", str(thi_truong_gia / "bc")])
    out = capsys.readouterr().out
    assert rc == 0 and "NGẮN HẠN" in out and (thi_truong_gia / "bc" / "khuyen_nghi.md").exists()
