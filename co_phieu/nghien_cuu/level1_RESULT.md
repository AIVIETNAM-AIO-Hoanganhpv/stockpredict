# LEVEL 1 trading method (MA pairs, position + confirmation orders, stop-money sizing) – out-of-sample backtest, 2026-11-19

## Verdict (read this first)
- **LEVEL 1 as written does not beat buy & hold in TEST.** Settings were chosen on TRAIN 2008–2019 only. The D, W and M parts run together in one
  1-billion-VND account: **TEST 2020-01 → 2026-11: +6.7 %/yr, total +56 %, max DD −35 %**. Over the same period, the equal-weight liquid basket
  (buy & hold) made **+9.9 %/yr (DD −60 %)** and the bt_chuky market-phase filter made **+16.0 %/yr (DD −22 %)**.
  It does beat the app rule (−3.0 %/yr) and the W/M R:R strategy (−1.3 %/yr).
- **Each timeframe alone makes only +2.6 to +5.2 %/yr in TEST.** The "textbook default" was fixed before any run
  (adaptive MA pair, sell 50 % on a close below the condition MA, VNINDEX-proxy filter, leg scaling, low stop money, 5 names).
  It made **+0.5 %/yr combined in TEST** (D −0.5 %, W +5.4 %, M −2.7 %).
- **The signals have no per-trade edge on D and W.** Average R per trade in TEST: D −0.06 R, W −0.09 R, with win rates of 25–28 %.
  Only M has a positive average (+0.66 R), but that comes from 43 trades and a few big winners, so it is not statistically meaningful.
- **The settings do not carry over from TRAIN to TEST.** TRAIN-vs-TEST rank correlation (Sharpe-like) across variants: D 0.20, W −0.13, M 0.07.
  Median TEST CAGR of all variants: D +1.1 %, W +1.6 %, M +5.5 %. Only 4–8 % of the 1,584 variants beat the basket's +9.9 % in TEST.
- **Why the returns are low:**
  - Sizing by stop money keeps the account mostly in cash. Exposure is 33 % per TF and 78 % combined.
  - W and M stops are very wide. The median distance to the stop is 18 % on W and 37 % on M, so positions are small.
  - D trades last a median of only 15 calendar days, not the 1–3 months the text expects, because the MA6/MA10 or MA10/MA20 cross-down comes quickly.
  - Diagnostic: with the same signals but equal-value sizing (no stop-money rule), TEST gives +11.3 %/yr combined but DD −44 %.
    That is about the basket's return with similar risk, so there is still no edge.
- **Patterns that look good but are biased:**
  - Episodes with a confirmation order average about +0.3 R, against about −0.8 R without one. This is selection: a confirmation is only
    bought after the position order is already in profit.
  - The leg-scaling rule (leg 2 = 100 %, legs 3–4 smaller) is not supported. In TEST, D leg 2 averaged −0.29 R and D leg 1 +0.09 R.
- **Data caveats:**
  - Survivorship bias (delisted stocks are missing) flatters every number here, the benchmarks included.
  - There is no real VNINDEX in the data. "Đồng pha với VNINDEX" uses the equal-weight liquid index.
  - Limit-up/limit-down lock-outs and slippage are not modelled.

## Setup
- Data: `features_full.pkl` → `bt_chuky/base.pkl` (891 stocks, daily adjusted OHLC, 2006-06 → 2026-11-19; the last session is only partly filled).
  Liquidity: 20-day traded value ≥ 1 bn VND at the signal bar.
- Bars: D = daily. W = W-FRI weeks. M = calendar months, built per stock from its own sessions. A W/M bar is used only once it is complete
  (signal at the close of the last session of the week or month).
- Execution: signal at the bar close, fill at the **next daily open**. Stops are checked on daily lows, with fill = min(open, stop).
  Exits on a timeframe signal fill at the next daily open. Fees: buy 0.15 %, sell 0.15 % + 0.1 % tax. Lots of 100 shares. Cash only (no margin).
- Capital: 1,000,000,000 VND. Stop money = risk % × equity (previous close) ÷ N names × leg factor; position order 30 %, confirmation 70 %.
  `shares = floor(money / (signal close − stop) / 100) × 100`, capped by cash. One episode per stock per TF. At most N live stocks per TF.
  Same-day signals are ranked by traded value.
- Split: chosen on **TRAIN 2008-01 → 2019-12** by Sharpe-like (CAGR / annual volatility, ≥ 30 trades). **TEST 2020-01 → 2026-11** run once,
  with fresh capital. Combined portfolio = the three per-TF TRAIN winners in one account.
- Grid (1,584 variants):
  - MA pair: adaptive (MA10/MA20 if the 20-bar mean |close − MA10| ≤ train-median × ATR14, else MA6/MA10), fixed 6/10, or fixed 10/20.
  - Exit: sell 50 % or 70 % on the first close below the condition MA; or hold everything until the cross-down
    (BÍ KÍP 1 "experienced"); or BÍ KÍP 3 (W and M only).
  - Market filter: none, phase risk-on (bt_chuky), or EW index MA10 > MA20 on the trade TF.
  - GĐ2 probe (trades against the bigger TF after ≥ 2 down legs, 30 % zone): off or on.
  - Leg scaling: on or off.
  - Stop money: low or high (D 5/8 %, W 8/12 %, M 12/20 %).
  - N: 5 or 10.

## Chosen variants (TRAIN only)
| TF | MA pair | exit | market filter | GĐ2 probe | leg scaling | stop money | N |
|---|---|---|---|---|---|---|---|
| D | adaptive | hold until MA cross-down (no partial) | EW index D MA10>MA20 | off | on | 5 % | 10 |
| W | MA6/MA10 | BÍ KÍP 3 (D close < D MA10 after ≥3 D pullbacks → keep 30 %; W close < MA6 → keep 50 %; W close < MA10 → 0) | none (bigger-TF M filter still applies) | on | off | 12 % | 10 |
| M | MA10/MA20 | hold until MA cross-down | none | n/a | on | 12 % | 10 |

## Main results
| strategy | TRAIN CAGR | TRAIN DD | **TEST CAGR** | TEST total | **TEST DD** | TEST trades | TEST win | TEST avg R | TEST median R | TEST hold (bars, mean/med) | TEST exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **LEVEL 1 chosen D+W+M (one account)** | +7.1 % | −25 % | **+6.7 %** | +56 % | **−35 %** | 1,239 | 27 % | −0.04 | −0.33 | 32 / 13 | 78 % |
| chosen D | +4.7 % | −14 % | +4.0 % | +31 % | −16 % | 731 | 28 % | −0.06 | −0.54 | 14 / 10 | 33 % |
| chosen W | +3.7 % | −16 % | +2.6 % | +20 % | −20 % | 509 | 25 % | −0.09 | −0.21 | 29 / 22 | 34 % |
| chosen M | +3.2 % | −12 % | +5.2 % | +41 % | −25 % | 43 | 35 % | +0.66 | −0.24 | 349 / 271 | 34 % |
| textbook default D+W+M | +3.8 % | −26 % | +0.5 % | +4 % | −41 % | 493 | 25 % | −0.08 | −0.47 | 32 / 13 | 59 % |
| textbook default D | +3.5 % | −15 % | −0.5 % | −4 % | −25 % | 383 | 25 % | −0.10 | −0.48 | 14 / 10 | 27 % |
| textbook default W | −0.1 % | −12 % | +5.4 % | +44 % | −14 % | 83 | 30 % | +0.14 | −0.41 | 64 / 44 | 29 % |
| textbook default M | +1.7 % | −15 % | −2.7 % | −17 % | −20 % | 30 | 17 % | −0.54 | −0.71 | 184 / 181 | 13 % |
| diag: chosen signals, equal-value sizing D+W+M | +7.4 % | −39 % | +11.3 % | +109 % | −44 % | 1,144 | 29 % | +0.05 | −0.28 | 33 / 13 | 87 % |
| EW liquid basket buy & hold | −7.5 % | −79 % | **+9.9 %** | +91 % | −60 % | | | | | | 100 % |
| phase filter + basket (bt_chuky) | +15.0 % | −33 % | **+16.0 %** | +177 % | −22 % | | | | | | 51 % |
| app rule (bt_vn) | −2.1 % | −40 % | −3.0 % | −19 % | −58 % | | | | | | 75 % |
| W/M R:R strategy (bt_vn) | +15.0 % | −21 % | −1.3 % | −8.5 % | −43 % | | | | | | 84 % |

Hold is in trading bars (days). Median calendar hold: D 15 days, W 35 days, M 398 days. The text expects D 1–3 months, W 3–9 months, M 1–2 years.
Only M lands in the expected range.
R = net P&L of the episode (both orders, fees included) ÷ planned risk money (shares × (fill − stop)).

### Per-year returns, TEST (fresh capital 2020; 2026 = to 19 Nov)
| year | chosen D | chosen W | chosen M | **chosen D+W+M** | default D+W+M | EW buy & hold | phase filter |
|---|---|---|---|---|---|---|---|
| 2020 | +23.4 % | +0.1 % | +16.8 % | +28.3 % | +31.8 % | +41.3 % | +35.5 % |
| 2021 | +12.5 % | +30.7 % | +33.9 % | +47.9 % | +23.3 % | +100.7 % | +58.3 % |
| 2022 | −10.9 % | −12.6 % | −19.9 % | −32.2 % | −16.2 % | −50.0 % | +7.8 % |
| 2023 | +8.7 % | −4.2 % | +3.0 % | +6.9 % | −0.7 % | +31.4 % | +7.0 % |
| 2024 | −1.6 % | +11.6 % | +10.2 % | +15.4 % | +6.5 % | +8.1 % | +7.7 % |
| 2025 | +10.3 % | +5.1 % | −0.5 % | +11.3 % | −16.2 % | +13.4 % | +20.0 % |
| 2026 | −10.1 % | −6.9 % | −0.2 % | −11.5 % | −14.1 % | −16.3 % | −13.4 % |

### Per-year returns, FULL continuous run (mostly in-sample)
| year | chosen D+W+M | default D+W+M | EW buy & hold |
|---|---|---|---|
| 2008 | −0.2 % | 0.0 % | −68.6 % |
| 2009 | −0.7 % | −2.5 % | +81.3 % |
| 2010 | +3.0 % | −12.9 % | −18.2 % |
| 2011 | −4.7 % | −0.3 % | −52.8 % |
| 2012 | +0.4 % | −3.1 % | +16.0 % |
| 2013 | +3.5 % | +7.2 % | +13.0 % |
| 2014 | +33.6 % | +28.1 % | +24.1 % |
| 2015 | +7.8 % | +7.7 % | −4.6 % |
| 2016 | +6.6 % | +5.3 % | −2.6 % |
| 2017 | +37.7 % | +27.7 % | +31.2 % |
| 2018 | −7.3 % | −9.1 % | −10.2 % |
| 2019 | +15.5 % | +5.8 % | +1.0 % |
| 2020–2026 | see TEST (FULL: +28.1, +65.9, −33.2, +5.4, +14.8, +2.0, −10.5 %) | | |

The method's main merit is avoiding the 2008 and 2011 crashes: it was mostly flat in bad years. It loses most of the strong up-years
(2009, 2021, 2023) and still fell −32 % in 2022, where the phase filter made +7.8 %.

## Grid robustness (TEST CAGR across all variants)
| TF | variants | min | 25 % | median | 75 % | max | share > 0 | share > basket +9.9 % | Spearman TRAIN↔TEST |
|---|---|---|---|---|---|---|---|---|---|
| D | 432 | −9.6 % | −0.9 % | +1.1 % | +3.5 % | +19.0 % | 64 % | 3.9 % | 0.20 |
| W | 576 | −5.8 % | −0.3 % | +1.6 % | +4.9 % | +20.0 % | 71 % | 8.0 % | −0.13 |
| M | 576 | −6.5 % | +2.5 % | +5.5 % | +7.6 % | +17.6 % | 90 % | 7.6 % | 0.07 |

Median TEST CAGR by choice (all other settings pooled):
- **MA pair:**
  - D: 10/20 +3.3 %, adaptive +1.2 %, 6/10 −0.1 %.
  - W: 6/10 +3.2 %, adaptive +0.9 %, 10/20 +0.3 %.
  - M: 10/20 +6.1 %.
- **Exit:**
  - D: hold-to-cross +2.7 %, sell 50 % +0.9 %, sell 70 % 0.0 %.
  - W: hold, 50 % and 70 % about +2.5 %; BÍ KÍP 3 +0.5 %.
- **Market filter:**
  - D: phase +2.4 %, idx +1.8 %, none −0.9 %.
  - W: idx +6.4 %, none +1.3 %, phase 0.0 %.
  - M: phase +7.6 %, none +5.6 %, idx +1.9 %.
  - The filters disagree between timeframes and between TRAIN and TEST.
- **GĐ2 probe, leg scaling, stop-money level:** each changes the median by less than 1 %/yr. N = 10 is slightly better than 5.

## Trade breakdown (TEST, chosen variants)
| TF | leg 1 | leg 2 | leg 3 | leg 4 | leg ≥5 | with confirmation | without |
|---|---|---|---|---|---|---|---|
| D avg R (n) | +0.09 (261) | −0.29 (211) | −0.30 (114) | +0.08 (64) | +0.24 (81) | +0.31 (489) | −0.83 (242) |
| W avg R (n) | −0.05 (238) | −0.17 (105) | −0.19 (68) | −0.10 (48) | +0.05 (50) | +0.21 (248) | −0.37 (261) |
| M avg R (n) | +1.34 (26) | −0.49 (9) | −0.11 (1) | −0.40 (4) | −0.11 (3) | +1.25 (29) | −0.57 (14) |
Leg 2 (sized 100 %) is not better than the other legs. The "with confirmation" split is biased by construction (see verdict).

## Current signals (`now.json`, as of 2026-11-19)
- Market: the phase filter is **risk-off**, and the EW index has MA10 < MA20 on D, W and M. The chosen D rule requires the index filter,
  so there are **no D entries now**.
  - On the last, partly filled session there were 0 new D position signals and 1 D confirmation signal (LSG).
- **W** (last completed week 2026-11-13): 21 position signals, of which **7 pass** the chosen W rules (liquid + bigger-TF M up, or a GĐ2 probe),
  including BAF, DXG and HDC. There are also 11 confirmation signals.
- **M** (last completed month 2026-10): 7 position signals: CAR, FMC, HIO, MVN, SAS, TDP and VEA.
  Some have huge stop distances; CAR's planned risk is 85 %, which suggests a data problem.
- `now.json` gives the entry reference, stop, leg, filters and share counts for a 1-billion-VND account (empty account, N = 10).
  - W/M positions are small (for example BAF: 1,500 shares, about 46 M VND) because the stops are wide.
  - It also lists open setups (entered, not yet exited) that passed the entry filters.
  - These are not recommendations: the backtest shows no edge over buy & hold.

## Files
- `SPEC.md` – exact rules. `sig.py` – signal/lot precompute. `engine.py` – portfolio engine. `grid.py` → `grid.pkl` (1,584 variants, TRAIN and TEST metrics).
- `final.py` → `final.pkl`, `equity_{chosen,default}_{D,W,M,DWM}_{test,full}.csv`, `trades_chosen_*_test.csv`. `now.py` → `now.json`.
- Benchmarks are read from `bt_chuky/equity_bh_ew_basket_*.csv` and `bt_chuky/equity_regime_basket_*.csv`. App rule and W/M numbers come from `bt_vn/RESULT.md`.
