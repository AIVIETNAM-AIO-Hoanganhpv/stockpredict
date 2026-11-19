# GreenView — công cụ biểu đồ giá kiểu TradingView

Chạy hoàn toàn trong trình duyệt, không cần cài đặt, không cần máy chủ.

## Cách dùng nhanh
1. Mở **`dist/GreenView.html`** bằng Chrome hoặc Edge trên máy tính (nháy đúp vào file). Bản này lấy được giá thật qua API.
2. Bấm tên mã (góc trên trái) để đổi mã và nguồn dữ liệu. Có thể gõ thẳng chữ cái trên bàn phím để mở ô tìm mã.
3. Nút ☀/🌙 đổi giữa hai giao diện: **Sáng xanh đậm** và **Ngọc lục bảo (tối)**.
4. Mọi thứ (danh sách theo dõi, cảnh báo, hình vẽ, bố cục, mẫu chỉ báo) tự lưu trong trình duyệt của máy đó.

## Nguồn dữ liệu
| Nguồn | Cần gì | Cập nhật |
|---|---|---|
| Binance (crypto) | Không cần gì | Realtime (WebSocket) |
| Cổ phiếu Việt Nam (VNDirect, dự phòng TCBS) | Không cần key, giá theo nghìn đồng | 20 giây/lần |
| Mỹ / Forex / Vàng (Twelve Data) | API key miễn phí: twelvedata.com/register | 60 giây/lần |
| Dữ liệu giả lập | Không cần mạng | Mỗi giây |
| File CSV | File của cô (Ngày, Mở, Cao, Thấp, Đóng, KL) | Tĩnh |

Nhập key và proxy: **⚙ Cài đặt › Nguồn dữ liệu**. Nếu API cổ phiếu VN bị trình duyệt chặn, điền proxy, ví dụ `https://corsproxy.io/?url=`.

## Có gì bên trong
- **Chỉ báo (ƒx):** 112 chỉ báo tích hợp sẵn, xếp theo tên như danh sách của TradingView, có tìm kiếm, mục yêu thích và bảng cài đặt riêng cho từng chỉ báo (đầu vào, màu, độ dày, ẩn/hiện). Thêm được nhiều lần với tham số khác nhau.
- **Chiến lược:** 23 chiến lược có sẵn, mỗi chiến lược có bảng *Kiểm tra chiến lược*: lãi ròng, tỉ lệ thắng, hệ số lợi nhuận, sụt giảm tối đa, đường vốn và danh sách lệnh.
- **Hồ sơ khối lượng:** Visible range, Fixed range, Session, Periodic, Auto anchored.
- **Mô hình:** 44 mô hình nến Nhật, 17 mô hình biểu đồ tự nhận diện (hai đỉnh, vai-đầu-vai, cờ, nêm, tam giác, cốc tay cầm, sóng Elliott…) và Auto trend detector.
- **Công cụ vẽ:** 85 công cụ chia 8 nhóm giống TradingView (xu hướng, Gann & Fibonacci, mô hình, dự đoán & đo lường, hình học, chú thích, hình ảnh/biểu tượng). Hình vẽ chọn được, kéo điểm, kéo cả hình, đổi màu/nét/chữ, khoá, nhân bản, ẩn, xoá. Có nam châm yếu/mạnh, giữ chế độ vẽ, khoá/ẩn/xoá tất cả.
- **16 loại biểu đồ:** thanh, nến, nến rỗng, đường, đường có điểm, bậc thang, vùng, HLC, đường cơ sở, cột, cao-thấp, Heikin Ashi, Renko, Line break, Kagi, Point & figure.
- **Trung tâm phân tích:** bố cục (lưu/mở/mới), cài đặt biểu đồ (màu nến, thang log/%/chỉ số 100, lưới), so sánh mã, cảnh báo giá, phát lại thanh, mẫu chỉ báo, cây đối tượng, chỉ số kỹ thuật (đồng hồ Mua/Bán), thông tin mã, chụp ảnh.

## Phím tắt
`Alt+T` đường xu hướng · `Alt+H` đường ngang · `Alt+V` đường dọc · `Alt+F` Fibonacci · `Alt+P` kênh song song · `Alt+R` hình chữ nhật · `Alt+A` tạo cảnh báo · `Alt+I` hoặc `/` mở chỉ báo · `Esc` thoát công cụ · `Delete` xoá hình đang chọn · bấm đúp hình có chữ để sửa chữ.

## Chưa làm được (cần dữ liệu ngoài)
Advance/decline, Cumulative volume index (dữ liệu toàn sàn); Correlation, Ratio, Spread (dùng "So sánh" thay thế); Open interest, Options (dữ liệu phái sinh); Performance, Price target, Seasonality, Tài chính, Dự báo (nguồn trả phí); script cộng đồng của TradingView; công cụ "Đăng"/"Ý tưởng" (mạng xã hội riêng của TradingView). Các chỉ báo CVD, Volume delta, Up/down volume là bản **ước lượng** từ nến, vì không có dữ liệu khớp lệnh từng giao dịch.

## Cấu trúc mã nguồn
```
src/index.html        khung giao diện
src/css/app.css       giao diện, hai theme, bố cục điện thoại
src/js/util.js        lưu trữ, gọi API, định dạng
src/js/theme.js       hai theme, logo GreenView, biểu tượng
src/js/sources.js     nguồn dữ liệu (Binance, VN, Twelve Data, giả lập, CSV)
src/js/ta.js          thư viện hàm kỹ thuật (giống ta.* của Pine Script)
src/js/indicators.js  112 chỉ báo + hồ sơ khối lượng + đánh giá kỹ thuật
src/js/patterns.js    mô hình nến & mô hình biểu đồ
src/js/strategies.js  23 chiến lược + bộ kiểm tra
src/js/chart.js       điều khiển biểu đồ, loại biểu đồ, so sánh, phát lại
src/js/drawcore.js    khung xử lý công cụ vẽ (chọn, kéo, nam châm…)
src/js/tools.js       định nghĩa từng công cụ vẽ + biểu tượng
src/js/ui.js          thanh công cụ, chú thích, các hộp thoại
src/js/panels.js      danh sách theo dõi, cảnh báo, trung tâm phân tích…
src/js/app.js         khởi động, tải mã, phím tắt
build.py              gộp tất cả thành 1 file:  python build.py
```
Thêm chỉ báo mới: trong `indicators.js`, gọi `R('id', 'Tên', { inputs, plots, calc(D, I) { … } })`, xem các chỉ báo có sẵn làm mẫu.

Biểu đồ dùng thư viện mã nguồn mở Lightweight Charts™ của TradingView (Apache 2.0). Công cụ chỉ để xem và phân tích giá, không phải lời khuyên đầu tư.
