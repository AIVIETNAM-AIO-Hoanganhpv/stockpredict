# Công cụ dự đoán xu hướng giá (cổ phiếu VN, quốc tế, forex)

Dự đoán **Tăng / Giảm / Đi ngang** cho từng mã. Công cụ kết hợp:

| Nhóm | Dùng gì |
|---|---|
| Chỉ báo | **Stochastic**, **MACD**, **MFI** (dòng tiền), **ADX** (độ mạnh xu hướng) |
| SMC | Cấu trúc thị trường (BOS, CHoCH), Order Block, Fair Value Gap, quét thanh khoản |
| ICT | Vùng Premium/Discount, vùng OTE (hồi 62–79%), killzone London/New York (khung 15m, 1H) |
| LEVEL 1 | Xu hướng theo đỉnh/đáy, vị thế giá so với MA20 (80%), MACD, nến Heikin Ashi, đếm nhịp |
| Fibonacci | Hồi 23,6–78,6% và mở rộng 1–2. Chốt lời theo quy tắc "hồi ít thì lên nhiều" |

Mỗi yếu tố bỏ phiếu tăng hoặc giảm kèm trọng số. Kết quả là điểm từ **-100 đến +100**:
- trên +20 là Tăng;
- dưới -20 là Giảm;
- còn lại là Đi ngang.

Công cụ chấm trên nhiều khung thời gian rồi gộp lại:
- Chứng khoán: tháng (M), tuần (W), ngày (D).
- Forex: W, D, 4H, 1H, 15m.

> ⚠ Đây là công cụ hỗ trợ phân tích kỹ thuật, **không phải lời khuyên đầu tư**. Mục "Thử lại trên
> quá khứ" trong báo cáo cho biết tỉ lệ đúng trước đây của từng mã. Nên xem con số này trước khi tin vào tín hiệu.

## Chạy trên máy Windows
1. Bấm đúp `run.bat`. Lần đầu máy sẽ tự cài thư viện.
2. Gõ mã cần phân tích, ví dụ `FPT EURUSD XAUUSD`, rồi bấm Enter. Kết quả hiện ngay trên màn hình.
3. Nếu để trống rồi bấm Enter, công cụ phân tích mọi mã trong `ma.txt` và mở báo cáo `bao_cao/index.html`.

Chạy bằng lệnh:
```
py du_doan.py FPT HPG EURUSD --thu-lai     # phân tích, kèm thử lại trên quá khứ
py du_doan.py --tat-ca --bao-cao           # mọi mã trong ma.txt → bao_cao/
py du_doan.py --file gia.csv --ten ABC     # dùng file giá tự tải (CSV/Excel)
```

## Mã được hỗ trợ
- **Cổ phiếu VN**: `FPT`, `HPG`, `VNINDEX`… Công cụ dùng `vnstock` nếu máy đã cài được, nếu không thì lấy từ Yahoo (`FPT.VN`).
- **Forex, vàng**: `EURUSD`, `GBPUSD`, `USDJPY`, `XAUUSD` (vàng, lấy theo hợp đồng tương lai GC=F).
- **Cổ phiếu quốc tế**: `AAPL`, `MSFT`… Nếu công cụ đoán sai loại mã, ghi rõ tiền tố: `vn:ABC`, `fx:EURUSD`, `us:IBM`.
- **File tự tải**: cần các cột Ngày, Mở, Cao, Thấp, Đóng, KL (tên tiếng Anh cũng được).

Giá Yahoo trễ khoảng 15 phút với cổ phiếu và vài phút với forex.

## Tự động trên GitHub
Tệp `.github/workflows/du_doan_co_phieu.yml` cho GitHub tự chạy **mỗi giờ, từ thứ 2 đến thứ 6**. Mỗi lần chạy, GitHub phân tích các
mã trong `ma.txt` rồi lưu báo cáo vào thư mục `co_phieu/bao_cao/`. Muốn đổi danh sách mã thì sửa `ma.txt`.
Xem bảng tóm tắt tại `co_phieu/bao_cao/README.md`. Muốn xem biểu đồ, tải các tệp HTML về rồi mở bằng trình duyệt.

## Cấu trúc
```
du_doan.py           chạy bằng lệnh
ma.txt               danh sách mã chạy tự động
dudoan/chi_bao.py    MA, MACD, Stoch, MFI, ADX, ATR, Heikin Ashi
dudoan/cau_truc.py   đỉnh/đáy, SMC (BOS/CHoCH/OB/FVG/thanh khoản), ICT (killzone), đếm nhịp
dudoan/fibo.py       Fibonacci hồi / mở rộng, chọn điểm chốt lời
dudoan/phan_tich.py  chấm điểm từng khung, gộp đa khung, thử lại quá khứ
dudoan/du_lieu.py    tải dữ liệu (Yahoo, vnstock, CSV/Excel)
dudoan/bao_cao.py    báo cáo HTML + biểu đồ, Markdown, Excel
tests/               kiểm tra bằng dữ liệu giả lập
```
