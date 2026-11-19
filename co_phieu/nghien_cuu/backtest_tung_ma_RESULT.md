# Per-symbol backtest – MACD + Sto, LEVEL 1 (2 MA), app rule (2026-11-19)

Code: `strat.py` (rules), `run.py` (per-symbol runs), `agg.py` (tables, Excel, JSON), `feat.py` (app-rule features), `dl_vn.py`, `dl_us.py`.
Outputs: `bt_tung_ma.xlsx`, `ket_qua_tung_ma.json`, full tables `tables.md`.

## Verdict (read first)
- **No strategy beats buy & hold on the typical symbol.** On liquid VN stocks each W/M strategy beats B&H on only **27–33 %** of symbols
  (median CAGR +0.3 … +1.6 %/yr vs B&H +6.1 … +6.7 %/yr). On the 20 US stocks/ETFs and on gold and BTC the strategies beat B&H on **0 %** of symbols.
  The only consistent benefit is a smaller drawdown (median −22 … −58 % vs −82 % for B&H in VN), because the strategies are in the market only 17–39 % of the time.
- **Choosing "symbols that fit a strategy" does not work out of sample.** Rank correlation between a symbol's first-half and second-half result is
  **−0.3 … +0.1** for every strategy and universe. Ranking by first-half total return or by first-half excess over B&H, the top 50 do no better than random
  in the second half (in VN liquid the top group is often *worse* than the bottom group).
  One exception to report honestly: on **monthly** strategies, ranking VN stocks by first-half **average % per trade** picks a top-50 whose second-half
  total return is higher (median +26 … +31 % vs ≈ 0 % for all; random-50 p ≈ 0.00). But those stocks also rose more under buy & hold
  (half-2 B&H median 58 % vs 47 %), most of them (56–58 %) still lost to B&H in half 2, and the effect disappears when ranking by total return or by
  excess over B&H. It is stock momentum, not a strategy fit, and it is not robust to the ranking metric.
- **The best strategy per symbol does not persist.** The strategy that was best for a stock in half 1 is still best in half 2 for 20 % (VN liquid) /
  24 % (VN all) of stocks – chance is 25 %. Following "the half-1 winner" gave a lower half-2 median than simply averaging the 4 strategies.
- Gold / BTC: all versions trail B&H (gold B&H +10.5 %/yr vs best rule +3.6 %; BTC B&H +50 %/yr vs best +32.7 % for 2MA D).

## Setup
- Universe: 1,516 listed VN stocks (`ma_vn.csv`; UTT had no data; 11 with < 60 bars dropped → 1,505), daily OHLCV from Vietcap (adjusted, full history,
  up to 2000-07); 20 US stocks/ETFs + GC=F (gold) + BTC-USD from Yahoo (max history). Survivorship bias: delisted VN stocks are missing.
- Each symbol is simulated on its own: 100 % of capital, one episode at a time, compounding, cash earns 0. Signal at bar close, fill at next daily open;
  stops on daily lows, fill at min(open, stop). Costs: VN buy 0.15 %, sell 0.25 % (incl. tax); US, gold, BTC 0.05 %/side.
  W/M bars: W-FRI / calendar month from daily, only completed bars.
- **Per user decision, stocks are tested on W and M only; gold/BTC on D and W.** No liquidity filter on entries (illiquid symbols are flagged instead).
- **MACD + Sto** (bt_macd_sto SPEC, Sto 8-5-3 / 13-13-5 fixed, MACD 12-26-9): position order (30 %) on Mua1|Mua2, confirmation (70 %) on XN1|XN2|XN3
  while in profit, swing-pivot stops; exit (a) = first sell signal, touch threshold 2. W: filter last completed month MA10 > MA20. M: no filter.
  Gold/BTC D: threshold 1, exit (c) MA10×MA20.
- **2MA / LEVEL 1** (bt_level1 SPEC + `level1.py` exits): W MA6/10 (bigger TF M must be up), M MA10/20 (no bigger TF); gold/BTC MA5/10 on D and W.
  Position order 30 % + confirmation 70 %; first close below the condition MA → sell 70 % (only 30 % if the lower TF has made ≤ 1 leg since entry,
  counted with `level1._nhip` on lower-TF closes vs MA6); signal MA crossing below condition MA → sell the rest; per-lot stops. Leg-size factor and GĐ2 probe not used.
- **App rule (daily, reference only)**: score ≥ 50 + weekly trend up, stop = zone low − 0.5 ATR (else −1 ATR), TP 3R, max 60 bars (`toi_uu.mo_phong`
  default ThamSo; my re-implementation matches `mo_phong` exactly on FPT/HPG/AMV). Features: `features_full.pkl` (891 VN stocks, **step 10 bars, liquid
  points only**) + `toi_uu.trich_xuat_ma` (step 10, all points) for 51 more VN stocks and all 22 global symbols. Extraction for the other ~575 (mostly
  illiquid) VN stocks was stopped by user decision (≈ 75 min of CPU) → no app-rule row for them. "+ lọc pha" = entries only when bt_chuky `risk_on`.
- Flags: illiquid = median 20-day traded value over the last 250 sessions < 1 bn VND (1,213 of 1,505 VN stocks are illiquid or < 2 years);
  short = < 2 years of history. Halves = each symbol's bars split in two; half stats use trades by entry bar and the equity ratio across the split.

## Aggregate (symbols with ≥ 2 years and ≥ 1 trade; medians across symbols; CAGR over each symbol's full span)
| group                       | strategy                              |   with_trades |   trades |   beats_pct |   med_avg |   pooled_avg |   med_win |   med_cagr |   med_bh_cagr |   med_mdd |   med_bh_mdd |   med_expo |
|:----------------------------|:--------------------------------------|--------------:|---------:|------------:|----------:|-------------:|----------:|-----------:|--------------:|----------:|-------------:|-----------:|
| VN liquid (≥1 bn/day, ≥2 y) | MACD + Sto Tuần                       |           280 |     2090 |        27.5 |       0.7 |          2.6 |      33.3 |        0.3 |           6.5 |     -22.4 |        -81.6 |       16.8 |
| VN liquid (≥1 bn/day, ≥2 y) | MACD + Sto Tháng                      |           250 |      704 |        32.8 |       3.4 |         18.1 |      40   |        0.5 |           6.1 |     -24.2 |        -82.8 |       20.7 |
| VN liquid (≥1 bn/day, ≥2 y) | 2MA Tuần (MA6/10; vàng, BTC MA5/10)   |           287 |     3956 |        32.8 |       2.9 |          4.4 |      28.6 |        1.6 |           6.6 |     -39.9 |        -81   |       20.1 |
| VN liquid (≥1 bn/day, ≥2 y) | 2MA Tháng (MA10/20)                   |           278 |      894 |        32.4 |      11.4 |         32.3 |      50   |        1.4 |           6.7 |     -57.6 |        -81.6 |       38.8 |
| VN liquid (≥1 bn/day, ≥2 y) | Quy tắc app (D – tham khảo)           |           283 |     2252 |        32.5 |       4   |          4.1 |      50   |        1   |           6.3 |     -38.4 |        -81.3 |       10   |
| VN liquid (≥1 bn/day, ≥2 y) | Quy tắc app + lọc pha (D – tham khảo) |           278 |     1750 |        32.7 |       3.8 |          4.8 |      50   |        0.8 |           6.2 |     -34.4 |        -81.4 |        8.2 |
| VN illiquid                 | MACD + Sto Tuần                       |          1047 |     6611 |        38.9 |      -0.8 |          1.3 |      25   |       -0.5 |           2.8 |     -25.3 |        -80.2 |       14.8 |
| VN illiquid                 | MACD + Sto Tháng                      |          1006 |     2731 |        40.9 |      -0.4 |          7.1 |      33.3 |       -0.1 |           2.6 |     -24.1 |        -80.6 |       19.9 |
| VN illiquid                 | 2MA Tuần (MA6/10; vàng, BTC MA5/10)   |          1124 |    13528 |        37.1 |      -0.6 |          3.4 |      25   |       -1   |           2.6 |     -44.8 |        -79.8 |       15.9 |
| VN illiquid                 | 2MA Tháng (MA10/20)                   |          1074 |     3091 |        42.3 |      -0.3 |         20.2 |      33.3 |       -0.4 |           2.6 |     -52.8 |        -80.1 |       32.1 |
| VN illiquid                 | Quy tắc app (D – tham khảo)           |           428 |     1501 |        45.3 |      -3.5 |          0.6 |      33.3 |       -0.9 |           0.6 |     -32.7 |        -86.1 |        3   |
| VN illiquid                 | Quy tắc app + lọc pha (D – tham khảo) |           390 |     1127 |        45.6 |      -4   |          1.4 |      33.3 |       -0.8 |           0.2 |     -29.9 |        -86.4 |        2.7 |
| VN all                      | MACD + Sto Tuần                       |          1327 |     8701 |        36.5 |      -0.5 |          1.6 |      27.3 |       -0.3 |           3.3 |     -24.5 |        -80.6 |       15.5 |
| VN all                      | MACD + Sto Tháng                      |          1256 |     3435 |        39.3 |       0.2 |          9.4 |      33.3 |       -0   |           3.3 |     -24.1 |        -81   |       20.1 |
| VN all                      | 2MA Tuần (MA6/10; vàng, BTC MA5/10)   |          1411 |    17484 |        36.2 |       0   |          3.6 |      25   |       -0.5 |           3.3 |     -43.7 |        -80   |       16.5 |
| VN all                      | 2MA Tháng (MA10/20)                   |          1352 |     3985 |        40.2 |       2.4 |         22.9 |      33.3 |       -0.1 |           3.3 |     -53.8 |        -80.3 |       33.8 |
| VN all                      | Quy tắc app (D – tham khảo)           |           711 |     3753 |        40.2 |      -0.1 |          2.7 |      40   |       -0.4 |           2.7 |     -34.7 |        -84   |        5.3 |
| VN all                      | Quy tắc app + lọc pha (D – tham khảo) |           668 |     2877 |        40.3 |       0.5 |          3.5 |      42.3 |       -0.3 |           2.3 |     -32   |        -84.1 |        4.3 |
| US stocks/ETF (20)          | MACD + Sto Tuần                       |            20 |      671 |         0   |       2.3 |          3.5 |      47   |        1.9 |          16.3 |     -27.8 |        -73.8 |       27.6 |
| US stocks/ETF (20)          | MACD + Sto Tháng                      |            20 |      212 |         0   |      15.5 |         38.1 |      55.9 |        3.4 |          16.3 |     -34.3 |        -73.8 |       36.6 |
| US stocks/ETF (20)          | 2MA Tuần (MA6/10; vàng, BTC MA5/10)   |            20 |     1256 |         0   |       2.9 |          3.3 |      43.6 |        4   |          16.3 |     -44.8 |        -73.8 |       39.8 |
| US stocks/ETF (20)          | 2MA Tháng (MA10/20)                   |            20 |      154 |         0   |      64.4 |        111.3 |      58.6 |        6.5 |          16.3 |     -46.9 |        -73.8 |       58.4 |
| US stocks/ETF (20)          | Quy tắc app (D – tham khảo)           |            20 |      776 |         0   |       3.6 |          4.1 |      55   |        2.4 |          16.3 |     -40.6 |        -73.8 |       17.8 |
| Gold + BTC                  | MACD + Sto Tuần                       |             2 |       30 |         0   |      14   |          7.8 |      50   |        7.1 |          30.3 |     -42.6 |        -63.9 |       40.8 |
| Gold + BTC                  | 2MA Tuần (MA6/10; vàng, BTC MA5/10)   |             2 |       60 |         0   |      13.8 |          8.9 |      43.2 |       11.9 |          30.3 |     -42.8 |        -63.9 |       35   |
| Gold + BTC                  | MACD + Sto Ngày (vàng, BTC)           |             2 |      195 |         0   |       0.8 |          0.8 |      34.5 |        5.5 |          30.3 |     -23.7 |        -63.9 |       31.9 |
| Gold + BTC                  | 2MA Ngày (vàng, BTC; MA5/10)          |             2 |      254 |         0   |       2.3 |          2   |      34.4 |       17.2 |          30.3 |     -31.5 |        -63.9 |       26.1 |
| Gold + BTC                  | Quy tắc app (D – tham khảo)           |             2 |       47 |         0   |       9.7 |         10.6 |      62.7 |       16.6 |          30.3 |     -33.9 |        -63.9 |       19.1 |

`pooled_avg` (all trades averaged) is inflated by a few huge monthly trades; use the median columns.

## Selection test (rank by half 1 → second-half result of the top group vs all eligible symbols)
Eligible: ≥ 2 years, ≥ 5 half-1 trades (W, app) or ≥ 2 (M). Top = 50, or one third of the eligible symbols if fewer than 150.
`p_rand` = share of 2,000 random same-size groups whose half-2 median total return ≥ the top group's (small = top group really better).
`h2_ex_med` = median (half-2 strategy total − half-2 B&H), in percentage points.
| universe      | strategy                            | rank_by          | set   |   n |   rho |   p_rand |   h1_tot_med |   h2_tot_med |   h2_avg_pooled |   h2_beats_bh |   h2_ex_med |
|:--------------|:------------------------------------|:-----------------|:------|----:|------:|---------:|-------------:|-------------:|----------------:|--------------:|------------:|
| VN liquid     | MACD + Sto Tuần                     | H1 total return  | top   |  20 |  -0.2 |      0.9 |         57.1 |         -5   |             1.3 |          35   |       -45.6 |
| VN liquid     | MACD + Sto Tuần                     | H1 total return  | all   |  60 |  -0.2 |    nan   |         10   |          5   |             3.4 |          31.7 |       -71.5 |
| VN liquid     | MACD + Sto Tuần                     | H1 avg %/trade   | top   |  20 |  -0.2 |      0.8 |         57.1 |         -2.4 |             2.9 |          35   |       -34.2 |
| VN liquid     | MACD + Sto Tuần                     | H1 avg %/trade   | all   |  60 |  -0.2 |    nan   |         10   |          5   |             3.4 |          31.7 |       -71.5 |
| VN liquid     | MACD + Sto Tuần                     | H1 excess vs B&H | top   |  20 |  -0.3 |      0.1 |         -0   |         12.6 |             3.7 |          15   |      -189.2 |
| VN liquid     | MACD + Sto Tuần                     | H1 excess vs B&H | all   |  60 |  -0.3 |    nan   |         10   |          5   |             3.4 |          31.7 |       -71.5 |
| VN liquid     | MACD + Sto Tháng                    | H1 total return  | top   |  32 |  -0.1 |      0.4 |         59.9 |          1.5 |             2.1 |          34.4 |       -24.7 |
| VN liquid     | MACD + Sto Tháng                    | H1 total return  | all   |  96 |  -0.1 |    nan   |          9.3 |          1   |             8.6 |          27.1 |       -55.9 |
| VN liquid     | MACD + Sto Tháng                    | H1 avg %/trade   | top   |  32 |  -0.1 |      0   |         54.6 |         30.9 |             3.1 |          43.8 |       -24.7 |
| VN liquid     | MACD + Sto Tháng                    | H1 avg %/trade   | all   |  96 |  -0.1 |    nan   |          9.3 |          1   |             8.6 |          27.1 |       -55.9 |
| VN liquid     | MACD + Sto Tháng                    | H1 excess vs B&H | top   |  32 |  -0   |      0   |         -0.2 |         18.1 |            16.8 |          28.1 |       -60.4 |
| VN liquid     | MACD + Sto Tháng                    | H1 excess vs B&H | all   |  96 |  -0   |    nan   |          9.3 |          1   |             8.6 |          27.1 |       -55.9 |
| VN liquid     | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 total return  | top   |  50 |  -0.2 |      1   |        135   |        -15.5 |             0.5 |          36   |       -41.3 |
| VN liquid     | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 total return  | all   | 162 |  -0.2 |    nan   |         32   |         -3.1 |             2.8 |          29   |       -56.2 |
| VN liquid     | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 avg %/trade   | top   |  50 |  -0.2 |      0.8 |        132.8 |         -9.7 |             1.4 |          38   |       -48.3 |
| VN liquid     | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 avg %/trade   | all   | 162 |  -0.2 |    nan   |         32   |         -3.1 |             2.8 |          29   |       -56.2 |
| VN liquid     | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 excess vs B&H | top   |  50 |  -0.2 |      0.1 |         41.7 |          3   |             3.5 |          22   |      -147.4 |
| VN liquid     | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 excess vs B&H | all   | 162 |  -0.2 |    nan   |         32   |         -3.1 |             2.8 |          29   |       -56.2 |
| VN liquid     | 2MA Tháng (MA10/20)                 | H1 total return  | top   |  40 |  -0.1 |      0.8 |         91.6 |         -2.3 |            15.9 |          25   |       -47.5 |
| VN liquid     | 2MA Tháng (MA10/20)                 | H1 total return  | all   | 121 |  -0.1 |    nan   |         16.3 |          2.4 |            16.3 |          21.5 |       -75.2 |
| VN liquid     | 2MA Tháng (MA10/20)                 | H1 avg %/trade   | top   |  40 |  -0.1 |      0.3 |         85.2 |          6.9 |            13.4 |          30   |       -68.9 |
| VN liquid     | 2MA Tháng (MA10/20)                 | H1 avg %/trade   | all   | 121 |  -0.1 |    nan   |         16.3 |          2.4 |            16.3 |          21.5 |       -75.2 |
| VN liquid     | 2MA Tháng (MA10/20)                 | H1 excess vs B&H | top   |  40 |  -0.3 |      0.2 |         18.9 |          7.6 |            17.5 |          12.5 |       -98.5 |
| VN liquid     | 2MA Tháng (MA10/20)                 | H1 excess vs B&H | all   | 121 |  -0.3 |    nan   |         16.3 |          2.4 |            16.3 |          21.5 |       -75.2 |
| VN liquid     | Quy tắc app (D – tham khảo)         | H1 total return  | top   |  22 |  -0.1 |      0.6 |        110.9 |          8.4 |             1.9 |          50   |         1.7 |
| VN liquid     | Quy tắc app (D – tham khảo)         | H1 total return  | all   |  66 |  -0.1 |    nan   |         29.6 |         13.7 |             3.2 |          37.9 |       -27.4 |
| VN liquid     | Quy tắc app (D – tham khảo)         | H1 avg %/trade   | top   |  22 |  -0.1 |      0.6 |        110.9 |          8.4 |             2.2 |          45.5 |        -9.6 |
| VN liquid     | Quy tắc app (D – tham khảo)         | H1 avg %/trade   | all   |  66 |  -0.1 |    nan   |         29.6 |         13.7 |             3.2 |          37.9 |       -27.4 |
| VN liquid     | Quy tắc app (D – tham khảo)         | H1 excess vs B&H | top   |  22 |  -0   |      0   |         19.9 |         42   |             5.7 |          40.9 |       -51.6 |
| VN liquid     | Quy tắc app (D – tham khảo)         | H1 excess vs B&H | all   |  66 |  -0   |    nan   |         29.6 |         13.7 |             3.2 |          37.9 |       -27.4 |
| VN all (≥2 y) | MACD + Sto Tuần                     | H1 total return  | top   |  50 |   0   |      0.1 |         52.2 |          0.6 |             1.5 |          32   |       -95.2 |
| VN all (≥2 y) | MACD + Sto Tuần                     | H1 total return  | all   | 262 |   0   |    nan   |          1.4 |         -3.8 |             0.9 |          29.4 |       -72.5 |
| VN all (≥2 y) | MACD + Sto Tuần                     | H1 avg %/trade   | top   |  50 |   0   |      0.1 |         52.2 |          0.6 |             1.8 |          34   |       -62.1 |
| VN all (≥2 y) | MACD + Sto Tuần                     | H1 avg %/trade   | all   | 262 |   0   |    nan   |          1.4 |         -3.8 |             0.9 |          29.4 |       -72.5 |
| VN all (≥2 y) | MACD + Sto Tuần                     | H1 excess vs B&H | top   |  50 |  -0.1 |      0.9 |          3.7 |         -6.1 |             0.7 |          36   |       -27.8 |
| VN all (≥2 y) | MACD + Sto Tuần                     | H1 excess vs B&H | all   | 262 |  -0.1 |    nan   |          1.4 |         -3.8 |             0.9 |          29.4 |       -72.5 |
| VN all (≥2 y) | MACD + Sto Tháng                    | H1 total return  | top   |  50 |   0.1 |      0.1 |         73   |          1.5 |             3.2 |          36   |       -18.3 |
| VN all (≥2 y) | MACD + Sto Tháng                    | H1 total return  | all   | 387 |   0.1 |    nan   |          2.2 |         -0.9 |             5.3 |          33.3 |       -42.6 |
| VN all (≥2 y) | MACD + Sto Tháng                    | H1 avg %/trade   | top   |  50 |   0   |      0   |         68.3 |         26.2 |             4.1 |          42   |       -12.3 |
| VN all (≥2 y) | MACD + Sto Tháng                    | H1 avg %/trade   | all   | 387 |   0   |    nan   |          2.2 |         -0.9 |             5.3 |          33.3 |       -42.6 |
| VN all (≥2 y) | MACD + Sto Tháng                    | H1 excess vs B&H | top   |  50 |   0   |      0.7 |          8.1 |         -1.6 |            12.6 |          46   |       -37.3 |
| VN all (≥2 y) | MACD + Sto Tháng                    | H1 excess vs B&H | all   | 387 |   0   |    nan   |          2.2 |         -0.9 |             5.3 |          33.3 |       -42.6 |
| VN all (≥2 y) | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 total return  | top   |  50 |   0.1 |      0   |        221.9 |          1.6 |             1.1 |          38   |       -49.2 |
| VN all (≥2 y) | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 total return  | all   | 706 |   0.1 |    nan   |         -2.8 |        -10.1 |             0.7 |          29.9 |       -51.3 |
| VN all (≥2 y) | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 avg %/trade   | top   |  50 |   0.1 |      0   |        192.6 |          0.5 |             1.4 |          40   |       -40.1 |
| VN all (≥2 y) | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 avg %/trade   | all   | 706 |   0.1 |    nan   |         -2.8 |        -10.1 |             0.7 |          29.9 |       -51.3 |
| VN all (≥2 y) | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 excess vs B&H | top   |  50 |  -0   |      0   |         97.4 |          1.6 |             2.9 |          46   |       -13.5 |
| VN all (≥2 y) | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 excess vs B&H | all   | 706 |  -0   |    nan   |         -2.8 |        -10.1 |             0.7 |          29.9 |       -51.3 |
| VN all (≥2 y) | 2MA Tháng (MA10/20)                 | H1 total return  | top   |  50 |   0   |      0.1 |        249   |          7.5 |            12.3 |          36   |       -27.5 |
| VN all (≥2 y) | 2MA Tháng (MA10/20)                 | H1 total return  | all   | 504 |   0   |    nan   |         -3.7 |         -2.3 |             8.3 |          26.8 |       -42.6 |
| VN all (≥2 y) | 2MA Tháng (MA10/20)                 | H1 avg %/trade   | top   |  50 |   0   |      0   |        226   |         29.8 |            16.6 |          38   |       -20   |
| VN all (≥2 y) | 2MA Tháng (MA10/20)                 | H1 avg %/trade   | all   | 504 |   0   |    nan   |         -3.7 |         -2.3 |             8.3 |          26.8 |       -42.6 |
| VN all (≥2 y) | 2MA Tháng (MA10/20)                 | H1 excess vs B&H | top   |  50 |   0   |      0.4 |        115.7 |         -1.3 |             6.3 |          26   |       -55.6 |
| VN all (≥2 y) | 2MA Tháng (MA10/20)                 | H1 excess vs B&H | all   | 504 |   0   |    nan   |         -3.7 |         -2.3 |             8.3 |          26.8 |       -42.6 |
| VN all (≥2 y) | Quy tắc app (D – tham khảo)         | H1 total return  | top   |  31 |   0.1 |      0.2 |         99.7 |         12.5 |             2.9 |          48.4 |        -3.7 |
| VN all (≥2 y) | Quy tắc app (D – tham khảo)         | H1 total return  | all   |  95 |   0.1 |    nan   |         19.9 |          4.2 |             2.9 |          40   |       -24.1 |
| VN all (≥2 y) | Quy tắc app (D – tham khảo)         | H1 avg %/trade   | top   |  31 |   0.1 |      0.2 |         99.7 |         12.5 |             2.7 |          51.6 |         7.1 |
| VN all (≥2 y) | Quy tắc app (D – tham khảo)         | H1 avg %/trade   | all   |  95 |   0.1 |    nan   |         19.9 |          4.2 |             2.9 |          40   |       -24.1 |
| VN all (≥2 y) | Quy tắc app (D – tham khảo)         | H1 excess vs B&H | top   |  31 |   0.1 |      0   |         19.9 |         29.2 |             6.2 |          48.4 |        -7.1 |
| VN all (≥2 y) | Quy tắc app (D – tham khảo)         | H1 excess vs B&H | all   |  95 |   0.1 |    nan   |         19.9 |          4.2 |             2.9 |          40   |       -24.1 |
| US (20)       | MACD + Sto Tuần                     | H1 total return  | top   |   5 |   0.2 |    nan   |        175.6 |         97.1 |             3   |           0   |     -1987.9 |
| US (20)       | MACD + Sto Tuần                     | H1 total return  | all   |  20 |   0.2 |    nan   |         12.1 |         50.8 |             3.5 |           0   |     -1736.4 |
| US (20)       | MACD + Sto Tháng                    | H1 total return  | top   |   5 |   0.3 |    nan   |        407   |         76.3 |            26.9 |           0   |     -1599.2 |
| US (20)       | MACD + Sto Tháng                    | H1 total return  | all   |  17 |   0.3 |    nan   |         84.6 |        126.4 |            19.8 |           0   |     -1840.4 |
| US (20)       | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 total return  | top   |   5 |  -0.2 |    nan   |        282.5 |        106.6 |             2.1 |           0   |     -2042.7 |
| US (20)       | 2MA Tuần (MA6/10; vàng, BTC MA5/10) | H1 total return  | all   |  20 |  -0.2 |    nan   |         90.3 |         94.4 |             2.9 |           0   |     -1731.2 |
| US (20)       | 2MA Tháng (MA10/20)                 | H1 total return  | top   |   5 |  -0.2 |    nan   |       1747.3 |        324.6 |            46.3 |           0   |     -1760.4 |
| US (20)       | 2MA Tháng (MA10/20)                 | H1 total return  | all   |  17 |  -0.2 |    nan   |        112.4 |        324.6 |            78.8 |           0   |     -1714.6 |

## Cross-strategy persistence (stocks; 4 W/M strategies, each ≥ 2 trades in half 1)
| universe   |   symbols |   same_best_pct |   chance_pct |   h2_med_of_h1_best |   h2_med_mean_of_3 |   h2_beats_bh_of_h1_best |
|:-----------|----------:|----------------:|-------------:|--------------------:|-------------------:|-------------------------:|
| VN liquid  |        56 |            19.6 |           25 |                 0.8 |                9.7 |                     19.6 |
| VN all     |       180 |            23.9 |           25 |                -1.3 |                5   |                     28.9 |
| US         |        15 |            40   |           25 |               284.7 |              260.8 |                      0   |

## Caveats
Survivorship bias (only currently listed VN stocks); no limit-up/down lock-outs or slippage; monthly strategies have few trades per symbol (median ≈ 3),
so per-symbol monthly numbers are mostly noise; app-rule features for 891 stocks exist only on liquid days (step 10), so the app rule effectively has a
liquidity filter there; the US list is 20 large survivors (B&H is very hard to beat there by construction).
