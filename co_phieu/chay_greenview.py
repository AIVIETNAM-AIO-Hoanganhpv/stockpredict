"""Mở GreenView với giá cổ phiếu Việt Nam thật (chạy trên máy, không cần mạng nội bộ hay proxy).

Trình duyệt bị chặn khi gọi thẳng API giá Vietcap → chương trình này chạy một máy chủ nhỏ trên máy
(chỉ máy này truy cập được, địa chỉ http://127.0.0.1:<cổng>), lấy giá hộ trình duyệt và mở GreenView.

Cách chạy:  bấm đúp chay_greenview.bat   (hoặc:  py chay_greenview.py)
Đường dẫn máy chủ:
  /                         GreenView (nguồn "StockPredict (giá VN)" + chỉ báo khuyến nghị)
  /api/gia?ma=FPT[&n=3]     giá ngày {ma, bars}
  /api/khuyen_nghi?ma=FPT   kế hoạch hiện tại + các lần báo Mua trong quá khứ
"""
import json
import socket
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dudoan import du_lieu, greenview as G  # noqa: E402

_KN: dict = {}          # mã -> (thời điểm, kế hoạch + tín hiệu)
HAN_KN = 1800           # giây
_KHOA = threading.Lock()


def gia(ma: str, n: int | None = None) -> dict:
    df = du_lieu.tai(ma, "D").iloc[-(n or 1500):]     # du_lieu tự lưu tạm 5 phút
    return {"ma": ma, "bars": G.nen(df), "luc": time.strftime("%d/%m/%Y %H:%M")}


def khuyen_nghi(ma: str) -> dict:
    with _KHOA:
        c = _KN.get(ma)
        if c and time.time() - c[0] < HAN_KN:
            return c[1]
    df = du_lieu.tai(ma, "D").dropna(subset=["open", "high", "low", "close"]).iloc[-1500:]
    kq = {"ma": ma, "ke_hoach": G.ke_hoach(ma, df), "tin_hieu": G.tin_hieu_qua_khu(ma, df)}
    with _KHOA:
        _KN[ma] = (time.time(), kq)
    return kq


class XuLy(BaseHTTPRequestHandler):
    def _gui(self, ma_http: int, noi_dung: bytes, kieu: str):
        self.send_response(ma_http)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(noi_dung)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(noi_dung)

    def _json(self, obj, ma_http=200):
        self._gui(ma_http, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):  # noqa: N802 (tên do thư viện quy định)
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        ma = "".join(ch for ch in q.get("ma", "").upper() if ch.isalnum())[:20]
        try:
            if u.path in ("/", "/index.html"):
                self._gui(200, G.html_nhung(api="").encode("utf-8"), "text/html; charset=utf-8")
            elif u.path == "/api/gia":
                if not ma:
                    return self._json({"loi": "Thiếu mã"}, 400)
                n = int(q["n"]) if q.get("n", "").isdigit() else None
                self._json(gia(ma, n))
            elif u.path == "/api/khuyen_nghi":
                if not ma:
                    return self._json({"loi": "Thiếu mã"}, 400)
                self._json(khuyen_nghi(ma))
            else:
                self._gui(404, b"Khong co trang nay", "text/plain; charset=utf-8")
        except Exception as e:
            self._json({"loi": f"Không lấy được {ma}: {str(e)[:200]}"})

    def log_message(self, fmt, *args):   # in gọn: chỉ đường dẫn
        print(time.strftime("%H:%M:%S"), self.path[:80])


def cong_trong(bat_dau: int = 8765) -> int:
    for p in range(bat_dau, bat_dau + 50):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError("Không tìm được cổng trống")


def main(mo_trinh_duyet: bool = True):
    if not G.FILE_GV.exists():
        print("Không thấy file", G.FILE_GV, "- hãy tải đủ thư mục greenview/ của repo.")
        return 1
    cong = cong_trong()
    may_chu = ThreadingHTTPServer(("127.0.0.1", cong), XuLy)
    dia_chi = f"http://127.0.0.1:{cong}/"
    print("GreenView đang chạy tại", dia_chi)
    print("Đóng cửa sổ này để tắt.")
    if mo_trinh_duyet:
        threading.Timer(1.0, lambda: webbrowser.open(dia_chi)).start()
    try:
        may_chu.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
