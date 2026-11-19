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
        assert kn.muc in K.MUC and kn.muc != "Không mua", kn.ly_do
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
                       "ten": ["A", "B", "C", "D"], "nganh": ["Ngân hàng", "Bất động sản", "Y tế", "Y tế"]})
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
    assert {k: tk[k] for k in ("tong", "phan_tich", "thanh_khoan_thap", "loi")} == \
        {"tong": 4, "phan_tich": 2, "thanh_khoan_thap": 1, "loi": 1}
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


def gia_dinh(seed=5):
    """Tăng mạnh nhiều nhịp rồi tạo đỉnh: cây nến râu trên dài, Stoch quá mua."""
    df = gia_vn(1.0, n=400, seed=seed)
    o, h, c = df["open"].iloc[-2], df["high"].iloc[-1], df["close"].iloc[-2]
    top = df["high"].iloc[-30:].max()
    df.iloc[-1, df.columns.get_loc("open")] = c
    df.iloc[-1, df.columns.get_loc("high")] = top * 1.06            # vượt đỉnh cũ (quét thanh khoản)
    df.iloc[-1, df.columns.get_loc("close")] = c * 0.995             # đóng cửa quay xuống → râu trên dài
    df.iloc[-1, df.columns.get_loc("low")] = c * 0.99
    del o, h
    return df


def test_tin_hieu_dinh():
    kq, _ = quet.phan_tich_df("TOP", gia_dinh())
    t = K.tin_hieu_dinh(kq, "D")
    assert t.so_dau_hieu >= 2, t.dau_hieu
    assert any("râu trên" in d or "Quét thanh khoản" in d for d in t.dau_hieu)
    assert t.muc in K.MUC_BAN and t.hang >= 1
    if t.vung_ban:
        assert t.vung_ban[0] <= t.vung_ban[1] and t.gia_ban >= t.vung_ban[0]
    # cổ phiếu đã giảm sâu thì không còn ở đỉnh
    kq2, _ = quet.phan_tich_df("BBB", gia_vn(-0.3, seed=2))
    assert K.tin_hieu_dinh(kq2, "D").muc in ("Chưa có đỉnh", "Theo dõi đỉnh")


def test_nguong_dinh_nhay_hon():
    kq, _ = quet.phan_tich_df("TOP", gia_dinh())
    assert K.tin_hieu_dinh(kq, "D", nguong=2).hang >= K.tin_hieu_dinh(kq, "D", nguong=4).hang


def test_danh_muc_ban_o_dinh():
    kq, kn = quet.phan_tich_df("TOP", gia_dinh())
    t = K.tin_hieu_dinh(kq, "D")
    t.muc = "Bán mạnh"
    t.gia_ban = kq.khung[-1].gia * 1.02
    v = K.danh_gia_vi_the(kq.khung[-1].gia * 0.7, 1000, kq, kn["D"], dinh=t)
    assert v["goi_y"] == "Bán ở đỉnh" and v["lai_neu_ban"] > v["lai"] > 0


def test_nganh_va_bang_ban(thi_truong_gia):
    kq = quet.quet(gtgd_min=1e6, so_luong=2)
    ng = quet.suc_manh_nganh(kq)
    assert set(ng["Ngành"]) == {"Ngân hàng", "Bất động sản"}
    assert ng["Sức mạnh"].is_monotonic_decreasing and list(ng["Hạng"]) == [1, 2]
    assert ng.iloc[0]["Ngành"] == "Ngân hàng"            # AAA tăng, BBB giảm
    b = quet.bang(kq, "D")
    assert "Ngành" in b and "Tín hiệu đỉnh" in b
    assert any("Ngành" in x for x in b["Lý do"])
    bb = quet.bang_ban(kq, "D")
    assert bb.empty or bb["Hạng"].is_monotonic_decreasing
    data = quet.ghi(thi_truong_gia, kq)
    assert {"ban_D", "ban_W", "nganh_D", "nganh_W"} <= set(data)


# ---------------------------------------------------------------- lỗi đã sửa (chống tái phát)
def test_buoc_gia_theo_san_va_chi_so():
    assert K.loai_gia("ABC", "vn", "HNX") == "vn_100"
    assert K.loai_gia("ABC", "vn", "UPCOM") == "vn_100"
    assert K.loai_gia("ABC", "vn", "HSX") == "vn"
    assert K.loai_gia("VNINDEX", "vn") == "chi_so"
    assert K.loai_gia("EURUSD", "fx") == "fx"
    assert K.lam_tron(23_480, "vn_100") == 23_400
    assert K.lam_tron(1703.01, "chi_so") == 1703.01


def test_khuyen_nghi_ngoai_te_khong_lam_tron():
    df = gia_vn(1.0) / [250, 250, 250, 250, 1] * [0.01, 0.01, 0.01, 0.01, 1]   # giá kiểu 1.0x
    kq, _ = quet.phan_tich_df("EURUSD", df, loai="fx")
    kn = K.khuyen_nghi(kq, "D")
    if kn.gia_mua:
        assert kn.gia_mua > 0.1 and kn.cat_lo > 0.1          # trước đây bị làm tròn về 0


def test_mua_luon_co_rr_toi_thieu_sau_lam_tron():
    for seed in range(1, 9):
        _, kn = quet.phan_tich_df("AAA", gia_vn(1.0, seed=seed), san="HNX")
        for tam in ("D", "W"):
            k = kn[tam]
            if k.muc == "Mua":
                assert 2.5 <= k.rr <= 3.5                       # chốt lời = 3 × rủi ro (sau làm tròn)
            for p in (k.gia_mua, k.cat_lo, k.chot_loi1):
                assert p is None or p % 100 == 0                # HNX: bước giá 100 đ


def test_danh_muc_thung_ho_tro():
    df = gia_vn(1.0)
    kq, _ = quet.phan_tich_df("AAA", df)
    ls = [s.price for s in kq.chinh.cau_truc.swings if s.kind == "L"]
    df2 = df.copy()
    gia_moi = ls[-1] * 0.93                                       # thủng đáy gần nhất
    df2.iloc[-1, :4] = [gia_moi * 1.01, gia_moi * 1.02, gia_moi * 0.99, gia_moi]
    kq2, kn2 = quet.phan_tich_df("AAA", df2)
    v = K.danh_gia_vi_the(gia_moi * 0.5, 100, kq2, kn2["D"])
    assert v["goi_y"] in ("Bán – thủng hỗ trợ", "Chốt lời / hạ tỷ trọng", "Bán ở đỉnh"), v


def test_ghi_khi_khong_co_ma_nao(tmp_path):
    quet.ghi(tmp_path, [])
    quet.ghi(tmp_path, [quet.KetQuaMa("AAA", "HSX", "A", loi="Thanh khoản thấp")])
    assert (tmp_path / "khuyen_nghi.md").exists()


def test_khong_dua_ke_hoach_ban_khong_cho_co_phieu_vn():
    from dudoan import bao_cao
    kq, _ = quet.phan_tich_df("BBB", gia_vn(-0.3, seed=2))
    assert kq.xu_huong == -1 and bao_cao.ke_hoach(kq) == {}


def test_kiem_dinh_khong_nhin_truoc_tuong_lai():
    from dudoan import kiem_dinh as KD
    df = gia_vn(1.0, n=520)
    r = KD.kiem_dinh_ma("AAA", df, buoc=20, so_diem=8)
    assert len(r["goc"]) >= 5
    # Đổi dữ liệu SAU điểm cuối được xét không được làm thay đổi tín hiệu tại các điểm trước đó
    df2 = df.copy()
    df2.iloc[-30:, :4] = df2.iloc[-30:, :4] * 0.5
    r2 = KD.kiem_dinh_ma("AAA", df2, buoc=20, so_diem=8)
    assert [x[0] for x in r["mua"]] == [x[0] for x in r2["mua"]]
    assert [x[0] for x in r["ban"]] == [x[0] for x in r2["ban"]]
    t = KD.tong_hop([r])
    assert "goc" in t and "ban" in t
    assert "Kiểm định" in KD.markdown(t, "thử")


def test_giao_dich_cat_lo_truoc_khi_cung_phien():
    from dudoan import kiem_dinh as KD
    o = np.array([100, 100, 100.0]); h = np.array([100, 120, 100.0]); l = np.array([100, 80, 100.0])
    c = np.array([100, 100, 100.0])
    lai, kq, _ = KD._giao_dich(o, h, l, c, 1, 100, 90, 110, 2)
    assert kq == "cắt lỗ" and lai < -0.09                 # cùng phiên chạm cả hai → tính cắt lỗ


def test_kiem_dinh_co_suc_khoe_tai_chinh():
    """Có BCTC (FPT mẫu) → mỗi điểm có sức khỏe tài chính; bước tổng hợp không lỗi."""
    from dudoan import co_ban, kiem_dinh as KD
    df = gia_vn(1.0, n=700)
    df.index = pd.date_range(end="2026-11-18", periods=len(df), freq="B")
    quy = co_ban.gan_gia_cong_bo(co_ban._chuoi_quy("FPT"), df)
    r = KD.kiem_dinh_ma("FPT", df, buoc=20, so_diem=10, quy=quy, ho_so=co_ban.ho_so_raw("FPT"))
    assert any(x[3] is not None for x in r["goc"])
    t = KD.tong_hop([r, r])
    assert len(t["theo_suc_khoe"]) == 4 and "Kết hợp sức khỏe" in KD.markdown(t, "thử")


def test_timing_ngay_chot_loi():
    kq, kn = quet.phan_tich_df("AAA", gia_vn(1.0))
    k = kn["D"]
    assert k.chot_loi1 and k.thoi_gian is not None
    tg = k.thoi_gian
    assert tg.som <= tg.thuong <= tg.muon                       # nhịp nhanh → sớm
    d_som, d_muon = tg.ngay(tg.som), tg.ngay(tg.muon)
    assert d_som <= d_muon and d_som.weekday() < 5 and d_som > kq.frames["D"].index[-1]
    assert len(tg.fibo) == 3 and tg.fibo[0] <= tg.fibo[1] <= tg.fibo[2] and tg.fibo[0] >= 1
    assert "phiên" in tg.mo_ta()
    # khung tuần: 1 nến = 5 phiên
    tw = kn["W"].thoi_gian
    if tw is not None and tw.thuong is not None:
        assert tw.phien(tw.thuong) == max(1, round(tw.thuong * 5))
    # chốt lời thấp hơn giá vào → không dự kiến
    assert K.du_kien_thoi_gian(kq.frames["D"], kq.khung[-1], 100, 90).thuong is None
    b = quet.bang([quet.KetQuaMa("AAA", "HSX", "A", kq=kq, kn=kn)], "D")
    assert "Dự kiến chốt lời" in b and "Số phiên dự kiến" in b
