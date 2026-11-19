"""Kiểm tra khuyến nghị theo ngày: lưu, đọc, hiệu quả, so sánh, lịch sắp tới (không cần mạng)."""
import pytest

pd = pytest.importorskip("pandas")

from dudoan import lich_su as LS  # noqa: E402


def du_lieu_quet(ds_mua, ds_ban):
    return {"luc": "19/11/2026 15:30", "thong_ke": {},
            "D": [{"Mã": m, "Hạng": h, "Khuyến nghị": "Mua" if h == 3 else "Chờ về vùng mua", "Giá": 100.0,
                   "Giá mua": 95.0, "Cắt lỗ": 90.0, "Chốt lời": 110.0, "Dự kiến chốt lời": "10/12/2099"}
                  for m, h in ds_mua] + [{"Mã": "ZZZ", "Hạng": 0}],
            "W": [], "ban_D": [{"Mã": m, "Hạng": 2, "Tín hiệu": "Chốt lời dần", "Giá": 100.0} for m in ds_ban],
            "ban_W": []}


def test_luu_doc_va_so_sanh(tmp_path):
    LS.luu_ngay(du_lieu_quet([("AAA", 3), ("BBB", 2)], ["CCC"]), "2026-11-18", tmp_path)
    LS.luu_ngay(du_lieu_quet([("AAA", 3), ("DDD", 3)], []), "2026-11-19", tmp_path)
    assert LS.ds_ngay(tmp_path) == ["2026-11-19", "2026-11-18"]
    moi, cu = LS.doc_ngay("2026-11-19", tmp_path), LS.doc_ngay("2026-11-18", tmp_path)
    assert [r["Mã"] for r in moi["mua_D"]] == ["AAA", "DDD"]          # bỏ mã hạng thấp (ZZZ)
    ss = LS.so_sanh(moi, cu)
    assert [r["Mã"] for r in ss["mua"]["moi_vao"]] == ["DDD"] and ss["mua"]["giu_nguyen"] == ["AAA"]
    assert [r["Mã"] for r in ss["cho"]["bi_loai"]] == ["BBB"]
    assert [r["Mã"] for r in ss["ban"]["bi_loai"]] == ["CCC"]


def test_hieu_qua_mua_va_ban():
    idx = pd.date_range("2026-11-19", periods=6, freq="B")
    gia = {
        "LAI": pd.DataFrame({"open": [100, 96, 97, 100, 105, 111], "high": [100, 97, 99, 104, 108, 112],
                             "low": [99, 94, 96, 99, 104, 109], "close": [100, 96, 98, 103, 107, 111]}, index=idx),
        "LO": pd.DataFrame({"open": [100, 96, 93, 91, 89, 88], "high": [100, 97, 94, 92, 90, 89],
                            "low": [99, 94, 92, 89, 88, 87], "close": [100, 95, 93, 90, 89, 88]}, index=idx),
        "CHUA": pd.DataFrame({"open": [100] * 6, "high": [101] * 6, "low": [99] * 6, "close": [100] * 6}, index=idx),
    }
    rows = [{"Mã": m, "Giá": 100.0, "Giá mua": 95.0, "Cắt lỗ": 90.0, "Chốt lời": 110.0} for m in gia]
    b = LS.hieu_qua_mua(rows, "2026-11-19", gia.get).set_index("Mã")
    assert b.loc["LAI", "Trạng thái"] == "Đã chạm chốt lời" and b.loc["LAI", "Lãi/lỗ %"] > 0
    assert b.loc["LO", "Trạng thái"] == "Đã cắt lỗ" and b.loc["LO", "Lãi/lỗ %"] < 0
    assert b.loc["CHUA", "Trạng thái"].startswith("Chưa khớp")
    s = LS.hieu_qua_ban([{"Mã": "LO", "Giá": 100.0}], "2026-11-19", gia.get)
    assert s.iloc[0]["Đánh giá"].startswith("Bán đúng")


def test_lich_sap_toi():
    hom_nay = pd.Timestamp.now().normalize()
    sk = pd.DataFrame({"Ngày": [(hom_nay + pd.Timedelta(days=d)).strftime("%Y-%m-%d") for d in (3, 200, -5)],
                       "Loại": ["Cổ tức tiền mặt", "Đại hội cổ đông thường niên", "Phát hành cổ phiếu"],
                       "Nội dung": ["Cổ tức 10%", "ĐHCĐ", "Phát hành"]})
    mua = [{"Mã": "BBB", "Khuyến nghị": "Mua", "Giá mua": 10000, "Chốt lời": 12000,
            "Dự kiến chốt lời": (hom_nay + pd.Timedelta(days=10)).strftime("%d/%m/%Y")}]
    lich = LS.lich_sap_toi(["AAA"], mua, 30, su_kien_ma=lambda m: sk)
    assert list(lich["Loại"]) == ["Cổ tức tiền mặt", "Dự kiến chốt lời"]    # bỏ sự kiện ngoài khoảng / đã qua
    assert lich["Thứ"].iloc[0].startswith(("Thứ", "CN"))


def test_quet_ghi_luu_ban_theo_ngay(tmp_path):
    from dudoan import quet
    quet.ghi(tmp_path, [])
    assert LS.ds_ngay(tmp_path / "lich_su")
