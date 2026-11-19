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
- **Cổ phiếu VN**: `FPT`, `HPG`, `VNINDEX`… Công cụ lấy giá từ Vietcap. Nếu không lấy được thì dùng vnstock, sau đó đến Yahoo (`FPT.VN`).
- **Forex, vàng**: `EURUSD`, `GBPUSD`, `USDJPY`, `XAUUSD` (vàng, lấy theo hợp đồng tương lai GC=F).
- **Cổ phiếu quốc tế**: `AAPL`, `MSFT`… Nếu công cụ đoán sai loại mã, ghi rõ tiền tố: `vn:ABC`, `fx:EURUSD`, `us:IBM`.
- **File tự tải**: cần các cột Ngày, Mở, Cao, Thấp, Đóng, KL (tên tiếng Anh cũng được).

Giá Yahoo trễ khoảng 15 phút với cổ phiếu và vài phút với forex.

## Khuyến nghị mua toàn thị trường (HOSE, HNX, UPCoM)
```
py du_doan.py --quet-thi-truong              # quét ~1.500 mã (3–7 phút) → bao_cao/khuyen_nghi.xlsx, khuyen_nghi.md
py du_doan.py --quet-thi-truong --san HSX --gtgd 5 --von 200000000
```
- **Nguồn giá**: Vietcap (giá đã điều chỉnh cổ tức). Công cụ bỏ qua mã có giá trị giao dịch thấp hơn `--gtgd` tỷ đồng mỗi phiên (mặc định 1 tỷ).
- **Vùng mua đẹp** là nơi nhiều mức hỗ trợ trùng nhau (hợp lưu): Fibonacci hồi 0.5 / 0.618 / 0.705 (OTE) / 0.786,
  Order Block, FVG, MA20/MA50, đáy gần nhất.
  - Giá đang nằm trong vùng: có thể mua ngay.
  - Giá cao hơn vùng: đặt lệnh chờ ở giữa vùng, không mua đuổi.
- **Cắt lỗ**: dưới vùng mua 0,5 ATR. **Chốt lời**: theo Fibonacci mở rộng ("hồi ít thì lên nhiều").
  Các giá đều được làm tròn theo bước giá của sàn.
- **Khuyến nghị**:
  - **Mua mạnh**: xu hướng tăng mạnh, giá trong vùng mua, lãi/lỗ kỳ vọng ≥ 2.
  - **Mua**: giá trong vùng mua, lãi/lỗ kỳ vọng ≥ 1,5.
  - **Chờ về vùng mua**: xu hướng tăng nhưng giá đã chạy xa vùng mua.
  - **Theo dõi**: đi ngang, hoặc tỷ lệ lãi/lỗ thấp.
  - **Không mua**: xu hướng giảm.
- **Tầm giữ**:
  - Ngắn hạn: khung ngày, giữ 1–3 tháng, có xét thêm khung tuần.
  - Trung hạn: khung tuần, giữ 3–9 tháng, có xét thêm khung tháng.
- **Tín hiệu bán ở đỉnh** (chốt lời/thoát hàng, vì cổ phiếu VN không bán khống được). Công cụ đếm các dấu hiệu:
  - chạm Fibonacci mở rộng 1.272/1.618;
  - Stoch/MFI quá mua;
  - phân kỳ giảm MACD;
  - quét thanh khoản đỉnh cũ;
  - chạm Order Block/FVG giảm;
  - CHoCH giảm;
  - nến đảo chiều (râu trên dài, nhấn chìm giảm, mây đen);
  - đã chạy từ 3 nhịp tăng.

  Kết luận theo số dấu hiệu:
  - từ 3 dấu hiệu: **Chốt lời dần**;
  - từ 5 dấu hiệu, hoặc từ 3 dấu hiệu kèm CHoCH giảm: **Bán mạnh**;
  - 2 dấu hiệu: **Theo dõi đỉnh**.

  Kèm theo **vùng bán đẹp**: nơi hợp lưu kháng cự (Fibo mở rộng, đỉnh cũ, vùng cung).
- **Phân ngành** (19 ngành ICB cấp 2): lọc theo ngành, bảng **sức mạnh ngành** (điểm TB, % mã tăng/giảm, hiệu suất 20 phiên).
  Mã thuộc ngành Mạnh được +10 điểm khi xếp hạng mua, ngành Yếu bị −10 điểm và không được xếp "Mua mạnh".
- **Tính lãi**: nhập số vốn → số cổ phiếu (lô 100), tiền và % lãi khi chạm chốt lời, tiền lỗ khi chạm cắt lỗ.
  Đã trừ phí mua 0,15%, phí bán 0,15% và thuế bán 0,1%.

## Web app trên điện thoại
`web_app.py` là web app có 4 tab:
- **Khuyến nghị**: gồm 3 chế độ xem:
  - **Nên mua**: bảng xếp hạng mua, có thể nhập số vốn để tính lãi/lỗ;
  - **Bán ở đỉnh**: các mã đang ở vùng đỉnh, kèm vùng bán đẹp;
  - **Sức mạnh ngành**.

  Có thể lọc theo sàn, ngành, mức tín hiệu và thanh khoản.
- **Tra cứu**: gõ mã bất kỳ để xem khuyến nghị, vùng mua và máy tính lãi/lỗ, có biểu đồ vuốt và phóng to được.
- **Danh mục**: nhập mã, giá mua và số lượng. App tính lãi/lỗ hiện tại (sau phí, thuế) và gợi ý
  Giữ / Chốt lời / **Bán ở đỉnh** / Cắt lỗ. Kèm theo giá bán đề xuất, tiền lãi nếu bán ở giá đó và mức cắt lỗ động.
- **Theo dõi**: các mã trong `ma.txt`, tự làm mới mỗi giờ.

Ở mục "⚙ Cài đặt chung" có thể chọn tầm giữ (ngắn hạn/trung hạn) và số vốn mỗi lệnh.

**Cách 1 – chạy trên máy tính, xem bằng điện thoại cùng Wi-Fi:**
1. Bấm đúp `run_web.bat`.
2. Trên điện thoại, mở địa chỉ *Network URL* hiện trong cửa sổ đen (dạng `http://192.168.x.x:8501`).

**Cách 2 – đưa lên mạng miễn phí (Streamlit Community Cloud), mở được ở bất cứ đâu:**
1. Vào https://share.streamlit.io và đăng nhập bằng tài khoản GitHub.
2. Bấm **Create app**, chọn **Deploy a public app from GitHub**, rồi điền:
   - Repository: `AIVIETNAM-AIO-Hoanganhpv/draft`
   - Branch: `claude/quirky-bell-oi3coh`
   - Main file path: `co_phieu/web_app.py`
3. Mở **Advanced settings** và chọn Python **3.12**.
4. Bấm **Deploy**. Đợi vài phút là có đường link dạng `https://....streamlit.app`.
5. Mở link trên điện thoại. Nếu muốn có biểu tượng trên màn hình chính: trên iPhone bấm *Chia sẻ → Thêm vào MH chính*, trên Android bấm *⋮ → Thêm vào màn hình chính*.

Mẹo:
- Nếu repo để Private, trong phần **Settings → Sharing** của app có thể chỉ cho phép một số email được xem.
- App miễn phí sẽ "ngủ" nếu vài ngày không ai mở. Khi đó chỉ cần bấm nút đánh thức trên trang.

## Backtest trên TradingView
Xem `tradingview/HUONG_DAN.md`. Bạn dán file `tradingview/du_doan_xu_huong.pine` vào Pine Editor, rồi xem kết quả ở tab Strategy Tester.

## Tự động trên GitHub
Tệp `.github/workflows/du_doan_co_phieu.yml` cho GitHub tự chạy **mỗi giờ, từ thứ 2 đến thứ 6**. Mỗi lần chạy, GitHub phân tích các
mã trong `ma.txt` rồi lưu báo cáo vào thư mục `co_phieu/bao_cao/`. Muốn đổi danh sách mã thì sửa `ma.txt`.
Xem bảng tóm tắt tại `co_phieu/bao_cao/README.md`. Muốn xem biểu đồ, tải các tệp HTML về rồi mở bằng trình duyệt.

## Cấu trúc
```
du_doan.py           chạy bằng lệnh
web_app.py           web app (Streamlit) cho điện thoại; run_web.bat để chạy trên máy
tradingview/         bản Pine Script để backtest trên TradingView
ma.txt               danh sách mã chạy tự động
dudoan/chi_bao.py    MA, MACD, Stoch, MFI, ADX, ATR, Heikin Ashi
dudoan/cau_truc.py   đỉnh/đáy, SMC (BOS/CHoCH/OB/FVG/thanh khoản), ICT (killzone), đếm nhịp
dudoan/fibo.py       Fibonacci hồi / mở rộng, chọn điểm chốt lời
dudoan/phan_tich.py  chấm điểm từng khung, gộp đa khung, thử lại quá khứ
dudoan/du_lieu.py    tải dữ liệu (Yahoo, vnstock, CSV/Excel)
dudoan/bao_cao.py    báo cáo HTML + biểu đồ, Markdown, Excel
dudoan/khuyen_nghi.py vùng mua đẹp, khuyến nghị, tính lãi/lỗ, đánh giá danh mục
dudoan/quet.py       quét toàn thị trường VN, xếp hạng
du_lieu_ma/ma_vn.csv danh sách mã HOSE/HNX/UPCoM (tự cập nhật)
tests/               kiểm tra bằng dữ liệu giả lập
```
