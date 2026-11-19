# CLAUDE.md – StockPredict

Công cụ dự đoán xu hướng & khuyến nghị cổ phiếu Việt Nam (`co_phieu/`) và biểu đồ GreenView (`greenview/`).
Tách từ repo `draft` (app luyện thi MOS) ngày 19/11/2026, giữ lịch sử commit.

## Cách làm việc với người dùng
- Người dùng không phải lập trình viên: trả lời **bằng tiếng Việt, ngắn gọn, dễ hiểu**; hỏi kỹ trước khi làm.
- Máy người dùng: **Windows + Python (lệnh `py`)**. Môi trường cloud là Linux: không thử được `.bat`, TradingView,
  Streamlit Cloud → nói rõ khi báo kết quả.
- Làm xong: chạy test, commit, push lên `main`. Người dùng tải bằng **Code → Download ZIP**.
- Luôn nói thẳng kết quả kiểm định (backtest): tín hiệu hiện chưa vượt mua/bán ngẫu nhiên.

## Lệnh
```bash
pip install -r co_phieu/requirements.txt pytest pyflakes
python -m pytest -q co_phieu/tests        # phải pass hết, KHÔNG gọi mạng (conftest thay nguồn bằng dữ liệu mẫu)
python -m pyflakes co_phieu
python greenview/build.py                  # gộp greenview/src → greenview/dist/GreenView.html
```

## co_phieu/
- Có `co_phieu/README.md`, `requirements.txt`, `run.bat`, test trong `co_phieu/tests/`.
- Cài: `pip install -r co_phieu/requirements.txt` (vnstock tuỳ chọn). Test dùng dữ liệu giả lập, không cần mạng.
- GitHub Actions `.github/workflows/du_doan_co_phieu.yml`: mỗi giờ phân tích ma.txt, 16h17 (giờ VN) quét toàn thị trường; chạy trên `main`.
- Web app: `co_phieu/web_app.py` (Streamlit, test bằng `streamlit.testing` + dữ liệu giả trong `tests/test_web_app.py`).
- TradingView: `co_phieu/tradingview/du_doan_xu_huong.pine` (Pine v6). Kiểm cú pháp: `pip install pynescript`,
  `pynescript.ast.parse(src)`; không chạy được trên TradingView thật từ cloud → nói rõ với người dùng.
- Dữ liệu VN: Vietcap `trading.vietcap.com.vn/api` (getAll = danh sách mã; gap-chart = giá, CHỈ 1 mã/lần gọi,
  cần header Accept + User-Agent). Quét toàn thị trường: `dudoan/quet.py`, khuyến nghị: `dudoan/khuyen_nghi.py`.
- Backtest: `dudoan/kiem_dinh.py` (`du_doan.py --kiem-dinh`, ~10–20 phút, 4 tiến trình). Kết quả 19/11/2026: tín hiệu
  Mua/Bán ở đỉnh CHƯA tốt hơn ngẫu nhiên (xem README) → luôn nói rõ điều này khi báo kết quả.
- Doanh nghiệp/BCTC: `dudoan/co_ban.py` (Vietcap `api/iq-insight-service/v1/company/<MÃ>[/financial-statement?section=…,
  /financial-statement/metrics, /statistics-financial, /shareholder]`), cache 12 giờ trong `du_lieu_ma/cache/` (gitignore).
  Test KHÔNG gọi mạng: `tests/conftest.py` thay `_goi` bằng dữ liệu mẫu `tests/du_lieu/co_ban_mau.json.gz` (FPT, VCB).
- Sự kiện/cổ tức/tin DN: Vietcap `events|news?ticker=&fromDate=YYYYMMDD&toDate=YYYYMMDD`, `company/<MÃ>/insider-transaction`;
  công ty con: CafeF `du-lieu/Ajax/PageNew/GetDataSubsidiaries.ashx`. TCBS (apipubaws) bị Cloudflare chặn – KHÔNG vượt.
- Tin tức: `dudoan/tin_tuc.py` (Google News RSS + RSS CafeF/Vietstock/VnExpress); test dùng RSS mẫu trong `tests/du_lieu/`.
- Bước giá: HOSE 10/50/100 đ, HNX/UPCoM 100 đ, chỉ số & ngoại tệ không làm tròn (`khuyen_nghi.loai_gia`).
- Môi trường cloud `draft` cho phép Yahoo Finance và trading.vietcap.com.vn.

## greenview/
- Mã nguồn trong `greenview/src` (JS thuần, Lightweight Charts). `build.py` gộp thành 1 file `dist/GreenView.html`.
- Nguồn giá: Binance, VNDirect/TCBS (trình duyệt có thể chặn → proxy), Twelve Data (cần key), giả lập, CSV; khi mở
  trong Claude dùng connector TCBS (`window.claude.use('mcp')`, tool `tcinvest-*`).
- Kiểm tra nhanh: mở dist bằng Playwright, nạp nguồn `DEMO`, chạy `calc` của mọi chỉ báo với `App.ta.prep(bars)`.
