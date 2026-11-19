# Exits, tops and bottoms for the tool's buy signals – out-of-sample research (2026-11-19)

## Setup
- Data: `features_full.pkl` (891 stocks, delisted missing → survivorship bias), daily adjusted OHLC.
  Tool rows are every **10** bars per stock (not 5).
- **Entries**: every tool row with `muc ∈ {Mua, Mua mạnh}` → buy at the **next open**. Stop = tool `cat_lo`
  (= zone low − 0.5 ATR, rounded) if below entry, else entry − 1 ATR (median R = 1.54 ATR).
  Each signal is treated as an independent trade (overlaps allowed) so every exit method sees exactly the same entries.
  Entries need ≥160 bars of future data → last entries ≈ March 2026.
- **Random control**: 18,856 random tool rows (any `muc`, any stock/date), stop = entry − 1.5 ATR.
- Fees: buy 0.15 %, sell 0.15 % + 0.1 % tax on every trade (from `khuyen_nghi.py`).
- Execution: stop/target intraday (gap → filled at the open), stop checked first on a bar; close-based
  rules (MA cross, top signals) sell at the **next open**; time exit at the close. Trailing stops use data up to
  yesterday's close only; swing pivots (k = 3 or 5) are used only after they are confirmed (k bars later).
- **Split**: TRAIN = entries 2006–2019 (792 tool / 6,694 random) – used to pick parameters;
  **TEST = 2020-01 → 2026-03 (1,480 tool / 12,162 random) – untouched until the end.**
- t-statistics are for the paired per-trade difference vs. the 3R baseline, clustered by entry month.
- Metrics: `capture` = exit price / highest high in the 120 bars after entry (median);
  `dist_top` = exit price / real local top − 1, real top = highest high in [entry, exit + 40 bars] (median);
  `≤5%` = share of exits within 5 % of that real top; `lag` = bars from real top to exit (median, + = sold after the top).

## A. Exit methods (same entries)

### TEST 2020–2026, tool buy signals (n = 1,480)
| exit | ret/trade | median | win | hold (bars) | ret per 100 bars held | capture | dist to real top | exits ≤5 % from top | Δ vs 3R (t) |
|---|---|---|---|---|---|---|---|---|---|
| **fixed 3R, 60 bars (current)** | **−0.23 %** | −4.6 % | 29 % | 17 | −1.3 % | 83.7 % | −12.3 % | 12.9 % | – |
| fixed 2R | −0.27 % | −4.2 % | 36 % | 14 | −2.0 % | 84.4 % | −11.5 % | 15.5 % | −0.04 (−0.2) |
| fixed 4R | −0.20 % | −4.9 % | 26 % | 19 | −1.1 % | 83.5 % | −12.7 % | 11.6 % | +0.03 (0.1) |
| **chandelier 4 ATR from highest high, max 120 (chosen on TRAIN)** | **+0.73 %** | −4.0 % | 26 % | 20 | **+3.7 %** | 83.5 % | −13.1 % | 6.2 % | **+0.96 (1.1)** |
| chandelier 3 ATR (high) | +0.06 % | −3.3 % | 28 % | 14 | +0.4 % | 84.5 % | −11.9 % | 7.1 % | +0.29 (1.0) |
| chandelier 2 ATR (high) | −0.50 % | −2.3 % | 33 % | 9 | −5.8 % | 84.8 % | −10.4 % | 11.2 % | −0.28 (−0.7) |
| chandelier 4 ATR (close) | +0.91 % | −4.4 % | 23 % | 24 | +3.9 % | 82.9 % | −13.7 % | 6.1 % | +1.14 (1.2) |
| chandelier 5 / 6 ATR (post-hoc) | +1.43 / +1.28 % | | 24 / 21 % | 25 / 28 | +5.8 / +4.5 % | 82.8 / 82.2 % | −13.9 / −14.3 % | 6 % | +1.66 (1.6) / +1.51 (1.4) |
| trail below confirmed swing low (pivot 3) | +0.10 % | −2.3 % | 19 % | 11 | +0.9 % | 84.2 % | −10.8 % | 14.8 % | +0.32 (0.7) |
| swing low − 0.5 ATR | +0.58 % | −3.5 % | 22 % | 18 | +3.3 % | 83.7 % | −12.0 % | 9.5 % | +0.81 (1.3) |
| close < MA20 (next open) | −0.01 % | −1.0 % | 31 % | 5 | −0.3 % | 84.6 % | −9.4 % | 25.6 % | +0.22 (0.5) |
| close < MA50 (armed after close > MA50) | +0.96 % | −2.6 % | 27 % | 16 | +6.0 % | 84.0 % | −11.8 % | 13.5 % | +1.19 (1.7) |
| 50 % at 2R, rest chandelier 4 ATR | +0.24 % | −3.8 % | 34 % | 20 | +1.2 % | 84.1 % | −12.3 % | 7.4 % | +0.47 (1.1) |
| 50 % at 3R, rest chandelier 4 ATR | +0.26 % | −4.0 % | 28 % | 20 | +1.3 % | 84.1 % | −12.5 % | 6.9 % | +0.49 (1.1) |
| chandelier 3 ATR + sell on RSI>75 | −0.11 % | −3.3 % | 28 % | 13 | −0.9 % | 84.7 % | −11.5 % | 9.3 % | +0.11 (0.5) |
| chandelier 3 ATR + sell on close > MA20+3 ATR | −0.12 % | | 28 % | 13 | −1.0 % | 84.8 % | −11.5 % | 10.5 % | +0.11 (0.4) |
| time 20 / 40 / 60 / 120 bars (stop only) | −0.39 / −0.06 / +0.42 / +1.43 % | | 32 / 26 / 21 / 15 % | 13 / 20 / 25 / 37 | −3.0 / −0.3 / +1.6 / +3.9 % | 82.5–84.3 % | −11.6 … −14.5 % | 6–11 % | time 120: +1.66 (1.4) |

TRAIN (2006–2019, tool entries): 3R −0.70 %; chandelier 4 ATR (high) **+0.72 %** (best of the grid, Δ +1.42, t 3.0);
swing − 0.5 ATR +0.56 %; MA50 +0.30 %; time 120 −0.65 %; all partial/top-signal variants ≤ +0.06 %.

### Random entries (control)
| | TRAIN 3R | TRAIN chand 4 | TEST 3R | TEST chand 4 | TEST Δ (t) | TEST time 120 |
|---|---|---|---|---|---|---|
| random entries | −0.60 % | −0.17 % | +0.40 % | +1.12 % | +0.72 (2.6) | +2.79 % |
| tool buy entries | −0.70 % | +0.72 % | −0.23 % | +0.73 % | +0.96 (1.1) | +1.43 % |

Per-year TEST, chandelier 4 − 3R on tool entries (pp/trade): 2020 +3.7, 2021 +3.9, 2022 +0.4, 2023 −0.1, 2024 −0.8,
2025 −0.5, 2026 −0.5. The whole gain comes from the 2020–21 bull run; in sideways years it is slightly worse.

Sensitivity (picked post-hoc from a small extra grid; treat as optimistic): initial stop = min(tool stop, entry − 2 ATR)
+ chandelier 4: TRAIN +0.89 %, TEST +1.07 % (Δ +1.30, t 1.4); 53–58 % of trades with the tool stop end at the
**initial** stop – the tool's stop (≈1.5 ATR) is tight.

**Verdict A**
- A wide trailing stop (4 ATR below the highest high since entry, max 120 bars) is the best exit chosen on TRAIN and
  stays the better choice on TEST: **+0.73 %/trade vs −0.23 % for the current fixed 3R (+0.96 pp, t 1.1 – not
  significant)**; on random entries +0.72 pp (t 2.6). It works by letting the few big trends run (95th pct trade
  +26 %) – it does not raise the win rate (26 %) and the median trade is still −4 %.
- It is regime-dependent (strong in 2020–21, slightly negative 2023–26). Holding for a fixed 120 bars did even better
  on TEST (+1.43 %) but was the worst on TRAIN (−0.65 %) – i.e. returns mostly come from market exposure, not exit skill.
- Fixed targets (2R/3R/4R), selling half at 2R/3R, MA20 exits and "sell on overbought" (RSI>75/80, >3–4 ATR above MA20)
  all **reduce** return vs the plain 4-ATR trail.
- **No exit method sells near real tops.** Every method sells at a median 10–15 % below the real local top and captures
  82–85 % of the 120-bar peak; only 6–16 % of exits are within 5 % of the top. Tighter exits are a bit closer to the top
  (MA20: 26 % within 5 %) but earn less. "Selling near the top" and "making money" pull in opposite directions here.
- Tool entries are no better than random entries under any exit (TEST 3R: −0.23 % vs +0.40 %; chand 4: +0.73 % vs +1.12 %).

## B. Top prediction

### B1. Does a "top" signal predict a fall? (precision = falls 5 % before rising 5 % within 20 bars)
Daily bars, all stocks. Base = all bars; "uptrend" = close > MA50 and > close 20 bars ago.
`top≤10` = a significant top (highest high of ±20 bars, followed by a ≥10 % drop within 20 bars) occurs within the next 10 bars.

| signal (daily) | TEST n | P(fall 5 % first) | lift vs uptrend | P(top ≤10 bars) | lift | fwd 20d return |
|---|---|---|---|---|---|---|
| base all bars | 1,466,674 | 44.9 % | | 17.6 % | | +1.4 % |
| base uptrend | 565,345 | 46.2 % | 1.00 | 25.5 % | 1.00 | +1.7 % |
| **naive control: high = 20-day high** | 233,608 | 41.3 % | 0.89 | 40.8 % | 1.60 | +1.9 % |
| naive control: 60-day high | 127,438 | 39.1 % | 0.85 | 41.2 % | 1.61 | +2.1 % |
| RSI > 75 | 72,127 | 39.2 % | 0.85 | 38.5 % | 1.51 | +2.1 % |
| RSI > 80 | 44,969 | 35.8 % | 0.77 | 38.0 % | 1.49 | +2.0 % |
| close > MA20 + 3 ATR | 92,353 | 45.4 % | 0.98 | 42.2 % | 1.65 | +2.2 % |
| close > MA20 + 4 ATR | 53,252 | 43.5 % | 0.94 | 44.3 % | 1.73 | +2.3 % |
| RSI>75 & >3 ATR | 51,226 | 42.8 % | 0.93 | 43.9 % | 1.72 | +2.7 % |
| first touch of Fib 1.272 ext. of last swing | 33,167 | 45.3 % | 0.98 | 44.9 % | 1.76 | +2.1 % |
| first touch of Fib 1.618 ext. | 20,077 | 45.5 % | 0.99 | 47.6 % | 1.86 | +2.4 % |
| bearish RSI divergence (pivot 3 / 5, at confirmation) | 12,849 / 9,432 | 44.4 / 44.3 % | 0.96 | 17.4 / 15.1 % | 0.68 / 0.59 | +1.8 / +1.9 % |

Tool rows (every 10 bars), TEST, base uptrend P(fall) 43.4 %, P(top≤10) 24.1 %, fwd20 +1.6 %:

| tool signal | n | P(fall) | lift | P(top≤10) | lift | fwd20 |
|---|---|---|---|---|---|---|
| dinh_muc ≥1 / ≥2 / ≥3 | 18,058 / 6,705 / 1,781 | 43.6 / 42.7 / 46.0 % | 1.00 / 0.98 / 1.06 | 18.0 / 24.7 / 13.5 % | 0.75 / 1.02 / 0.56 | +1.4 / +2.0 / +0.9 % |
| dinh_so ≥4 / ≥5 | 4,030 / 918 | 45.3 / 47.9 % | 1.04 / 1.10 | 25.8 / 27.8 % | 1.07 / 1.15 | +1.8 / +1.2 % |
| dh_fibo / dh_stoch / dh_mfi | 2,821 / 9,723 / 5,107 | 45.6 / 43.4 / 43.9 % | 1.05 / 1.00 / 1.01 | 34.3 / 26.9 / 30.6 % | 1.42 / 1.12 / 1.27 | +1.9 / +2.2 / +2.8 % |
| dh_phan_ky / dh_quet / dh_cung | 4,434 / 5,030 / 31,309 | 45.0 / 43.8 / 45.9 % | 1.04 / 1.01 / 1.06 | 16.0 / 24.8 / 11.2 % | 0.66 / 1.03 / 0.47 | +1.1 / +0.9 / +0.5 % |
| dh_choch / dh_nen / dh_nhip | 8,177 / 5,724 / 10,755 | 46.6 / 39.3 / 44.4 % | 1.07 / 0.91 / 1.02 | 5.8 / 22.6 / 22.9 % | 0.24 / 0.94 / 0.95 | +0.3 / +1.9 / +2.0 % |

TRAIN numbers are the same within ±3 pp (see `B1_log.txt`).

**Verdict B1**: No top signal predicts a fall. Overbought signals (RSI, distance above MA20, Fib extension touches)
have a *lower* chance of a 5 % fall than the base and positive forward returns (momentum continues). Their higher
"top within 10 bars" rate (1.5–1.9×) is mechanical: simply being at a 20-day high gives the same lift (1.6×).
The tool's `dinh_*`/`dh_*` signals: lift 0.9–1.1 on falls; the "structure-break" ones (`dh_choch`, `dh_cung`,
`dh_phan_ky`) fire **after** the top (top-within-10 rate 0.24–0.66× base). Best tool lift: `dinh_so ≥5` 1.10–1.22
(n small, fwd20 still positive). → Do not use any of these as a SELL trigger; they can be shown as information only.

### B2. "Expected top price" estimates at the tool's buy entries
Realized next top = highest high after entry until price first drops 10 % below that high (zigzag 10 %, max 120 bars).
TEST, tool entries (n = 1,480; realized median gain +7.6 %, median time to top 6 bars, IQR 1–18):

| estimate | median abs error | median signed | hit ±3 % | reached (top ≥ estimate) | rank corr. with realized |
|---|---|---|---|---|---|
| tool tp1 | 12.7 % | +10.3 % | 12.8 % | 22 % | +0.03 |
| tool tp2 | 14.5 % | +12.0 % | 10.3 % | 19 % | |
| entry + 2R / 3R / 4R | 7.7 / 11.0 / 14.9 % | +3 / +8 / +13 % | 19 / 13 / 10 % | 38 / 27 / 20 % | −0.07 (3R) |
| entry + 2 / 3 / 5 / 8 ATR | 5.9 / 7.9 / 12.3 / 20.8 % | 0 / +4 / +10 / +20 % | 25 / 19 / 12 / 6 % | 47 / 36 / 23 / 13 % | −0.04 |
| Fib 1.272 / 1.618 ext. of last swing (pivot 5) | 9.6 / 12.6 % | +5 / +10 % | 17 / 13 % | 35 / 25 % | |
| next Fib level above entry (1.0…4.236) | 7.7 % | +1.4 % | 20.5 % | 45 % | −0.05 |
| last swing high (if above entry) | 7.9 % | +1.9 % | 19.5 % | 44 % | −0.05 |
| 52-week high | 14.7 % | +11.7 % | 10.8 % | 23 % | 0.00 |
| **constant: entry × (1 + 7.4 %)** (TRAIN median) | **5.5 %** | 0 % | **28.3 %** | 51 % | (none) |
| constant: entry + 1.9 ATR (TRAIN median) | 5.8 % | 0 % | 26.4 % | 49 % | |

Expected **time** to top: constant 6 bars (TRAIN median) → median abs error 6 bars, within ±5 bars 43 %;
random-walk time from the 3R distance: error 22 bars; from next-Fib distance: 9 bars. Random entries give the same picture.

Realized next-top distribution (tool entries, TEST; TRAIN within 0.1 ATR): gain in ATR P25/50/75/90 = 0.64 / 1.86 /
4.65 / 9.3; P(top ≥ entry + 1/2/3/4/6 ATR) = 66 / 47 / 36 / 29 / 18 %; time P25/50/75/90 = 1 / 6 / 18 / 44 bars.
With a 15 % zigzag: 2.7 ATR median, 12 bars (IQR 2–39).

**Verdict B2**: No price estimate has any skill – rank correlation with the realized top is 0 or slightly negative for
all of them. The tool's tp1 overshoots (only 22 % reached, median error 12.7 %). The best "estimate" is a constant
(+1.9 ATR ≈ +7.5 %), which is right within ±3 % only 28 % of the time. Time to top is likewise only predictable as
a distribution (median 6 bars, very wide). → Show the top as a probability band, not a point forecast.

## C. Entry vs. the real bottom
Real bottom = lowest low in [entry − 20, entry + 20] bars.

| | median distance entry → bottom | ≤3 % above bottom | ≤5 % | position in ±20-bar range (0 = bottom) | bottom still ahead |
|---|---|---|---|---|---|
| tool buys TRAIN / TEST | 9.9 % / 10.3 % | 7.1 / 6.7 % | 18.8 / 18.2 % | 0.42 / 0.42 | 48 / 50 % |
| random TRAIN / TEST | 13.5 % / 13.5 % | 5.8 / 6.2 % | 13.6 / 14.0 % | 0.48 / 0.49 | 42 / 39 % |

Limit orders after the signal (valid 10 bars, cancelled if the stop is touched first), TEST, tool entries; exit = chandelier 4 ATR:

| order | filled | better price vs market | dist. to bottom (filled) | ret per filled trade | same trades at market | missed trades at market | **ret per signal** (missed = 0) |
|---|---|---|---|---|---|---|---|
| market (next open) | 100 % | – | 10.3 % | – | – | – | **+0.73 %** |
| zone high (`vung_cao`) | 93 % | 0 % | 10.1 % | +1.10 % | +0.90 % | −1.6 % | +1.03 % |
| `gia_mua` | 89 % | −0.1 % | 9.8 % | +1.08 % | +0.55 % | +2.2 % | +0.96 % |
| zone mid | 72 % | −1.4 % | 8.5 % | +0.92 % | −0.74 % | +4.6 % | +0.67 % |
| close − 0.5 ATR | 65 % | −1.9 % | 8.5 % | +0.72 % | −1.34 % | +4.6 % | +0.47 % |
| close − 1 ATR | 33 % | −3.7 % | 7.8 % | +0.60 % | −3.44 % | +2.8 % | +0.20 % |
| close − 3 % | 44 % | −3.0 % | 10.5 % | +1.50 % | −1.35 % | +2.4 % | +0.66 % |
With the 3R exit, per-signal returns: market −0.23 %, zone high +0.04 %, zone mid −0.19 %, close−1 ATR +0.10 %.
TRAIN shows the same pattern (zone high +0.98 %, zone mid +0.34 % vs market +0.72 % per signal with chand 4).

**Verdict C**: Tool buys are somewhat closer to the local bottom than random entries (median 10 % vs 13.5 % above it;
19 % vs 14 % within 5 %), but only ~7 % are within 3 % of the bottom and half the time the bottom is still ahead.
Waiting for a pullback buys 1.5–3.7 % cheaper but misses 28–67 % of trades, and the missed ones are the winners
(adverse selection): per-signal return is no better (zone mid +0.67 %, −1 ATR +0.20 % vs market +0.73 %).
A limit at the zone high/`gia_mua` ≈ market order (+0.2–0.3 pp, within noise). → No improvement worth the missed trades.

## Overall verdict
1. **Exit**: replace the fixed 3R target with a **4-ATR chandelier trailing stop from the highest high, max 120 bars**
   (keep the initial stop). Best on TRAIN, better on TEST (+0.96 pp/trade vs 3R, +0.72 pp on random entries), but
   not statistically significant on tool entries (t 1.1), and the gain is concentrated in trending years.
2. **Tops cannot be predicted** with any of the tested signals or price formulas; exits end 10–15 % below the real top
   whatever the method. A "predicted top" must be shown as a probability band (≈ entry + 0.6 / 1.9 / 4.7 ATR for
   P25/P50/P75), and the tool's tp1 should not be presented as "the sell price" (reached only 22 % of the time).
3. **Bottoms**: the tool buys slightly closer to bottoms than random, but waiting for a deeper pullback does not help.
4. The underlying problem remains the entry signal (≈ random, see `../research/RESULT.md`); a better exit adds at most
   ~1 pp/trade and cannot turn the signals into a reliable edge.

## Files (`research2/`)
`common2.py` (indicators, pivots, numba trade simulator), `prep.py` (entries), `exits.py` (method grid + metrics),
`run_A.py`/`A_log.txt` (exit grid), `run_A2.py`/`A2_log.txt` (k = 5/6, per year), `run_A4.py`/`A4_log.txt` (initial stop width),
`A3_log.txt` (exit distributions), `run_B1.py`/`B1_log.txt` (top signals), `run_B2.py`/`B2_log.txt`/`B2b_log.txt`
(top price/time estimates), `run_C.py`/`C_log.txt` (bottoms, limit orders). Tables: `A_table.pkl`, `B1_table.pkl`,
`B2_table.pkl`, `C_table.pkl`. Spec: `SPEC.md`.
