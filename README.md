# StockPredict – dự đoán xu hướng & khuyến nghị cổ phiếu Việt Nam

| Thư mục | Nội dung |
|---|---|
| [`co_phieu/`](co_phieu/README.md) | Công cụ chính (Python). Dự đoán Tăng/Giảm theo Stoch, MACD, MFI, ADX, ICT, SMC, Fibonacci. Gồm: khuyến nghị mua toàn thị trường (HOSE/HNX/UPCoM) kèm vùng mua, cắt lỗ, chốt lời, ngày chốt lời dự kiến; tín hiệu bán ở đỉnh; phân ngành; thông tin doanh nghiệp, BCTC, tin tức; web app cho điện thoại; bản TradingView; backtest. |
| [`greenview/`](greenview/README.md) | GreenView – biểu đồ giá chạy trong trình duyệt, có 112 chỉ báo, 23 chiến lược và 85 công cụ vẽ. |
| `.github/workflows/` | Lịch chạy tự động trên GitHub: phân tích mỗi giờ, quét toàn thị trường mỗi ngày sau 15h. |

## Dùng nhanh (Windows)
1. Trên GitHub bấm **Code → Download ZIP**, giải nén.
2. Bấm đúp `co_phieu/run_web.bat` để mở web app, hoặc `co_phieu/run.bat` để chạy bằng dòng lệnh.
3. Mở `greenview/dist/GreenView.html` bằng Chrome/Edge để xem biểu đồ.

Cần cài Python (https://www.python.org/downloads/). Lần đầu chạy, máy tự cài các thư viện cần thiết.

> Công cụ chỉ hỗ trợ phân tích kỹ thuật, không phải lời khuyên đầu tư. Kết quả kiểm định trên dữ liệu quá khứ xem trong
> `co_phieu/README.md`. Tín hiệu hiện **chưa tốt hơn** mua/bán ngẫu nhiên.
