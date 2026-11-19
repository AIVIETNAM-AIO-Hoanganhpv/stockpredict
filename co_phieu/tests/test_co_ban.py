"""Kiểm tra thông tin doanh nghiệp, BCTC, chỉ số, sức khỏe tài chính (dữ liệu mẫu, không cần mạng)."""
import pytest

pd = pytest.importorskip("pandas")

from dudoan import co_ban as C  # noqa: E402


def test_ho_so_va_ctck():
    hs = C.ho_so("FPT")
    assert hs["ten_ngan"] == "FPT Corp" and hs["von_hoa"] > 1e13 and hs["so_cp"] > 1e9
    assert "&" not in hs["gioi_thieu"][:200] and "<" not in hs["gioi_thieu"]     # đã bỏ thẻ HTML
    assert hs["ctck"]["xep_hang"] == "MUA" and hs["ctck"]["gia_muc_tieu"] > 0
    assert C.ho_so("VCB")["la_ngan_hang"] is True


def test_bang_bctc_nam_quy():
    nam = C.bang_bctc("FPT", "kqkd")
    assert list(nam.columns[2:]) == ["2021", "2022", "2023", "2024", "2025"]
    dt = nam[nam["_ma"] == "isa3"].iloc[0]
    assert 60_000 < dt["2025"] < 80_000                        # tỷ đồng
    quy = C.bang_bctc("FPT", "cdkt", quy=True)
    assert len(quy.columns) == 2 + 8 and quy.columns[-1].startswith("Q")
    eps = nam[nam["_ma"] == "isa23"].iloc[0]["2025"]
    assert eps > 1000                                           # EPS giữ nguyên đơn vị đồng
    assert not C.bang_bctc("VCB", "kqkd").empty
    assert not C.bang_bctc("FPT", "lctt", quy=True).empty


def test_chi_so_va_co_dong():
    cs = C.bang_chi_so("FPT")
    assert "P/E" in set(cs["Chỉ số"]) and "ROE" in set(cs["Chỉ số"])
    assert C.chi_so_moi_nhat("FPT")["pe"] > 0
    cd = C.co_dong("FPT", 5)
    assert len(cd) == 5 and cd["Tỷ lệ %"].is_monotonic_decreasing


def test_suc_khoe_ngan_hang_va_doanh_nghiep():
    for ma in ("FPT", "VCB"):
        sk = C.suc_khoe(ma, gia=50_000)
        assert sk.du_lieu and 1 <= sk.tong <= 5
        assert all(1 <= x <= 5 for x in (sk.tang_truong, sk.sinh_loi, sk.an_toan, sk.dinh_gia))
        assert sk.chi_tiet["dt_ttm"] > 0                         # ngân hàng: không lấy ô doanh thu = 0


def test_suc_khoe_khong_nhin_truoc_tuong_lai():
    sk_2024 = C.suc_khoe("FPT", ngay="2024-06-01", gia=100_000)
    assert sk_2024.du_lieu
    ky = sk_2024.chi_tiet["ky_moi_nhat"]
    assert ky in ("Q1/2024", "Q4/2023")                         # chỉ báo cáo đã công bố trước 01/06/2024
    assert not C.suc_khoe("FPT", ngay="2019-01-01").du_lieu    # chưa đủ 8 quý


def test_tom_tat_va_dieu_chinh_khuyen_nghi():
    from dudoan.khuyen_nghi import KhuyenNghi
    t = C.tom_tat_co_ban("FPT", pd.DataFrame({"close": [50_000.0]}, index=[pd.Timestamp("2026-11-18")]))
    assert t["Sức khỏe"] is not None and t["CTCK"] == "MUA" and t["Đang lỗ"] is False
    kn = KhuyenNghi("FPT", "D", "Mua mạnh", 50_000, 50)
    C.dieu_chinh_khuyen_nghi(kn, {"Đang lỗ": True})
    assert kn.muc == "Mua" and kn.diem == 35
    kn2 = KhuyenNghi("FPT", "D", "Mua", 50_000, 50)
    C.dieu_chinh_khuyen_nghi(kn2, {"Sức khỏe": 4.5, "Đang lỗ": False})
    assert kn2.diem == 60
    assert C.tom_tat_co_ban("ZZZ")["Sức khỏe"] is None          # không có dữ liệu → không lỗi


def test_xuat_excel(tmp_path):
    p = C.xuat_excel("FPT", tmp_path / "FPT.xlsx")
    sheets = pd.read_excel(p, sheet_name=None)
    assert "Hồ sơ" in sheets and "Cổ đông lớn" in sheets
    assert any(s.startswith("Kết quả kinh doanh") for s in sheets)


def test_cli_doanh_nghiep(tmp_path, capsys):
    import du_doan
    rc = du_doan.main(["--doanh-nghiep", "FPT", "ZZZ", "--thu-muc", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0 and "Sức khỏe tài chính" in out and "ZZZ" in out
    assert (tmp_path / "FPT_tai_chinh.xlsx").exists()
