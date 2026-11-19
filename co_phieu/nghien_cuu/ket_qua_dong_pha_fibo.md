# "Đồng pha" D/W/M + Fibonacci take-profit ("hồi ít thì lên nhiều"): out-of-sample backtest, 2026-11-19

Base strategy, data, sizing, benchmarks and the no-Fibo baseline are unchanged from `../bt_dong_pha/` (RESULT.md, SPEC.md).
Exact Fibo rule: `SPEC.md` (addendum F1–F5). Code: `fcore.py`, `persym_f.py`, `port_lots_f.py`, `engine_f.py`, `port_f.py`,
`ana_sym.py`, `report_f.py`, `vjc_f.py`. All tables: `tables_f.md`. Runtime about 2 minutes on 4 processes.

The target follows the app's rule (`co_phieu/dudoan/fibo.py::muc_tieu_song`, GreenView `App.fiboSong`): old wave A–B–C first;
if it is broken (C ≤ A) or too small to give a target above signal close +1 %, the **new wave** A′–B′–C′ is measured.
Checked on VJC 2025-08-15: weekly TP 177,172 (A′ 66,305 / B′ 112,149 / C′ 102,996, ×1.618), monthly 188,498, same as the app.
Sanity check: with Fibo off, the code reproduces bt_dong_pha exactly (96/96 lot sets identical; portfolio 16.9 % / 3.9 % / 1.5 %).

## Verdict (read this first)
- **The Fibo target does not create an edge. It trades big winners for a higher win rate, and the total return falls.**
- **Portfolio (VN, 1 bn VND).** TRAIN picked variant **b** (70 % at TP, 30 % on the sell signal) for both W and M.
  - TEST 2020-01 → 2026-11: **+7.1 %/yr, max DD −46 %**, against +16.9 % / −61 % without Fibo.
  - **Without HQC: +0.1 %/yr** (no Fibo: +3.9 %). Without HQC and VIC: −0.3 % (no Fibo: +1.5 %).
    HQC still made 118 % of the TEST profit (0.71 of 0.60 bn).
  - Random entries on đồng pha days with the same Fibo exits: +4.1 %/yr (5–95 %: −3.7 … +12.2); 25 % of random runs beat the real
    signal in TEST, **80 % beat it in TRAIN**.
  - Benchmarks unchanged: EW basket buy & hold +9.8 % (DD −60 %), market phase filter **+16.0 % (DD −22 %)**.
- **Per symbol (100 % capital), TEST.** The TP lowers the average trade by half or more and moves the median only slightly.
  - VN liquid: weekly 8.0 → 3.4 %/trade, monthly 16.2 → 8.0 %/trade. Median trade −3.6 → −1.6 % (W), −5.9 → −2.5 % (M).
  - Win rate 30 → 40 % (W), 24 → 34 % (M).
  - Stocks beating buy & hold: 27–28 %, the same as without Fibo. Global: 0 of 22 (BTC no longer beats it).
- **The target is far and usually not reached.** VN liquid TEST, variant b:
  - TP hit on 40 % (W) and 38 % (M) of trades.
  - Median target is +18.5 % (W) and +35 % (M) above the fill. Median time to reach it: 11 and 17 sessions.
  - Exits move only slightly closer to the top: the median exit is 17.8 % (W) and 17.4 % (M) below the highest high within ±40
    sessions, against 18.0 % / 19.0 % without Fibo.
- **The daily-wave target (side row) is worse.** It is close (+7.5 %), hit about 60 % of the time, and cuts trades to about 11 sessions.
  Portfolio daily-wave a lost −7.2 %/yr in TEST. Daily-wave b made +6.4 % (DD −41 %), or +0.7 % without HQC.
- **Ratio buckets.** The 1.618 bucket (shallow pullback) has the best average, but it hits its target least often
  (VN W 26 %, M 30 %). The average comes from trades that run past the target or never reach it.
  This is not proof that shallow pullbacks go further: 36–70 % of these trades used the new wave, which usually gives a shallow depth.
- Data caveats as before: survivorship bias, no limit-up/down lock-outs or slippage, and the last session may be incomplete.
  Nothing was run on TradingView or GreenView itself.

## Portfolio (VN, 1 bn VND, bt_dong_pha chosen settings: W "either" signal 8 %/N10, M MACD+Sto 20 %/N5, exit a)
| Fibo variant | TRAIN CAGR | **TEST CAGR** | TEST maxDD | TEST w/o HQC | TEST w/o HQC+VIC | TEST trades | win | random TEST mean (5–95 %) | random ≥ real |
|---|---|---|---|---|---|---|---|---|---|
| c: no Fibo (bt_dong_pha) | +6.3 % | **+16.9 %** | −61 % | +3.9 % (DD −41 %) | +1.5 % | 303 | 25 % | +6.5 (−2.9…+17.8) | 10 % |
| a: all at TP | +1.6 % | +2.0 % | −48 % | +1.3 % (DD −48 %) | +1.9 % | 542 | 39 % | +3.1 (−1.2…+8.1) | 70 % |
| **b: 70 % at TP (chosen on TRAIN)** | +3.4 % | **+7.1 %** | **−46 %** | **+0.1 %** (DD −38 %) | −0.3 % | 296 | 30 % | +4.1 (−3.7…+12.2) | 25 % |
| daily wave, a (side row) | +2.6 % | −7.2 % | −67 % | −7.2 % | −7.4 % | 984 | 49 % | | |
| daily wave, b (side row) | +5.1 % | +6.4 % | −41 % | +0.7 % (DD −29 %) | +0.4 % | 318 | 39 % | | |
| EW liquid basket buy & hold | −7.4 % | +9.8 % | −60 % | | | | | | |
| market phase filter (bt_chuky) | +15.0 % | +16.0 % | −22 % | | | | | | |

- **a/b choice on TRAIN, per type (CAGR/vol):** W: a 0.47 vs b 0.49 → b. M: a −0.19 vs b 0.40 → b.
- **Per type, TEST CAGR:**

  | type | no Fibo | a | b | daily wave b |
  |---|---|---|---|---|
  | W | +4.2 % | +2.9 % | +1.4 % | +1.1 % |
  | M | +11.1 % | +2.2 % | −0.3 % | +6.8 % |

  With b, random W is +1.5 % (55 % of runs ≥ real) and random M +3.7 % (75 % ≥ real).
  The combined W+M (+7.1 %) is above both parts because of how cash is shared in one account and how HQC was sized there. It is not a robust gain.
- **Full period 2008 → 2026-11, W+M:** no Fibo +7.0 %/yr (DD −53 %); a +1.4 %; b +3.9 % (DD −47 %); daily-wave b +5.4 % (DD −43 %).
- **Per year:** Fibo helps in falling years (2022: −33 % → −15 %), but it gives up the big years (2013 +43 → +17 %, 2017 +61 → +23 %,
  2025 +28 → 0 %). See `tables_f.md`.
- **Inside the portfolio** (TEST, variant b): every trade had a target. Hit rate was 34 % (W) and 29 % (M).
  The median target was +21 % (W) and +27 % (M) above the fill. Wave used: old 180 / new 68 (W), old 33 / new 15 (M).

## Per symbol (standalone, 100 % capital; VN: 2MA entry, exit b; global: "either" entry, exit b, as chosen in bt_dong_pha)
TRAIN = entries before 2020 (global: first half of bars), TEST = 2020+ (second half). The a/b choice on TRAIN average per trade was **b** in all 4 cases.

**VN liquid (292 stocks), TEST:**
| type | Fibo | trades | avg %/trade | median | win | % stocks beating B&H | TP hit | median TP distance | median sessions to TP | exit below top ±40 (median) | median hold |
|---|---|---|---|---|---|---|---|---|---|---|---|
| W | none | 725 | **8.0** | −3.6 | 30 % | 28 % | – | – | – | 18.0 % | 41 |
| W | a | 847 | 1.6 | −1.6 | 43 % | 26 % | 43 % | +18.3 % | 13 | 16.3 % | 18 |
| W | **b** | 761 | **3.4** | −1.6 | 40 % | 27 % | 40 % | +18.5 % | 11 | 17.8 % | 34 |
| W | daily wave b | 767 | 2.3 | −0.5 | 44 % | 25 % | 55 % | +7.6 % | 4 | 16.6 % | 33 |
| M | none | 566 | **16.2** | −5.9 | 24 % | 28 % | – | – | – | 19.0 % | 57 |
| M | a | 781 | 4.5 | −2.4 | 41 % | 26 % | 40 % | +34.4 % | 18 | 17.3 % | 22 |
| M | **b** | 595 | **8.0** | −2.5 | 34 % | 28 % | 38 % | +35.4 % | 17 | 17.4 % | 54 |
| M | daily wave b | 603 | 4.1 | −0.7 | 42 % | 25 % | 60 % | +7.6 % | 5 | 17.6 % | 55 |

Buy & hold median TEST CAGR = +10.0 %. The median stock's strategy CAGR is about 0 % for every variant.

**Gold, BTC, 20 US, second half:**
| type | Fibo | avg %/trade | win | symbols beating B&H | TP hit | median TP distance |
|---|---|---|---|---|---|---|
| W | none | 4.7 | 38 % | 1/22 (BTC) | – | – |
| W | b | 2.3 | 43 % | 0/22 | 34 % | +12.1 % |
| M | none | 27.5 | 32 % | 1/22 (BTC) | – | – |
| M | b | 10.2 | 41 % | 0/22 | 36 % | +19.1 % |

**Random control, 10 seeds** (same đồng pha days, stops, confirmation, Fibo and sell exits), TEST average per trade:

| group | type | Fibo | real | random | random seeds ≥ real |
|---|---|---|---|---|---|
| VN | W | none | 8.0 | 5.6 | 0/10 |
| VN | W | b | 3.4 | 2.7 | 1/10 |
| VN | M | none | 16.2 | 12.9 | 1/10 |
| VN | M | b | 8.0 | 7.6 | 3/10 |
| Global | W | b | 2.3 | 2.7 | 8/10 |
| Global | M | b | 10.2 | 10.8 | 7/10 |

- % of VN stocks beating B&H with b: real 27–28 %, random 26 %.
- As in bt_dong_pha, the small VN edge of the real weekly signal over random sits in a few outliers. The Fibo target cuts those outliers.

## Fibo-specific
**Ratio buckets** (initial ratio from the pullback depth; variant b, all periods, `n` = trades):

| group | type | ratio | n (TEST) | TEST avg | TEST median | TP hit | median TP distance | median sessions to TP | new wave |
|---|---|---|---|---|---|---|---|---|---|
| VN | W | 1.0 | 361 (196) | +1.2 | −0.6 | 61 % | +5.8 % | 4 | 5 % |
| VN | W | 1.272 | 505 (281) | +1.9 | −2.1 | 40 % | +17.4 % | 12 | 8 % |
| VN | W | 1.618 | 464 (284) | +6.4 | −2.2 | 26 % | +36.8 % | 34 | 36 % |
| VN | M | 1.0 | 309 (147) | +6.3 | −1.2 | 51 % | +12.5 % | 8 | 10 % |
| VN | M | 1.272 | 391 (218) | +5.6 | −2.2 | 40 % | +29.0 % | 19 | 16 % |
| VN | M | 1.618 | 370 (230) | +11.4 | −4.3 | 30 % | +63.4 % | 50 | 70 % |

- The step-up rule often raises the ratio, because đồng pha entries come late, far above the measured wave.
- Global shows the same pattern: 1.0 hits 49–62 % with a +3 to +7 % target; 1.618 hits 21–24 % with a +23 to +48 % target.

**Old vs new wave** (variant b, all periods; all trades had a target):

| group | type | old wave | new wave | avg %/trade old / new | TP hit old / new |
|---|---|---|---|---|---|
| VN liquid | W | 1,108 | 222 (17 %) | +3.0 / +7.6 | 42 % / 36 % |
| VN liquid | M | 716 | 354 (33 %) | +6.1 / +15.9 | 42 % / 33 % |
| global | W | 521 | 132 (20 %) | +2.3 / +5.1 | 40 % / 23 % |
| global | M | 289 | 101 (26 %) | +19.8 / +11.6 | 41 % / 25 % |

The new-wave targets are far: median +27 % (W) and +62 % (M) in VN.

## Worked example: VJC 2025–2026 (bottom 59.3k on 2025-04-09, top 169.2k on 2025-11-26)
- The only daily signal inside an aligned window was MACD+Sto on 2025-08-15 (close 112.0k).
  The chosen per-symbol VN variant (2MA) again took no trade.
- **Weekly wave:** the old wave was too small, so the new wave was used: A′ 66.3k, B′ 112.1k, C′ 103.0k, depth 20 %, ×1.618.
  **TP = 177.2k** (+58 %).
- **Monthly wave:** new wave, A′ 59.3k (the April bottom), B′ 112.1k, C′ 103.0k, depth 17 %, ×1.618. **TP = 188.5k** (+68 %).
- Both targets sit above the actual top of 169.2k. Neither was reached, so the trades are the same as without Fibo:
  - Lệnh tuần (MACD+Sto, exit a): entry 2025-08-18 at 112.0k, sold 2025-09-22 at 105.0k (−2 % on capital).
  - Lệnh tháng: still held at 137.2k.
  - The weekly target was 4.7 % above the top. A target from the old wave would have been tiny (B 71k), which is why the step-up and new-wave rules exist.
- **Daily wave (side row):** A 88.5k, B 101.5k, C 93.5k, depth 62 %, stepped up to ×1.618 → TP 114.5k. It was hit at the gap
  open the next day (116.8k): +4 % on the position, with 92 % of the later move to 169k left on the table.

## Files
- `dong_pha_fibo_tung_ma.xlsx`:
  - "Tổng hợp": every variant, VN and global.
  - "Lệnh tuần" / "Lệnh tháng": per symbol, chosen variant b, with "Số lệnh có mục tiêu Fibo", "Số lệnh chạm Fibo" and the no-Fibo total for comparison.
  - "Danh sách lệnh": 3,443 trades, VN liquid + global. Columns include **'Chốt Fibo (giá)', 'Tỉ lệ Fibo', 'Chạm Fibo'**, plus
    'Sóng đo' (cũ/mới), 'Độ sâu hồi %', 'Số phiên đến Fibo' and 'Bán thấp hơn đỉnh ±40 phiên %'.
- `ket_qua_dong_pha_fibo.json`: same format as `ket_qua_dong_pha.json`, with keys `dong_pha_fibo_w` and `dong_pha_fibo_m`, plus `cham_fibo` and `co_fibo`.
- `tables_f.md`: every table, including the per-year returns and the portfolio random control per type.
