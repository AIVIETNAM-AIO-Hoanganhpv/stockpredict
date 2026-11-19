"""GreenView ↔ StockPredict: gói dữ liệu, HTML nhúng, máy chủ trên máy, nguồn dự phòng VNDirect (không gọi mạng)."""
import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dudoan import du_lieu, greenview as G  # noqa: E402
from test_du_doan import gia_gia_lap  # noqa: E402


@pytest.fixture
def gia_tang():
    return gia_gia_lap(1.0, n=700, seed=3, freq="B") * 100


def test_goi_du_lieu(gia_tang):
    g = G.goi_du_lieu("ABC", gia_tang)
    assert g["ma"] == "ABC" and len(g["bars"]) == 700
    b = g["bars"][-1]
    assert set(b) == {"time", "open", "high", "low", "close", "volume"}
    assert b["time"] == int(gia_tang.index[-1].timestamp())
    kh = g["ke_hoach"]
    assert kh["muc"] in ("Không mua", "Theo dõi", "Gần đủ điều kiện", "Mua")
    for s in g["tin_hieu"]:
        assert s["t_bao"] < s["t_mua"] <= s["t_ra"]
        assert s["cat_lo"] < s["gia_mua"] < s["chot_loi"]
        assert s["ket_qua"] in ("Chốt lời", "Cắt lỗ", "Hết 60 phiên", "Đang giữ")
    json.dumps(g)          # phải chuyển được sang JSON


def test_tin_hieu_khong_chong_lenh(gia_tang):
    ds = G.tin_hieu_qua_khu("ABC", gia_tang, so_phien=400, buoc=5)
    for a, b in zip(ds, ds[1:]):
        assert b["t_mua"] > a["t_ra"]


def test_html_nhung():
    html = G.html_nhung({"ma": "X", "bars": [], "ghi_chu": "</script>"}, api="")
    dau = html[:html.index("</head>")]
    assert "window.GV_DATA=" in dau and 'window.GV_API="";' in dau
    assert "<\\/script>" in dau          # không làm vỡ thẻ script
    assert "stockpredict.js" in html     # bản dist đã gộp file kết nối


def test_may_chu(monkeypatch, gia_tang):
    import chay_greenview as C
    monkeypatch.setattr(du_lieu, "tai", lambda ma, khung: gia_tang)
    C._KN.clear()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), C.XuLy)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    goc = f"http://127.0.0.1:{srv.server_address[1]}"
    lay = lambda p: urllib.request.urlopen(goc + p, timeout=60).read().decode("utf-8")  # noqa: E731
    try:
        assert 'window.GV_API=""' in lay("/")
        g = json.loads(lay("/api/gia?ma=abc&n=3"))
        assert g["ma"] == "ABC" and len(g["bars"]) == 3
        k = json.loads(lay("/api/khuyen_nghi?ma=ABC"))
        assert "muc" in k["ke_hoach"] and isinstance(k["tin_hieu"], list)
        monkeypatch.setattr(du_lieu, "tai", lambda ma, khung: (_ for _ in ()).throw(RuntimeError("hết mạng")))
        assert "hết mạng" in json.loads(lay("/api/gia?ma=XYZ"))["loi"]
    finally:
        srv.shutdown()


class _Tra:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self.data


def test_vndirect_du_phong(monkeypatch):
    x = {"s": "ok", "t": [1794960000, 1795046400], "o": [19.3, 18.8], "h": [19.3, 19.0], "l": [18.8, 18.5],
         "c": [18.8, 18.7], "v": [158000, 117000]}
    url = []

    def mo(req, timeout=0):
        url.append(req.full_url)
        if "vietcap" in req.full_url:
            raise OSError("HTTP Error 403: Forbidden")
        return _Tra(json.dumps(x).encode())
    monkeypatch.setattr(du_lieu.urllib.request, "urlopen", mo)
    du_lieu._CACHE.clear()
    df = du_lieu.tai("PLC", "D")
    assert list(df.close) == [18800, 18700]          # nghìn đồng → đồng
    assert any("vndirect" in u for u in url)
    du_lieu._CACHE.clear()
    assert du_lieu._vnd("HNXINDEX").close.iloc[-1] == 18.7    # chỉ số giữ nguyên
    assert "symbol=HNX&" in url[-1]
    du_lieu._CACHE.clear()


def test_khoa_twelvedata(monkeypatch, tmp_path):
    monkeypatch.delenv("TWELVEDATA_API_KEY", raising=False)
    monkeypatch.setattr(G, "FILE_KHOA_TD", tmp_path / "khoa.txt")
    assert G.khoa_twelvedata() == ""
    (tmp_path / "khoa.txt").write_text("abc123DEF\n", encoding="utf-8")
    assert G.khoa_twelvedata() == "abc123DEF"
    assert 'window.GV_TD_KEY="abc123DEF"' in G.html_nhung(api="")
    (tmp_path / "khoa.txt").write_text("<script>", encoding="utf-8")
    assert G.khoa_twelvedata() == ""            # chỉ nhận chữ/số
