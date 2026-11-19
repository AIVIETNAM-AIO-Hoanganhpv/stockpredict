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

## Khi nào vào lệnh, khi nào thoát
- **Mua** khi điểm tổng vượt lên trên +20 (từ Đi ngang/Giảm chuyển sang Tăng).
- **Bán khống** khi điểm tổng xuống dưới -20. Một tín hiệu ngược chiều sẽ đóng lệnh cũ rồi mở lệnh mới.
- **Chốt lời / cắt lỗ theo Fibonacci** như tài liệu: "hồi ít thì lên nhiều". Cắt lỗ đặt dưới đáy hồi (với lệnh mua).
  Nếu không tính được mức Fibonacci hợp lý, công cụ dùng mức dự phòng: 2×ATR cho cắt lỗ, 3×ATR cho chốt lời.
- Điểm tổng = điểm khung đang xem (trọng số 1) + điểm khung lớn hơn (trọng số 0,75).
  Khung lớn được tự chọn: 15m→1H, 1H→4H, 4H→D, D→W, W→M. Khung lớn chỉ dùng nến **đã đóng**, nên
  kết quả backtest không bị "nhìn trước tương lai".

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

## Các cài đặt (nút ⚙ cạnh tên strategy)
| Cài đặt | Mặc định | Ghi chú |
|---|---|---|
| Ngưỡng điểm | 20 | Ngưỡng cao hơn thì ít lệnh hơn nhưng chắc hơn |
| Chiều lệnh | Cả Mua và Bán | Cổ phiếu VN không bán khống được: nên chọn **Chỉ Mua** |
| Khung lớn | tự chọn | Phải lớn hơn khung đang xem |
| Cắt lỗ/chốt lời theo Fibonacci | bật | Tắt thì chỉ dùng mức theo ATR |
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
