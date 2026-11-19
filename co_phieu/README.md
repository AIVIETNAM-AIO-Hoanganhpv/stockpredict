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
- **Timing – dự kiến ngày chốt lời**:
  - **Theo tốc độ**: đo các nhịp tăng trước của chính mã đó (mỗi phiên đi được bao nhiêu ATR), từ đó suy ra số phiên
    để đi từ giá mua tới chốt lời. Kết quả là khoảng **sớm – thường – muộn**.
  - **Theo Fibonacci thời gian**: đáy hồi cộng 0.618 / 1 / 1.618 lần độ dài nhịp tăng trước.
  - Ngày tính theo phiên giao dịch: bỏ thứ 7, chủ nhật, chưa trừ ngày lễ.
  - Hiện ở: thẻ khuyến nghị, bảng Nên mua (cột "Dự kiến chốt lời"), tab Danh mục (số phiên còn lại), TradingView
    (đường dọc kèm nhãn số phiên).
- **Tính lãi**: nhập số vốn → số cổ phiếu (lô 100), tiền và % lãi khi chạm chốt lời, tiền lỗ khi chạm cắt lỗ.
  Đã trừ phí mua 0,15%, phí bán 0,15% và thuế bán 0,1%.

## Thông tin doanh nghiệp & báo cáo tài chính (nguồn: Vietcap)
```
py du_doan.py --doanh-nghiep FPT HPG     # hồ sơ, sức khỏe tài chính, xuất BCTC ra bao_cao/<MÃ>_tai_chinh.xlsx
```
- **Hồ sơ**: tên, ngành, vốn hóa, số cổ phiếu, ngày niêm yết, giới thiệu, % sở hữu nước ngoài/nhà nước,
  cao/thấp 52 tuần, **cổ đông lớn & ban lãnh đạo**.
- **Khuyến nghị của CTCK** (Vietcap Securities): MUA/NẮM GIỮ/BÁN, giá mục tiêu, ngày. Đây là ý kiến của bên thứ ba.
- **Báo cáo tài chính**: Kết quả kinh doanh, Cân đối kế toán, Lưu chuyển tiền tệ. Lấy 5 năm và 8 quý gần nhất,
  đơn vị tỷ đồng. Hỗ trợ đủ doanh nghiệp thường, ngân hàng, chứng khoán và bảo hiểm.
- **Chỉ số**: P/E, P/B, P/S, EV/EBITDA, ROE, ROA, biên lợi nhuận, nợ vay/vốn chủ, cổ tức. Ngân hàng có thêm NIM, nợ xấu, CASA.
- **Sức khỏe tài chính 1–5★** = trung bình 4 mục:
  - Tăng trưởng: lợi nhuận và doanh thu 4 quý so với 4 quý trước.
  - Sinh lời: ROE. Đang lỗ thì 1★.
  - An toàn: nợ vay/vốn chủ. Ngân hàng tính vốn chủ/tổng tài sản.
  - Định giá: P/E hiện tại so với chính mã đó trong 3 năm.

  Điểm chỉ dùng các báo cáo **đã công bố** tính đến thời điểm chấm (theo ngày công bố), nên dùng được cho backtest.
- **Ảnh hưởng tới khuyến nghị mua**: sức khỏe từ 4 trở lên được +10 điểm; từ 2 trở xuống bị −10 điểm;
  doanh nghiệp đang lỗ bị −15 điểm. Hai trường hợp sau không được xếp "Mua mạnh".
- **Hồ sơ mở rộng**: ban lãnh đạo, công ty con & liên kết (nguồn CafeF), lịch sử trả cổ tức (tiền mặt / cổ phiếu),
  sự kiện (ĐHCĐ, phát hành, niêm yết bổ sung), giao dịch nội bộ. **Công ty kiểm toán**: chưa có nguồn lấy tự động
  (TCBS chặn truy cập tự động).
- **Web app**:
  - Tab Tra cứu có 5 mục: Kỹ thuật / Doanh nghiệp / Tài chính / Chỉ số / **Tin tức**, kèm nút tải Excel.
  - Tab **Bộ lọc** lọc theo P/E, ROE, tăng trưởng lợi nhuận, nợ, sức khỏe, CTCK, cùng khuyến nghị kỹ thuật.

## Tin tức
- **Tin theo mã**: lấy từ Google News, tổng hợp nhiều báo, kèm tin và công bố của doanh nghiệp (nguồn Vietcap).
- **Tab "Tin thị trường"** có 4 nhóm, tự làm mới mỗi 15 phút, lọc được theo nguồn, đánh giá và từ khóa/mã:
  - **Chứng khoán**: CafeF, Vietstock, VnExpress Kinh doanh.
  - **Kinh tế trong nước**: CafeF Vĩ mô và Ngân hàng, Vietstock Vĩ mô và Kinh tế.
  - **Kinh tế thế giới**: CafeF và Vietstock Quốc tế, BBC Business và MarketWatch (tiếng Anh).
  - **Chủ đề vĩ mô** (theo Google News): lãi suất, tỷ giá USD, Fed, giá vàng, giá dầu, xuất nhập khẩu, lạm phát, đầu tư công.
- **Tự gắn mã** khi tiêu đề nhắc tới mã (HPG) hoặc tên công ty (Hòa Phát, Techcombank…).
- **Nhãn Tích cực / Tiêu cực**: gắn theo từ khóa, ví dụ "lãi kỷ lục", "trúng thầu" / "thua lỗ", "bị phạt", "thủng đáy".
  Đây chỉ là gợi ý, có thể sai.
- **Tab Danh mục**: hiện tin mới của các mã đang giữ và cảnh báo khi có tin tiêu cực.

## Kết quả kiểm định trên dữ liệu quá khứ (19/11/2026)
Lệnh chạy: `py du_doan.py --kiem-dinh` (10–20 phút). Kết quả đầy đủ ở `bao_cao/kiem_dinh.md`.
- **Phạm vi:** 267 mã đủ thanh khoản, khoảng 2 năm, 26.529 điểm thời gian.
- **Cách đo:** tại mỗi điểm chỉ dùng dữ liệu đến hôm đó. Lệnh mua giả lập đã trừ phí và thuế.

| | Kết quả |
|---|---|
| Mốc so sánh: mua bất kỳ, giữ 60 phiên | lãi 44% số lần, TB **+2,1%** |
| Tín hiệu **Mua** (764 lệnh) | thắng 28%, TB **−0,7%**/lệnh, 70% lệnh chạm cắt lỗ |
| Tín hiệu **Mua mạnh** (92 lệnh) | thắng 24%, TB **−2,4%**/lệnh |
| Lệnh chờ ở vùng mua (2.745 lệnh khớp) | thắng 25%, TB 0% |
| **Bán ở đỉnh** (2.946 lần) | đúng 50% (giá thấp hơn sau 20 phiên), giá còn tăng TB +1,8% |

**Kết luận thẳng thắn:** ở cấu hình hiện tại, tín hiệu Mua và Bán ở đỉnh **chưa tốt hơn mua/bán ngẫu nhiên**.
Lý do chính là cắt lỗ quá gần (0,5 ATR dưới vùng mua): 70% số lệnh bị cắt lỗ sau khoảng 17 phiên.
Cần chỉnh lại tham số và kiểm định lại trước khi dùng các khuyến nghị để giao dịch thật.

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
dudoan/co_ban.py     hồ sơ doanh nghiệp, BCTC, chỉ số, sức khỏe tài chính, cổ tức, sự kiện, nội bộ, công ty con
dudoan/tin_tuc.py    tin tức (Google News, CafeF, Vietstock, VnExpress), gắn mã, nhãn tích cực/tiêu cực
dudoan/kiem_dinh.py  backtest tín hiệu
du_lieu_ma/ma_vn.csv danh sách mã HOSE/HNX/UPCoM (tự cập nhật)
tests/               kiểm tra bằng dữ liệu giả lập
```
