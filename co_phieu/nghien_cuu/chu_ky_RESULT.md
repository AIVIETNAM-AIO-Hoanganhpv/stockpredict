# Cycle trading for Vietnamese stocks – out-of-sample portfolio backtest (2026-11-19)

## Verdict (read this first)
- **Market-phase filter (approach 1) works in TEST, mainly as risk control.** The chosen variant (picked on 2008–2019 only, best of 1,728)
  holds the equal-weight liquid basket only in Uptrend/Accumulation phases: **TEST 2020-01 → 2026-11: +16.0 %/yr, max DD −22 %**,
  vs equal-weight basket buy & hold **+9.9 %/yr, max DD −60 %**. It is in the market 51 % of the time.
  Robustness: of 576 basket variants, 68 % beat buy & hold in TEST (median +11.3 %/yr, median DD −24 %).
- **Best combination: phase filter + sector rotation (top 2 ICB sectors): TEST +19.5 %/yr, max DD −23 %** (TRAIN +18.3 %).
  But the gain over the plain phase filter is **not reliable**: the median of the 81 phase-filtered sector variants is +14.3 %/yr (below +16.0 %).
- **Sector rotation alone does not beat buy & hold** (TEST +6.2 %/yr, DD −64 %).
- **Per-stock price cycles (approach 3) do not exist in a usable form.** A stock's own past cycle length predicts its next swing low
  no better than a random cycle length taken from another stock, and worse than one constant. Cycle-window buying lost money in TEST (−3.6 %/yr).
- **Take-profit rules (amplitude, Fibonacci, timing, Stochastic, MACD, scale-out): none beat the simple default exit** (hold until the market
  turns risk-off, with an initial stop) when chosen on TRAIN. All exits sell 13–18 % below the real local top (median), whatever the rule.
- Fragility (be careful): the edge needs fast execution. With a **1-day delay** the phase-basket TEST CAGR falls from 16.0 % to 11.9 %;
  with **+0.2 % extra cost per side** to 11.5 %. The filter flips ~17 times a year (turnover ~10× equity per year).
  Part of the edge is short-term autocorrelation of an equal-weight index of many small stocks, which is hard to capture in real trading.
- **Long-term (hold 6–24 months):** the best rule was month-end buying of top-2-sector stocks while the market is risk-on, selling on a monthly close below the 10-month SMA or after 12 months. TEST +14.7 %/yr, max DD −30 %. That beats buy & hold but not the short-term phase filter. Fixed long holds with only a wide stop failed in TRAIN. With only 3–14 non-overlapping periods in TEST, horizon differences are not significant (see the long-term section).
- Compared with previous strategies on the same TEST period: app rule −3.0 %/yr, W/M strategy −1.3 %/yr (from `bt_vn/RESULT.md`).

## Setup
- Data: `features_full.pkl` via `bt_vn/prep.pkl`: 891 stocks, daily adjusted OHLC, no volume. **Survivorship bias** (delisted stocks missing)
  makes all numbers, benchmarks included, optimistic. Dates before 2010 are approximate; days with less than half the usual number of
  priced stocks were dropped (bad rebuilt dates). Data end 2026-11-19 (the last 2 sessions are partly filled).
- Liquidity: 20-day traded value ≥ 1e9 VND (tool rows, 10-bar validity). Liquid stocks per year: 15 (2008) → 149 (2019) → ~330 (2021–2025).
- Execution: signals at close t, trade at **open t+1**. Fees buy 0.15 %, sell 0.15 % + 0.1 % tax. Capital 1,000,000,000 VND, equal weight among
  holdings, max 20 % per stock, cash otherwise (no interest on cash). No ceiling/floor lock, no slippage, no lot rounding.
- Macro: Yahoo `^TNX`, `^IRX`, `USDVND=X`, `DX-Y.NYB`; month-end values used from the next month. **Vietnamese interest-rate history was not
  reachable here**; VND 3-month change and US 10y yield change were used as proxies. The US 10y filter helped a little in TRAIN and was kept;
  the VND filter did not help.
- Split: all choices on **TRAIN 2008-01 → 2019-12** (selection metric = Sharpe-like = CAGR / annual stdev). **TEST 2020-01 → 2026-11** was run with
  fresh capital. FULL = one run 2008 → 2026 (mostly in-sample).
- Benchmark: equal-weight basket of all liquid stocks, bought at the first open of each year, held to year end (fees paid): TEST +9.9 %/yr
  (the earlier `bt_vn` run, with execution at close and slightly different dates, gave +8.5 %).

## Main results
| strategy | TRAIN CAGR | TRAIN DD | **TEST CAGR** | TEST total | **TEST max DD** | TEST Sharpe-like | TEST in market | TEST turnover/yr | FULL CAGR |
|---|---|---|---|---|---|---|---|---|---|
| **A1+A2 phase filter + top-2 sectors** | +18.3 % | −30 % | **+19.5 %** | +241 % | **−23 %** | 1.13 | 51 % | 12.8× | +18.8 % |
| **A1 phase filter + liquid basket** | +15.0 % | −33 % | **+16.0 %** | +177 % | **−22 %** | 1.27 | 51 % | 10.0× | +15.4 % |
| A1 phase filter + stock entries (higher swing low > MA50), exit on risk-off | +13.9 % | −18 % | +14.2 % | +150 % | −23 % | 0.92 | 49 % | 9.4× | +14.0 % |
| A1 phase filter + top-20 momentum stocks | +12.1 % | −33 % | +6.4 % | +53 % | −24 % | 0.39 | 51 % | 11.4× | +10.0 % |
| A2 sector rotation, no phase filter | +3.6 % | −70 % | +6.2 % | +51 % | −64 % | 0.22 | 100 % | 8.5× | +4.5 % |
| A3 cycle stocks, standalone (best TRAIN) | +8.9 % | −41 % | −3.6 % | −23 % | −67 % | −0.18 | 71 % | 10.2× | +4.1 % |
| A1+A2+A3 cycle stocks gated by phase + sector (best TRAIN Sharpe) | +1.9 % | −3 % | +1.5 % | +11 % | −6 % | 0.36 | 5 % | 1.5× | +1.7 % |
| EW liquid basket buy & hold (yearly) | −7.5 % | −79 % | **+9.9 %** | +91 % | −60 % | 0.44 | 100 % | 0.4× | −1.5 % |
| previous: W/M strategy (bt_vn) | +15.0 % | −21 % | −1.3 % | −8.5 % | −43 % | | 84 % | | |
| previous: app rule (bt_vn) | −2.1 % | −40 % | −3.0 % | −19 % | −58 % | | 75 % | | |

### Per-year returns (TEST runs, fresh capital 2020; 2026 = to 19 Nov)
| year | phase + sectors | phase + basket | phase + stock entries | sectors only | cycle stocks | EW buy & hold |
|---|---|---|---|---|---|---|
| 2020 | +27.0 % | +35.5 % | +79.9 % | +34.2 % | +39.8 % | +41.3 % |
| 2021 | +62.7 % | +58.3 % | +38.9 % | +123.3 % | +53.2 % | +100.7 % |
| 2022 | −1.8 % | +7.8 % | +3.7 % | −55.5 % | −45.9 % | −50.0 % |
| 2023 | +5.8 % | +7.0 % | −6.5 % | −2.5 % | −1.5 % | +31.4 % |
| 2024 | +26.4 % | +7.7 % | +3.5 % | +19.8 % | +4.5 % | +8.1 % |
| 2025 | +23.3 % | +20.0 % | +18.9 % | +10.9 % | −8.4 % | +13.4 % |
| 2026 | +1.9 % | −13.4 % | −16.3 % | −12.8 % | −29.0 % | −16.3 % |
Most of the edge comes from **2022** (avoided most of the −50 % crash). The filter lags in strong rebounds (2021, 2023).

### Per-year returns (FULL continuous run, mostly in-sample)
| year | phase + sectors | phase + basket | EW buy & hold |
|---|---|---|---|
| 2008 | −28.9 % | +8.8 % | −68.6 % |
| 2009 | +105.2 % | +100.0 % | +81.3 % |
| 2010 | +23.9 % | +18.7 % | −18.2 % |
| 2011 | −8.3 % | −10.4 % | −52.8 % |
| 2012 | +33.1 % | +40.9 % | +16.0 % |
| 2013 | +50.9 % | +21.6 % | +13.0 % |
| 2014 | +54.7 % | +38.7 % | +24.1 % |
| 2015 | +4.8 % | −7.8 % | −4.6 % |
| 2016 | +5.5 % | −11.9 % | −2.6 % |
| 2017 | +8.2 % | +16.9 % | +31.2 % |
| 2018 | +14.3 % | +1.6 % | −10.2 % |
| 2019 | +7.0 % | +0.9 % | +1.0 % |

## Approach 1 – market phase (regime)
Index = equal-weight index of liquid stocks (an all-stocks version was also tested). Phase rules: see SPEC.md.
Grid (1,728): universe {all, liquid} × MA pair {50/200, 20/100, 50/150} × breadth threshold {40, 50, 60 %} × risk-on set
{Up; Up+Acc-late; Up+Acc-late+Acc; Up+Acc-late+Distribution} × confirmation {1, 5 days} × macro {none, VND, US10y, both} × holding {basket, top-10, top-20 momentum}.
- Chosen: liquid index, MA20/MA100, breadth ≥ 60 %, risk-on = Uptrend + Accumulation-late + Accumulation, US10y filter, liquid basket.
- TRAIN rank vs TEST rank: Spearman 0.31. Grid median TEST +4.9 %/yr overall, but **+11.3 %/yr for basket holdings** (momentum top-10: −0.6 %).
- Holding top-momentum stocks instead of the basket was worse in TEST. Confirmation delay (5 days) was worse. The VND filter was worse; US10y helped a bit.
- Next-day return of the index by phase (annualised): TEST Uptrend +49 %, Accumulation +30 %, Acc-late +16 %, Distribution −20 %, Downtrend −32 %
  (TRAIN: +44 / +52 / +137 / −50 / −63 %). Median phase length is only 5–8 days.

## Approach 2 – sector rotation
Grid (162): top-k {2, 3, 5} × lookback {21, 63, 126 days} × score {return, breadth, rank-sum} × stocks {all liquid in sector, top-3, top-5 by 3-month return} × {no filter, phase filter}.
- Without the phase filter: best TRAIN pick TEST −7.5 %/yr; median TEST +5.3 %/yr, median DD −63 %. **No better than buy & hold.**
- With the phase filter: chosen (top-2, 63 days, rank-sum, all stocks) TEST +19.5 %; median of the 81 filtered variants +14.3 % (range +7.5 to +23 %),
  so the sector layer adds about nothing on average over the phase-filtered basket (+16.0 %). Spearman TRAIN vs TEST within filtered variants 0.49.
- Turnover is high (12.8× per year), fees are included.

## Approach 3 – single-stock price cycles
Cycle T = median distance between the last 6 confirmed swing lows (pivot k = 5 or 10 bars, confirmed k bars later).
### Does the predicted next low beat random timing? (liquid stocks, all confirmed lows)
| pivot k | period | lows | median gap (bars) | median error, own T | error, shuffled T (random stock) | error, one constant | hit ±20 % own | hit shuffled | hit constant | corr(T, actual gap) | top error: low+T/2 | top error: shuffled | top error: constant |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | TRAIN | 16,834 | 14.0 | 5.5 | 5.5 | 5.0 | 28.7 % | 29.0 % | 27.7 % | 0.01 | 3.5 | 3.75 | 3.0 |
| 5 | TEST | 32,328 | 14.5 | 5.5 | 5.5 | 5.0 | 28.5 % | 28.9 % | 27.2 % | 0.03 | 3.75 | 3.75 | 3.0 |
| 10 | TRAIN | 8,063 | 28.0 | 10.5 | 10.5 | 9.0 | 29.2 % | 29.2 % | 33.5 % | −0.01 | 7.25 | 7.0 | 6.5 |
| 10 | TEST | 16,131 | 28.0 | 10.5 | 11.0 | 9.0 | 28.6 % | 28.4 % | 32.2 % | 0.03 | 7.25 | 7.25 | 6.5 |
**The stock-specific cycle carries no information** (correlation ≈ 0; same error as a random stock's cycle; a constant is better).
The same holds for the expected top (low + T/2) and the median past up-wave duration.

Entry in the window vs outside (same trigger, 4·ATR trailing exit, avg net return per trade, TEST): in-window |z−1| ≤ 0.3: +1.4 % (k=5) / +1.1 % (k=10);
early z < 0.7: +2.3 % / +1.9 %; late z > 1.3: +1.0 % / +1.9 %. No advantage for the window.

Portfolio grid (256): k {5, 10} × window ±{15, 30 %} × dispersion filter {none, IQR/T ≤ 0.5} × exit {low + 0.5/0.75/1.0·T, 4·ATR trail} × 5 or 10 slots ×
gate {none, phase, sector, phase+sector}. Standalone best TRAIN pick: TEST −3.6 %/yr (DD −67 %); standalone median TEST −0.7 %.
With phase gating the median is +5.1 %, i.e. the phase filter, not the cycle, does the work.

## Exit (take-profit) study
Same entries for every exit rule; initial stop = entry swing low − 0.5·ATR in all rules (except the Fib-stop variants); max hold 250 bars.
Entries: **"phase risk-on + stock buy"** = liquid stock, 3-bar swing low just confirmed and higher than the previous one, close up, close > SMA50,
market risk-on, valid A→B→C structure (C > A) and entry below the AB=CD target (TRAIN 2,385 / TEST 5,718 trades).
The best overall strategies hold baskets, so they have no per-stock exit; this entry is the stock-level version of them.
Portfolio: 10 slots × 10 %, priority = 63-day return. Scale-out rules are booked as one trade at the average exit price on the last exit day (approximation).
"% below local top" = median of (highest high within ±40 bars of the exit − exit price) / that high.

Default exit = sell when the market turns risk-off. Chosen on TRAIN (Sharpe-like): **the default itself** (TRAIN +13.9 %, TEST +14.2 %, DD −23 %).
Some rules did better in TEST after the fact (weekly Stochastic with gain +19.9 %, Fib-0.786 stop + 1.618 projection +19.9 %, 1.618 projection or 4·ATR trail +16.7 %),
but they were mid-ranked on TRAIN (TRAIN↔TEST rank correlation over the 61 rules is only 0.18), so this is likely noise.
4·ATR trailing alone: TEST +10.1 %. Fixed +10 % target: +8.8 %. Stochastic %K/%D cross > 80: +4.5 %. MACD cross: +4.0 %.
**No take-profit rule is reliably better than the simple baseline; none sells close to the top** (13–18 % below it in every rule).

### Exit rules on "phase risk-on + stock buy" entries (sorted by TRAIN Sharpe-like; TEST columns are out of sample)

| exit rule | family | TRAIN CAGR | TRAIN Sharpe | TEST avg net/trade | TEST win | TEST hold (bars) | TEST ret/100 bars | TEST target hit | TEST median % below local top | TEST CAGR | TEST maxDD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regime_off | baseline | +13.9 % | 0.93 | +1.14 % | 36 % | 15 | +7.9 % | 0 % | 14.6 % | +14.2 % | -23 % |
| mx | stoch/macd | +12.9 % | 0.86 | +1.14 % | 37 % | 11 | +10.0 % | 0 % | 13.6 % | +4.0 % | -52 % |
| fib618+trail4 | fib | +12.4 % | 0.76 | +2.11 % | 32 % | 23 | +9.2 % | 0 % | 15.7 % | +11.3 % | -29 % |
| fib786+trail4 | fib | +12.5 % | 0.76 | +2.19 % | 35 % | 26 | +8.5 % | 0 % | 16.0 % | +9.7 % | -30 % |
| pct30 | amplitude | +10.1 % | 0.68 | +2.47 % | 29 % | 37 | +6.8 % | 28 % | 16.5 % | +8.9 % | -41 % |
| mx+g | stoch/macd | +10.5 % | 0.67 | +1.99 % | 51 % | 18 | +10.8 % | 0 % | 14.4 % | +6.9 % | -44 % |
| mm1.618|trail4 | combo | +9.4 % | 0.65 | +1.46 % | 37 % | 18 | +8.1 % | 25 % | 14.9 % | +16.7 % | -31 % |
| trail4 | baseline | +9.7 % | 0.60 | +2.01 % | 34 % | 24 | +8.5 % | 0 % | 15.8 % | +10.1 % | -31 % |
| st80 | stoch/macd | +7.9 % | 0.59 | +0.55 % | 42 % | 10 | +5.2 % | 0 % | 13.7 % | +6.1 % | -34 % |
| time_med | time | +7.6 % | 0.59 | +0.60 % | 44 % | 9 | +6.4 % | 0 % | 13.6 % | +6.6 % | -37 % |
| pct15 | amplitude | +7.2 % | 0.56 | +1.32 % | 42 % | 22 | +6.1 % | 41 % | 15.0 % | +8.8 % | -30 % |
| st80+g | stoch/macd | +7.9 % | 0.55 | +1.18 % | 53 % | 15 | +7.8 % | 0 % | 14.2 % | +9.3 % | -34 % |
| cyc10_h1.0 | cycle-time | +9.0 % | 0.55 | +1.74 % | 39 % | 19 | +9.1 % | 0 % | 15.0 % | +2.8 % | -38 % |
| half_mx+trail4 | partial | +8.8 % | 0.53 | +1.58 % | 37 % | 24 | +6.6 % | 0 % | 15.0 % | +9.0 % | -32 % |
| cyc10_h0.75 | cycle-time | +7.9 % | 0.53 | +1.21 % | 42 % | 15 | +8.1 % | 0 % | 14.5 % | +7.0 % | -37 % |
| time0.618 | time | +6.7 % | 0.52 | +0.56 % | 44 % | 8 | +7.1 % | 0 % | 13.3 % | +6.0 % | -35 % |
| wst | stoch/macd | +7.7 % | 0.49 | +1.54 % | 38 % | 20 | +7.6 % | 0 % | 14.9 % | +7.8 % | -33 % |
| cyc10_h0.5 | cycle-time | +6.5 % | 0.48 | +0.71 % | 45 % | 10 | +7.0 % | 0 % | 13.7 % | +8.2 % | -31 % |
| scale_mm1.272/1.618/trail4 | combo | +8.2 % | 0.47 | +2.15 % | 40 % | 36 | +6.0 % | 42 % | 15.5 % | +8.9 % | -29 % |
| pct20|time1.618 | combo | +6.3 % | 0.46 | +1.03 % | 44 % | 14 | +7.6 % | 17 % | 14.1 % | +14.6 % | -29 % |
| pct20 | amplitude | +6.4 % | 0.46 | +1.82 % | 36 % | 27 | +6.8 % | 36 % | 15.7 % | +12.4 % | -34 % |
| cyc5_h1.0 | cycle-time | +5.9 % | 0.44 | +0.77 % | 44 % | 10 | +7.4 % | 0 % | 13.7 % | +6.0 % | -41 % |
| pct10 | amplitude | +5.3 % | 0.44 | +0.90 % | 50 % | 16 | +5.7 % | 50 % | 14.2 % | +8.8 % | -21 % |
| wst+g | stoch/macd | +6.8 % | 0.42 | +2.06 % | 43 % | 24 | +8.5 % | 0 % | 15.3 % | +19.9 % | -29 % |
| mm1.618|time1.618 | combo | +6.5 % | 0.41 | +1.45 % | 43 % | 15 | +9.9 % | 14 % | 14.2 % | +11.3 % | -32 % |
| ext1.618 | fib | +5.2 % | 0.39 | +1.28 % | 46 % | 20 | +6.5 % | 46 % | 14.8 % | +8.6 % | -36 % |
| mm1.0 | amplitude | +5.1 % | 0.38 | +1.30 % | 49 % | 18 | +7.3 % | 49 % | 14.7 % | +8.5 % | -35 % |
| stK&mxfall | stoch/macd | +4.8 % | 0.37 | +0.66 % | 41 % | 12 | +5.3 % | 0 % | 13.9 % | +3.2 % | -34 % |
| mm1.0|time1.0 | combo | +4.5 % | 0.37 | +0.73 % | 49 % | 9 | +7.8 % | 28 % | 13.5 % | +9.2 % | -30 % |
| scale_pct10/20/trail4 | combo | +6.2 % | 0.36 | +1.58 % | 43 % | 33 | +4.8 % | 50 % | 14.8 % | +7.0 % | -38 % |
| time1.0 | time | +5.3 % | 0.36 | +1.10 % | 44 % | 11 | +9.6 % | 0 % | 13.8 % | +9.0 % | -45 % |
| wmx | stoch/macd | +7.0 % | 0.36 | +4.17 % | 30 % | 40 | +10.5 % | 0 % | 17.6 % | +12.5 % | -49 % |
| half_stK|mx+trail4 | combo | +6.0 % | 0.35 | +1.09 % | 39 % | 24 | +4.6 % | 0 % | 14.7 % | +6.0 % | -33 % |
| half_mxturn+trail4 | partial | +6.0 % | 0.35 | +1.17 % | 37 % | 24 | +4.9 % | 0 % | 14.9 % | +8.4 % | -30 % |
| half_stK+trail4 | partial | +5.8 % | 0.34 | +1.16 % | 40 % | 24 | +4.8 % | 0 % | 14.9 % | +6.5 % | -32 % |
| time1.618 | time | +5.5 % | 0.33 | +1.64 % | 42 % | 16 | +10.1 % | 0 % | 14.5 % | +14.3 % | -41 % |
| mm1.618|time1.0 | combo | +4.6 % | 0.32 | +1.05 % | 45 % | 11 | +9.7 % | 10 % | 13.6 % | +8.4 % | -37 % |
| scale_mm1.0/1.618/time1.618 | combo | +5.5 % | 0.32 | +1.82 % | 43 % | 32 | +5.7 % | 49 % | 14.9 % | +7.3 % | -28 % |
| wmx+g | stoch/macd | +6.1 % | 0.32 | +4.62 % | 32 % | 44 | +10.5 % | 0 % | 17.8 % | +14.4 % | -44 % |
| mxturn | stoch/macd | +3.6 % | 0.31 | +0.32 % | 40 % | 7 | +4.4 % | 0 % | 13.2 % | +2.8 % | -30 % |
| mm1.618 | amplitude | +4.5 % | 0.28 | +2.51 % | 36 % | 30 | +8.3 % | 35 % | 15.7 % | +12.0 % | -35 % |
| stK&mxfall+g | stoch/macd | +3.8 % | 0.27 | +1.12 % | 50 % | 16 | +6.8 % | 0 % | 14.4 % | +2.9 % | -42 % |
| mm2.618 | amplitude | +4.3 % | 0.25 | +3.52 % | 27 % | 45 | +7.8 % | 23 % | 16.8 % | +4.9 % | -49 % |
| mm1.272 | amplitude | +3.7 % | 0.25 | +1.93 % | 42 % | 24 | +8.2 % | 42 % | 15.1 % | +10.6 % | -35 % |
| stK|mx | combo | +2.5 % | 0.23 | +0.16 % | 41 % | 7 | +2.3 % | 0 % | 13.0 % | +1.2 % | -38 % |
| mm2.0 | amplitude | +3.9 % | 0.23 | +2.91 % | 31 % | 37 | +8.0 % | 29 % | 16.2 % | +12.0 % | -39 % |
| cyc5_h0.75 | cycle-time | +2.8 % | 0.23 | +0.44 % | 45 % | 8 | +5.9 % | 0 % | 13.4 % | +7.8 % | -28 % |
| ext1.272 | fib | +2.4 % | 0.21 | +0.69 % | 57 % | 12 | +5.5 % | 57 % | 13.9 % | +4.4 % | -32 % |
| fib786+mm1.618 | fib | +3.5 % | 0.20 | +3.51 % | 44 % | 51 | +6.9 % | 42 % | 16.3 % | +19.9 % | -26 % |
| fib618+mm1.618 | fib | +3.3 % | 0.19 | +3.18 % | 37 % | 39 | +8.1 % | 36 % | 15.9 % | +11.1 % | -39 % |
| mxturn+g | stoch/macd | +2.5 % | 0.18 | +0.79 % | 57 % | 12 | +6.5 % | 0 % | 13.8 % | +5.0 % | -39 % |
| stK | stoch/macd | +1.9 % | 0.16 | +0.31 % | 44 % | 9 | +3.4 % | 0 % | 13.5 % | +4.5 % | -36 % |
| stK+g | stoch/macd | +1.4 % | 0.11 | +0.65 % | 54 % | 13 | +5.1 % | 0 % | 13.9 % | +2.1 % | -33 % |
| stK|mx+g | combo | +0.8 % | 0.06 | +0.66 % | 57 % | 12 | +5.6 % | 0 % | 13.7 % | +3.4 % | -34 % |
| ext2.618 | fib | +0.5 % | 0.03 | +2.87 % | 31 % | 38 | +7.6 % | 29 % | 16.3 % | +4.6 % | -50 % |
| mxdiv+g | stoch/macd | +0.2 % | 0.01 | +3.08 % | 38 % | 34 | +9.2 % | 0 % | 15.9 % | +14.0 % | -50 % |
| mm0.618 | amplitude | -0.2 % | -0.02 | +0.38 % | 61 % | 11 | +3.5 % | 61 % | 13.7 % | +7.7 % | -19 % |
| mxdiv | stoch/macd | -0.4 % | -0.02 | +2.74 % | 34 % | 29 | +9.3 % | 0 % | 15.4 % | +15.2 % | -43 % |
| cyc5_h0.5 | cycle-time | -1.2 % | -0.11 | +0.07 % | 44 % | 4 | +1.6 % | 0 % | 12.9 % | +0.8 % | -36 % |
| resist | amplitude | -3.8 % | -0.32 | +0.52 % | 60 % | 14 | +3.7 % | 59 % | 13.9 % | +6.5 % | -33 % |
### Exit rules on cycle-window entries (k = 10, |z − 1| ≤ 0.3, no phase gate; TRAIN 2,194 / TEST 4,734 trades)
Default for these entries is the cycle top time (low + T). None of the exits turns cycle entries into a good strategy: TEST median Sharpe-like −0.02.

| exit rule | family | TRAIN CAGR | TRAIN Sharpe | TEST avg net/trade | TEST win | TEST hold (bars) | TEST ret/100 bars | TEST target hit | TEST median % below local top | TEST CAGR | TEST maxDD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regime_off | baseline | +7.3 % | 0.54 | +0.75 % | 37 % | 11 | +6.9 % | 0 % | 13.1 % | -0.2 % | -38 % |
| fib618+trail4 | fib | +8.4 % | 0.49 | +1.10 % | 27 % | 20 | +5.5 % | 0 % | 15.1 % | +3.3 % | -48 % |
| fib786+trail4 | fib | +6.8 % | 0.37 | +1.13 % | 32 % | 24 | +4.7 % | 0 % | 15.3 % | +4.4 % | -48 % |
| trail4 | baseline | +6.4 % | 0.34 | +1.18 % | 32 % | 24 | +4.9 % | 0 % | 15.3 % | +0.3 % | -57 % |
| pct30 | amplitude | +5.0 % | 0.30 | +1.94 % | 27 % | 37 | +5.2 % | 26 % | 15.9 % | +11.1 % | -40 % |
| fib618+mm1.618 | fib | +4.5 % | 0.26 | +1.91 % | 30 % | 34 | +5.7 % | 28 % | 15.3 % | +10.7 % | -33 % |
| pct20 | amplitude | +3.8 % | 0.23 | +1.25 % | 33 % | 28 | +4.5 % | 33 % | 15.3 % | +5.4 % | -48 % |
| mm1.618|trail4 | combo | +4.0 % | 0.23 | +0.94 % | 34 % | 19 | +5.0 % | 22 % | 14.4 % | +3.3 % | -54 % |
| mm2.618 | amplitude | +4.5 % | 0.23 | +2.47 % | 24 % | 47 | +5.3 % | 20 % | 16.4 % | +1.6 % | -59 % |
| scale_pct10/20/trail4 | combo | +4.4 % | 0.22 | +1.02 % | 40 % | 33 | +3.1 % | 47 % | 14.4 % | +1.6 % | -41 % |
| scale_mm1.272/1.618/trail4 | combo | +4.3 % | 0.22 | +1.45 % | 36 % | 37 | +3.9 % | 38 % | 15.1 % | +3.2 % | -47 % |
| half_mx+trail4 | partial | +4.1 % | 0.21 | +0.86 % | 34 % | 24 | +3.6 % | 0 % | 14.4 % | -0.6 % | -56 % |
| mm1.618 | amplitude | +3.5 % | 0.19 | +1.86 % | 33 % | 32 | +5.7 % | 32 % | 15.3 % | +5.1 % | -49 % |
| half_mxturn+trail4 | partial | +3.6 % | 0.18 | +0.67 % | 36 % | 24 | +2.8 % | 0 % | 14.3 % | -0.4 % | -54 % |
| mm2.0 | amplitude | +3.3 % | 0.17 | +2.05 % | 28 % | 39 | +5.3 % | 26 % | 16.0 % | +9.7 % | -59 % |
| … (44 more rules, all in exit_table.pkl) | | | | | | | | | | | |

Rule names: `regime_off` = sell when market risk-off; `trail4` = 4·ATR trailing stop from the highest high; `pctX` = +X % target;
`mmR` = C + R·(B−A) (amplitude / AB=CD / Fib projection); `extR` = A + R·(B−A); `resist` = previous swing high; `fib618/786` = Fib retracement stop;
`timeR` = R × previous up-wave duration; `time_med` = median past up-wave; `cycK_hH` = entry low + H·T (cycle top window);
`X|Y` = first of X, Y; `scale_a/b/c` = 1/3 at each; `stK` = Stochastic %K crosses below %D above 80; `st80` = %K falls below 80; `wst`/`wmx` = weekly
Stochastic / MACD cross (completed weeks); `mx` = MACD crosses below signal; `mxturn` = histogram falls 2 bars from a positive peak;
`mxdiv` = bearish divergence (k=3 pivots); `stK&mxfall` = Stoch cross and histogram falling; `stK|mx` = either; `+g` = signal only counts if
in profit; `half_X+trail4` = sell 1/2 on X, rest on 4·ATR trail.


## Long-term horizon (hold 6–24 months, typically 9–12) – added on request
**Verdict:** long holding does **not** beat the short-term phase filter. The best long-term rule (chosen on TRAIN) made **TEST +14.7 %/yr, max DD −30 %**
(TRAIN +9.5 %). That is better than equal-weight buy & hold (+9.9 %, DD −60 %), but below the phase-filtered basket (+16.0 %, DD −22 %), with
much lower turnover (1.5× vs 10× per year). Fixed holding with only a wide % stop was bad in TRAIN for every entry type (−8 % to +4 %/yr).
The **monthly close below the 10-month SMA** exit was the most useful long-term exit. In practice it ends most trades early: the median hold
was 101 bars (≈5 months), not 9–12 months. Weekly/monthly Stochastic, MACD and Fibonacci/amplitude targets did not beat it on TRAIN.
**Per-stock cycle entries stay useless at long horizons** (TEST −4 % to +5 %).

**Uncertainty:** TEST is 6.9 years. That is only about 13.8 / 9.2 / 6.9 / 4.6 / 3.4 non-overlapping 6 / 9 / 12 / 18 / 24-month periods,
and one crash (2022) dominates. The per-trade ± values below (≈ 2 × SD of entry-year cohort means / √periods) are wide, mostly ±10–45 points.
So differences between horizons of a few %/yr are **not** statistically meaningful. TRAIN↔TEST rank correlation over the 350 long-term
variants was 0.65, mostly driven by the entry type (sector/phase entries good, cycle/any-stock entries bad), not by the exit.

**Setup:**
- Entries are taken at month-end closes and filled at the next open:
  - `reg`: market risk-on.
  - `sec`: risk-on and the stock is in the top-2 sectors.
  - `cyc`: expected-low window |z−1| ≤ 0.3, k = 10.
  - `all`: any liquid stock (control).
  - `gen`: the daily "phase + higher swing low > SMA50" trigger.
- Every trade has a maximum hold H = 126/189/252/378/504 bars plus one of these exits:
  - an intraday stop −15/−20/−25 % from the fill;
  - `ma10m`: a completed monthly close below the 10-month SMA, sold at the next open;
  - the −20 % stop plus a weekly/monthly take-profit:
    - `wstK`/`mstK`: weekly/monthly Stochastic cross > 80;
    - `wmx`/`mmx`: weekly/monthly MACD cross;
    - `+g` = the signal only counts if the trade is in profit;
    - `pct50`/`pct100`: +50 %/+100 % target;
    - `wmm1.0`/`wmm1.618`: weekly AB=CD / Fib projection, C + r·(B−A) on weekly k = 2 pivots.
- Portfolio: 10 slots × 10 % of equity. Priority is **most liquid first** (declared up front). The momentum-first and random priorities were also run.
  Results are sensitive to this choice: momentum-first was much worse for `reg`/`all`, because buying the strongest 6-month stocks for a long hold failed in VN.
- "% below local top" uses ±40 daily bars around the exit.

### Sector + phase entries (month-end, top-2 sectors, risk-on), 10 slots, most liquid first – per horizon
| rule | TRAIN CAGR | TEST CAGR | TEST max DD | TEST Sharpe-like | TEST win | TEST avg net/trade ± ~95 % | TEST avg hold (bars) | target hit | median % below local top | turnover/yr | non-overlapping periods in TEST | trades cut at data end |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H126|stop20 | -0.8 % | +16.1 % | -31 % | 0.78 | 41 % | +3.9 % ± 11 | 93 | 0 % | 22 % | 1.5× | 13.8 | 4 % |
| H126|ma10m | +5.5 % | +20.1 % | -35 % | 0.90 | 40 % | +4.4 % ± 10 | 89 | 0 % | 19 % | 1.8× | 13.8 | 1 % |
| H126|stop20|wstK+g | +4.9 % | +13.7 % | -25 % | 0.80 | 60 % | +3.0 % ± 4 | 49 | 0 % | 18 % | 2.8× | 13.8 | 3 % |
| H126|stop20|wmx+g | +2.0 % | +13.1 % | -34 % | 0.68 | 51 % | +4.3 % ± 8 | 76 | 0 % | 22 % | 1.9× | 13.8 | 3 % |
| H126|stop20|pct50 | +4.2 % | +18.6 % | -29 % | 1.03 | 46 % | +5.8 % ± 7 | 77 | 24 % | 19 % | 1.8× | 13.8 | 4 % |
| H126|stop20|wmm1.618 | +0.3 % | +14.6 % | -29 % | 0.76 | 50 % | +4.8 % ± 8 | 72 | 28 % | 20 % | 1.8× | 13.8 | 3 % |
| H126|stop20|mmx+g | -0.7 % | +15.8 % | -31 % | 0.77 | 41 % | +4.0 % ± 11 | 93 | 0 % | 22 % | 1.5× | 13.8 | 4 % |
| H189|stop20 | -0.7 % | +14.5 % | -40 % | 0.64 | 37 % | +8.2 % ± 21 | 122 | 0 % | 22 % | 1.4× | 9.2 | 4 % |
| H189|ma10m | +7.4 % | +10.8 % | -28 % | 0.48 | 36 % | +7.7 % ± 18 | 108 | 0 % | 19 % | 1.6× | 9.2 | 1 % |
| H189|stop20|wstK+g | +5.4 % | +12.0 % | -26 % | 0.70 | 61 % | +2.7 % ± 5 | 53 | 0 % | 18 % | 2.7× | 9.2 | 3 % |
| H189|stop20|wmx+g | +0.7 % | +13.7 % | -32 % | 0.70 | 52 % | +4.9 % ± 12 | 83 | 0 % | 22 % | 1.8× | 9.2 | 4 % |
| H189|stop20|pct50 | +4.2 % | +12.8 % | -29 % | 0.67 | 43 % | +5.9 % ± 10 | 94 | 28 % | 22 % | 1.6× | 9.2 | 4 % |
| H189|stop20|wmm1.618 | -1.6 % | +14.4 % | -35 % | 0.69 | 48 % | +6.7 % ± 16 | 88 | 30 % | 21 % | 1.7× | 9.2 | 4 % |
| H189|stop20|mmx+g | -1.5 % | +13.9 % | -40 % | 0.61 | 38 % | +8.2 % ± 21 | 122 | 0 % | 22 % | 1.4× | 9.2 | 4 % |
| H252|stop20 | -2.0 % | +8.3 % | -46 % | 0.39 | 35 % | +10.6 % ± 28 | 149 | 0 % | 22 % | 1.1× | 6.9 | 5 % |
| H252|ma10m | +9.5 % | +14.7 % | -29 % | 0.64 | 35 % | +9.1 % ± 25 | 119 | 0 % | 19 % | 1.5× | 6.9 | 1 % |
| H252|stop20|wstK+g | +5.7 % | +13.3 % | -23 % | 0.78 | 61 % | +2.7 % ± 6 | 55 | 0 % | 18 % | 2.7× | 6.9 | 3 % |
| H252|stop20|wmx+g | +1.2 % | +12.4 % | -31 % | 0.65 | 53 % | +4.9 % ± 13 | 86 | 0 % | 22 % | 1.7× | 6.9 | 4 % |
| H252|stop20|pct50 | +5.0 % | +9.9 % | -31 % | 0.58 | 44 % | +6.9 % ± 12 | 105 | 31 % | 21 % | 1.4× | 6.9 | 5 % |
| H252|stop20|wmm1.618 | -1.6 % | +8.7 % | -43 % | 0.42 | 48 % | +8.0 % ± 21 | 101 | 31 % | 21 % | 1.2× | 6.9 | 5 % |
| H252|stop20|mmx+g | -2.6 % | +6.1 % | -47 % | 0.29 | 37 % | +10.7 % ± 28 | 145 | 0 % | 22 % | 1.1× | 6.9 | 5 % |
| H378|stop20 | -3.4 % | +14.8 % | -40 % | 0.68 | 28 % | +6.9 % ± 44 | 190 | 0 % | 24 % | 1.0× | 4.6 | 10 % |
| H378|ma10m | +6.5 % | +14.8 % | -26 % | 0.70 | 35 % | +8.2 % ± 34 | 130 | 0 % | 21 % | 1.3× | 4.6 | 2 % |
| H378|stop20|wstK+g | +5.1 % | +12.8 % | -25 % | 0.75 | 61 % | +2.7 % ± 7 | 55 | 0 % | 18 % | 2.7× | 4.6 | 3 % |
| H378|stop20|wmx+g | +1.0 % | +13.9 % | -32 % | 0.72 | 53 % | +4.8 % ± 15 | 87 | 0 % | 22 % | 1.7× | 4.6 | 4 % |
| H378|stop20|pct50 | +4.1 % | +12.1 % | -31 % | 0.65 | 41 % | +6.7 % ± 15 | 119 | 34 % | 22 % | 1.3× | 4.6 | 7 % |
| H378|stop20|wmm1.618 | -1.7 % | +14.7 % | -39 % | 0.71 | 45 % | +7.2 % ± 28 | 119 | 32 % | 22 % | 1.1× | 4.6 | 7 % |
| H378|stop20|mmx+g | -6.1 % | +14.1 % | -43 % | 0.67 | 36 % | +9.5 % ± 44 | 174 | 0 % | 24 % | 1.0× | 4.6 | 7 % |
| H504|stop20 | -5.4 % | +18.8 % | -51 % | 0.80 | 25 % | +2.2 % ± 35 | 220 | 0 % | 25 % | 0.8× | 3.4 | 11 % |
| H504|ma10m | +6.1 % | +17.9 % | -24 % | 0.81 | 35 % | +7.0 % ± 34 | 132 | 0 % | 21 % | 1.3× | 3.4 | 2 % |
| H504|stop20|wstK+g | +5.1 % | +12.8 % | -25 % | 0.75 | 61 % | +2.7 % ± 8 | 55 | 0 % | 18 % | 2.7× | 3.4 | 3 % |
| H504|stop20|wmx+g | +0.8 % | +13.6 % | -32 % | 0.70 | 53 % | +4.8 % ± 18 | 87 | 0 % | 22 % | 1.7× | 3.4 | 4 % |
| H504|stop20|pct50 | +4.1 % | +8.6 % | -29 % | 0.48 | 41 % | +7.0 % ± 18 | 124 | 36 % | 22 % | 1.3× | 3.4 | 7 % |
| H504|stop20|wmm1.618 | -3.4 % | +19.4 % | -49 % | 0.83 | 44 % | +5.2 % ± 25 | 132 | 33 % | 22 % | 0.8× | 3.4 | 8 % |
| H504|stop20|mmx+g | -4.0 % | +18.3 % | -52 % | 0.78 | 35 % | +7.5 % ± 45 | 186 | 0 % | 24 % | 0.9× | 3.4 | 7 % |

### All entries, fixed horizon + −20 % stop only (TEST CAGR / max DD; TRAIN CAGR in brackets)
| H (bars) | phase basket entries (reg) | sector + phase (sec) | per-stock cycle window (cyc) | phase + daily stock trigger (gen) | any liquid stock (control) |
|---|---|---|---|---|---|
| 126 | +6.1 % / -44 % (-2.8 %) | +16.1 % / -31 % (-0.8 %) | -3.0 % / -65 % (-8.6 %) | +11.9 % / -37 % (+3.4 %) | +3.6 % / -63 % (-14.0 %) |
| 189 | +3.5 % / -44 % (-8.1 %) | +14.5 % / -40 % (-0.7 %) | -4.4 % / -66 % (-6.4 %) | +11.0 % / -48 % (-3.4 %) | +3.7 % / -66 % (-10.2 %) |
| 252 | +4.6 % / -46 % (-6.1 %) | +8.3 % / -46 % (-2.0 %) | +2.8 % / -58 % (-9.1 %) | +12.6 % / -27 % (+3.6 %) | +6.6 % / -57 % (-13.1 %) |
| 378 | +5.0 % / -46 % (-7.3 %) | +14.8 % / -40 % (-3.4 %) | -1.6 % / -63 % (-10.5 %) | +11.0 % / -39 % (+0.5 %) | +4.4 % / -70 % (-13.2 %) |
| 504 | +6.3 % / -43 % (-7.0 %) | +18.8 % / -51 % (-5.4 %) | +5.4 % / -54 % (-10.7 %) | +18.0 % / -32 % (-0.5 %) | +11.6 % / -55 % (-11.5 %) |

### Best long-term rule per entry (chosen on TRAIN Sharpe-like)
| entry: rule | TRAIN CAGR | TEST CAGR | TEST max DD | TEST Sharpe-like | TEST win | TEST avg net/trade ± ~95 % | TEST avg hold (bars) | target hit | median % below local top | turnover/yr | non-overlapping periods in TEST | trades cut at data end |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reg: H189|ma10m|wmx+g | +3.2 % | +7.7 % | -37 % | 0.47 | 42 % | +6.4 % ± 6 | 46 | 0 % | 17 % | 2.7× | 9.2 | 0 % |
| sec: H252|ma10m | +9.5 % | +14.7 % | -29 % | 0.64 | 35 % | +9.1 % ± 25 | 119 | 0 % | 19 % | 1.5× | 6.9 | 1 % |
| cyc: H189|ma10m | -3.1 % | +2.6 % | -48 % | 0.13 | 39 % | +5.2 % ± 11 | 75 | 0 % | 17 % | 2.6× | 9.2 | 2 % |
| gen: H504|stop20|wmx+g | +8.7 % | +10.3 % | -29 % | 0.56 | 54 % | +7.2 % ± 18 | 95 | 0 % | 21 % | 2.2× | 3.4 | 2 % |
| all: H189|ma10m+stop25 | -7.9 % | +4.7 % | -64 % | 0.22 | 37 % | +5.4 % ± 11 | 73 | 0 % | 18 % | 3.1× | 9.2 | 2 % |

Equity: `equity_longterm_sector_ma10m_{test,full}.csv` (TEST per year: 2020 +60.8 %, 2021 +51.5 %, 2022 −8.0 %, 2023 +10.1 %, 2024 +19.4 %, 2025 +4.5 %, 2026 −16.4 %).
Code: `lt.py` (per-stock long-term simulations), `ltan.py` (tables; `PRIO=liqv|rnd|mom126`), results `lt_table_*.pkl`.

## Today (as of 2026-11-19) – see `now.json`
- Market phase: **Downtrend** since 2026-10-29 → **risk-off (cash)**. Index −3.4 % below MA20, −6.7 % below MA100, breadth > MA50 = 27 %,
  drawdown from the 1-year high −21 %. US10y 3-month change +0.18 pp (no macro alarm), VND 3-month change −1.5 %.
- Top sectors now (rank-sum of 3-month return and breadth): **Du lịch & Giải trí**, **Ngân hàng** (then Hàng & Dịch vụ công nghiệp, Dịch vụ tài chính).
  The strategy would hold them only after the market turns risk-on.
- 62 liquid stocks are in an "expected-low window" (k = 10), 22 of them with a fresh swing-low confirmation. **This list has no proven value**
  (approach 3 failed); show it as information only.

## Caveats
- About 2,200 variants were tested in total; the chosen ones are optimistic in TRAIN by construction. TEST is 6.9 years and one big event (2022) drives the edge.
- Survivorship bias, approximate early dates, no real VNINDEX, no volume, no VN interest rates, cash earns 0 %.
- Not modelled: ceiling/floor locks (selling a whole basket into a floor day may not fill), T+2 settlement, slippage, market impact.
- The phase filter switches often; delays or higher costs cut the edge by about a third (see Verdict).

## Files (all in this folder)
- `RESULT.md`, `SPEC.md`, `now.json`.
- Equity curves (date, equity in VND; `_test` = fresh capital 2020, `_full` = 2008 → 2026): `equity_regime_sector_*.csv` (best combo),
  `equity_regime_basket_*.csv`, `equity_regime_stock_entries_*.csv`, `equity_sector_only_*.csv`, `equity_cycle_stocks_*.csv`, `equity_bh_ew_basket_*.csv`.
- Code: `mats.py` (matrices), `lib.py` (features, weight engine, metrics), `common.py` (phase, sector, holdings), `regime.py`, `sector.py`, `stock.py`, `ind.py`,
  `cyc.py` (per-stock cycles, triggers, all exit simulations), `cycan.py` (timing test), `cyc_port.py`, `exits.py`, `tradeeng.py`, `final.py`, `now.py`, `bench.py`.
- Grids: `regime_grid.pkl`, `sector_grid.pkl`, `cyc_grid.pkl`, `exit_table.pkl`.
