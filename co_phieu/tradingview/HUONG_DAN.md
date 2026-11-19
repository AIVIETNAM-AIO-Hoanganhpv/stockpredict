# Backtest trên TradingView

File `du_doan_xu_huong.pine` là bản **Pine Script v6** (dạng strategy). Nó chấm điểm giống công cụ Python, gồm:
- Đỉnh/đáy, MA20 (80%), MACD, Heikin Ashi;
- Stochastic, MFI, ADX;
- SMC: BOS/CHoCH, Order Block, FVG, quét thanh khoản;
- ICT: OTE, Premium/Discount.

Ngoài ra nó kết hợp thêm khung thời gian lớn hơn, rồi tự vào lệnh và thoát lệnh để TradingView tính lãi/lỗ.

## Cách thêm vào biểu đồ
1. Mở tradingview.com và chọn mã. Ví dụ: `HOSE:FPT`, `OANDA:XAUUSD`, `FX:EURUSD`, `NASDAQ:AAPL`.
2. Bấm **Pine Editor** ở dưới màn hình, xoá hết nội dung mẫu, rồi dán toàn bộ file `du_doan_xu_huong.pine`.
3. Bấm **Save**, sau đó bấm **Add to chart**.
4. Mở tab **Strategy Tester** để xem tổng lãi/lỗ, tỉ lệ thắng, số lệnh, sụt giảm tối đa và danh sách từng lệnh.

## Khi nào vào lệnh, khi nào thoát (tham số đã kiểm định – mặc định)
- **Mua** khi đủ 3 điều kiện:
  - điểm tổng = (2 × điểm khung chart + điểm khung lớn) / 3 **≥ 50**, tính theo bộ trọng số "Động lượng";
  - điểm khung chart > 0;
  - **khung lớn đang tăng**.
- **Cắt lỗ** dưới đáy hồi gần nhất 0,5 ATR; nếu không có đáy hồi thì lấy giá − 1 ATR.
- **Chốt lời = 3 × rủi ro.** **Giữ tối đa 60 nến** rồi tự đóng lệnh.
- Bộ tham số này được chỉnh bằng backtest Python trên 891 mã giai đoạn 2006–2019. Khi kiểm tra trên 2020–2026, lãi trung bình
  **+3,6%/lệnh**, trong khi mua ngẫu nhiên giữ 60 phiên được +2,3%.
- Bản Pine chỉ **gần giống** bản Python: vùng hỗ trợ được thay bằng đáy hồi gần nhất. Vì vậy kết quả trên TradingView sẽ hơi khác.
- Muốn dùng cách cũ: chọn bộ trọng số "Gốc", hạ ngưỡng về 20 và bật "Dùng Fibonacci thay cho 3R".
- **Tín hiệu đỉnh** mặc định **chỉ vẽ nhãn**, không đóng lệnh, vì kiểm định 20 năm cho thấy nó không dự báo được giá giảm.

## Tín hiệu bán ở đỉnh
Script đếm 9 dấu hiệu đỉnh:
- chạm Fibonacci mở rộng 1.272;
- Stoch quá mua;
- MFI quá mua;
- phân kỳ giảm MACD;
- quét thanh khoản đỉnh cũ;
- chạm FVG giảm (vùng cung);
- CHoCH giảm;
- nến đảo chiều (râu trên dài hoặc nhấn chìm giảm);
- đã chạy từ 3 nhịp tăng.

Khi có **từ 3 dấu hiệu** và giá đang ở gần vùng đỉnh, biểu đồ hiện nhãn **ĐỈNH** màu nâu đỏ. Khi đó:
- lệnh Mua đang mở sẽ được đóng (chốt lời);
- nếu "Chiều lệnh" cho phép Bán, script mở thêm lệnh Bán (hợp với forex/vàng; cổ phiếu VN nên chọn **Chỉ Mua**).

Bảng điểm có thêm dòng "Tín hiệu đỉnh". Bạn đổi số dấu hiệu tối thiểu trong nhóm cài đặt "Tín hiệu bán ở đỉnh".

## Ngày chốt lời dự kiến (timing)
Khi vào lệnh Mua, script vẽ một **đường dọc chấm màu xanh ngọc** tại ngày dự kiến chạm chốt lời, kèm nhãn
"Dự kiến chốt lời ~N phiên". Số phiên được tính theo tốc độ của nhịp tăng trước. Nhãn cũng ghi độ dài nhịp trước,
chính là mốc Fibonacci thời gian 1.0. Tắt bằng mục "Vẽ ngày chốt lời dự kiến" trong nhóm Hiển thị.

## Các cài đặt (nút ⚙ cạnh tên strategy)
| Cài đặt | Mặc định | Ghi chú |
|---|---|---|
| Bộ trọng số chỉ báo | Động lượng | Đã kiểm định; "Gốc" là cách cũ |
| Ngưỡng điểm | 50 | Đã kiểm định |
| Chỉ mua khi khung lớn tăng | bật | Đã kiểm định |
| Chiều lệnh | Cả Mua và Bán | Cổ phiếu VN không bán khống được: nên chọn **Chỉ Mua** |
| Khung lớn | tự chọn | Phải lớn hơn khung đang xem |
| Dùng Fibonacci thay cho 3R | tắt | Mặc định chốt lời = 3 × rủi ro (đã kiểm định) |
| Giữ tối đa | 60 nến | Đã kiểm định |
| Thoát khi về Đi ngang | tắt | Bật để thoát sớm khi xu hướng yếu đi |
| Backtest từ ngày | 01/01/2018 | |

Phí giao dịch mặc định là 0,15% mỗi chiều và vốn ban đầu là 100 triệu. Bạn đổi ở tab **Properties**.

## Cảnh báo về điện thoại
Bấm **Alert**, chọn condition là strategy này, rồi chọn *"alert() function calls only"*. TradingView sẽ gửi thông báo
mỗi khi có tín hiệu Tăng/Giảm.

## Lưu ý
- Bản Pine chỉ giống bản Python ở mức gần đúng, không trùng khớp hoàn toàn. Nguyên nhân: dữ liệu của TradingView khác dữ liệu Yahoo, và bản Pine theo dõi
  ít vùng OB/FVG hơn.
- Kết quả backtest tốt trong quá khứ **không đảm bảo** sẽ có lãi trong tương lai. Hãy thử trên nhiều mã và nhiều khung thời gian.
- File này mới được kiểm tra cú pháp trên máy, **chưa chạy thử trên TradingView thật**. Nếu TradingView báo lỗi, hãy chụp
  màn hình dòng lỗi gửi lại để sửa.
