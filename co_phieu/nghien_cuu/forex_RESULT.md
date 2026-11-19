# Backtest: StockPredict forex/crypto trade plan (+ LEVEL 1 MA formula) – 10,000 USD account

Run date 2026-11-19. Code in this folder (`signals.py`, `sim.py`, `l1.py`, `report.py`); app code imported read-only from
`/home/user/stockpredict/co_phieu` (`forex.ke_hoach_fx`, `forex.khoi_luong`, `phan_tich.phan_tich_khung`).

## Verdict (short)

* **The app's Buy/Sell plan does not show an edge over random direction on any timeframe.** The same entries with a
  coin-flip direction (same SL distance, 3R TP, same sizing) did about as well (D: +172% vs random mean +168%; 4H: +60% vs
  +29% but random 5–95% range is −50%…+224%; W, M: inside the random range). No positive t-statistic of avg R reaches 2 (best: D +1.95, but random direction on the same bars has avg R +0.07 vs +0.08).
* **15m and 1H lose the account** (−98% both; avg R −0.20 / −0.07): the spread alone costs 0.19 R / 0.08 R per trade
  because the stops are small. Random direction loses the same way → the losses are costs, the signal adds nothing.
* **4H and D were profitable in this sample (+60%, +172%) but that profit is the market, not the signal:** it comes mostly
  from BTC and gold longs during their secular bull runs (random direction on D is also +168% on average because long
  random trades on BTC/XAU earn roughly +0.6 R / +0.4 R per trade in a diagnostic run). Pure FX majors on D/4H are around zero or negative
  (AUDUSD, NZDUSD, USDCHF clearly negative). Max drawdowns on 4H/D were 44–54% at 1% risk per trade.
* **Stability:** 4H/D were ~break-even in the first half (avg R +0.02) and positive in the second half (+0.11…+0.14,
  the BTC/gold rally of 2024–2026 for 4H). W and M flip sign between halves. Not stable.
* **Trailing-stop variant (4·ATR, max 100 bars)** changes little: same sign per TF, still not better than random.
* **LEVEL 1 two-MA formula** (MA6/10 and MA10/20, position 30% + confirmation 70% of 1% risk): loses on 15m, 4H and on D with
  MA6/10; roughly break-even on 1H MA10/20 (−15%); positive on **D MA10/20 (+26%, avg R +0.08, PF 1.23, max DD −20%,
  stable in both halves)** and **W MA6/10 (+15%, only 73 opportunities)**. These beat 85–90% of the random-direction runs but
  avg R t-stats are only +0.9 and +1.3 → **not statistically significant**; with 2 MA pairs × 5 TFs tested, one or two
  "winners" are expected by chance.
* Bottom line: **do not trade these signals with real money on the strength of this test.** Nothing here beats random
  direction with confidence. Lower timeframes (15m, 1H) are clearly loss-making after spread.

## Data per timeframe

| TF | instruments | trading period (first decision → last bar) | bars/instrument (median) | decision step |
|---|---|---|---|---|
| 15m | 9 | 2026-09-01 → 2026-11-19 | 5625 | every 2 bar(s) |
| 1H | 9 | 2024-02-14 → 2026-11-19 | 17252 | every 2 bar(s) |
| 4H | 9 | 2024-03-20 → 2026-11-19 | 4449 | every 1 bar(s) |
| D | 9 | 1997-08-26 → 2026-11-18 | 5971 | every 1 bar(s) |
| W | 9 | 2000-02-04 → 2026-11-13 | 1198 | every 1 bar(s) |
| M | 9 | 2001-10-31 → 2026-10-31 | 275 | every 1 bar(s) |

## Fixed SL / TP = 3R (the app's plan as-is)

| TF | trades | win rate | avg R | t(avg R) | spread cost (R) | net USD | return | max DD | PF | skipped |
|---|---|---|---|---|---|---|---|---|---|---|
| 15m | 1853 | 20.3% | -0.196 | -4.95 | 0.187 | -9,766 | -97.7% | -98.4% | 0.70 | 1215 |
| 1H | 5087 | 23.4% | -0.068 | -2.83 | 0.079 | -9,824 | -98.2% | -98.9% | 0.85 | 7308 |
| 4H | 1383 | 27.0% | +0.069 | +1.44 | 0.033 | +5,971 | +59.7% | -43.9% | 1.06 | 19 |
| D | 1784 | 27.4% | +0.084 | +1.95 | 0.012 | +17,166 | +171.7% | -53.9% | 1.09 | 11 |
| W | 315 | 26.3% | +0.023 | +0.23 | 0.005 | +647 | +6.5% | -25.7% | 1.03 | 167 |
| M | 101 | 28.7% | +0.079 | +0.46 | 0.002 | +1,137 | +11.4% | -10.8% | 1.20 | 224 |

**vs. random direction** (same entry bars, same SL/TP distance, same sizing; 20 seeds)

| TF | strategy return | random return mean [5%–95%] | strategy avg R | random avg R mean | share of random runs ≥ strategy |
|---|---|---|---|---|---|
| 15m | -97.7% | -94.0% [-97.5% – -87.1%] | -0.196 | -0.153 | 95% |
| 1H | -98.2% | -96.6% [-99.3% – -91.3%] | -0.068 | -0.070 | 60% |
| 4H | +59.7% | +28.8% [-50.2% – +224.3%] | +0.069 | +0.023 | 25% |
| D | +171.7% | +167.9% [+11.5% – +380.1%] | +0.084 | +0.072 | 45% |
| W | +6.5% | -7.2% [-30.3% – +23.4%] | +0.023 | -0.026 | 20% |
| M | +11.4% | +6.2% [-4.7% – +22.4%] | +0.079 | +0.083 | 30% |

**Stability: first half vs second half of each TF's period** (by entry time)

| TF | H1 trades | H1 win | H1 avg R | H1 PF | H2 trades | H2 win | H2 avg R | H2 PF |
|---|---|---|---|---|---|---|---|---|
| 15m | 954 | 18.4% | -0.284 | 0.69 | 899 | 22.2% | -0.103 | 0.80 |
| 1H | 2658 | 23.3% | -0.070 | 0.85 | 2429 | 23.5% | -0.066 | 0.88 |
| 4H | 677 | 25.6% | +0.021 | 0.99 | 706 | 28.3% | +0.114 | 1.12 |
| D | 770 | 25.7% | +0.018 | 0.99 | 1014 | 28.7% | +0.135 | 1.13 |
| W | 118 | 27.1% | +0.097 | 1.09 | 197 | 25.9% | -0.022 | 1.00 |
| M | 49 | 32.7% | +0.299 | 1.55 | 52 | 25.0% | -0.128 | 0.90 |

## Variant: same entry & initial SL, no TP, 4·ATR trailing stop, max hold 100 bars

| TF | trades | win rate | avg R | t(avg R) | spread cost (R) | net USD | return | max DD | PF | skipped |
|---|---|---|---|---|---|---|---|---|---|---|
| 15m | 1851 | 22.0% | -0.183 | -3.85 | 0.198 | -9,741 | -97.4% | -98.4% | 0.54 | 1217 |
| 1H | 4286 | 24.5% | -0.091 | -2.88 | 0.088 | -9,893 | -98.9% | -99.3% | 0.75 | 12478 |
| 4H | 1344 | 28.9% | +0.073 | +1.18 | 0.036 | +3,911 | +39.1% | -53.2% | 1.05 | 23 |
| D | 1790 | 27.4% | +0.096 | +1.49 | 0.013 | +19,658 | +196.6% | -61.0% | 1.12 | 10 |
| W | 324 | 29.6% | +0.066 | +0.48 | 0.005 | +991 | +9.9% | -24.0% | 1.06 | 105 |
| M | 81 | 25.9% | -0.033 | -0.18 | 0.002 | -100 | -1.0% | -10.4% | 0.98 | 214 |

**vs. random direction** (same entry bars, same SL/TP distance, same sizing; 20 seeds)

| TF | strategy return | random return mean [5%–95%] | strategy avg R | random avg R mean | share of random runs ≥ strategy |
|---|---|---|---|---|---|
| 15m | -97.4% | -96.3% [-97.6% – -94.3%] | -0.183 | -0.164 | 70% |
| 1H | -98.9% | -95.2% [-98.9% – -90.6%] | -0.091 | -0.045 | 95% |
| 4H | +39.1% | +39.9% [-47.0% – +224.3%] | +0.073 | +0.039 | 35% |
| D | +196.6% | +355.1% [+95.9% – +971.7%] | +0.096 | +0.104 | 50% |
| W | +9.9% | +42.0% [+4.5% – +109.6%] | +0.066 | +0.147 | 85% |
| M | -1.0% | +8.0% [-19.1% – +32.1%] | -0.033 | +0.124 | 55% |

**Stability: first half vs second half of each TF's period** (by entry time)

| TF | H1 trades | H1 win | H1 avg R | H1 PF | H2 trades | H2 win | H2 avg R | H2 PF |
|---|---|---|---|---|---|---|---|---|
| 15m | 971 | 20.0% | -0.313 | 0.51 | 880 | 24.3% | -0.040 | 0.90 |
| 1H | 2651 | 26.0% | -0.107 | 0.75 | 1635 | 22.3% | -0.065 | 0.87 |
| 4H | 655 | 27.9% | -0.025 | 0.92 | 689 | 29.8% | +0.166 | 1.18 |
| D | 664 | 27.4% | +0.012 | 0.99 | 1126 | 27.4% | +0.145 | 1.16 |
| W | 119 | 24.4% | +0.059 | 1.06 | 205 | 32.7% | +0.070 | 1.06 |
| M | 39 | 25.6% | -0.094 | 1.00 | 42 | 26.2% | +0.024 | 0.94 |

## Per instrument (fixed SL/TP 3R; avg R is independent of compounding)

| instrument | 15m n / avgR / net USD | 1H n / avgR / net USD | 4H n / avgR / net USD | D n / avgR / net USD | W n / avgR / net USD | M n / avgR / net USD |
|---|---|---|---|---|---|---|
| AUDUSD | 320 / -0.28 / -2,357 | 659 / -0.05 / -1,640 | 155 / -0.02 / -1,086 | 122 / -0.18 / -6,766 | 23 / -0.70 / -1,408 | 11 / +0.17 / +254 |
| BTCUSD | 185 / -0.22 / -536 | 418 / -0.03 / -104 | 152 / +0.17 / +3,055 | 180 / +0.70 / +19,632 | 34 / +0.29 / +840 | 4 / +1.00 / +382 |
| EURUSD | 265 / +0.01 / -747 | 692 / -0.09 / -1,258 | 155 / +0.17 / +2,499 | 175 / +0.09 / +2,648 | 38 / -0.20 / -736 | 15 / -0.47 / -489 |
| GBPUSD | 249 / -0.20 / -2,687 | 769 / -0.02 / -1,190 | 154 / +0.26 / +3,393 | 163 / +0.10 / +70 | 33 / -0.09 / -261 | 10 / +0.08 / -11 |
| NZDUSD | 316 / -0.30 / -2,727 | 806 / -0.14 / -1,692 | 174 / -0.06 / -1,267 | 177 / -0.08 / -3,654 | 21 / -0.28 / -650 | 13 / -0.13 / -92 |
| USDCAD | 103 / -0.06 / +697 | 398 / -0.07 / -1,422 | 145 / -0.01 / -522 | 194 / +0.02 / -977 | 30 / -0.00 / +47 | 14 / -0.40 / -367 |
| USDCHF | 175 / -0.26 / -1,005 | 537 / -0.09 / -1,637 | 154 / -0.11 / -2,135 | 179 / -0.05 / -2,032 | 43 / -0.07 / -118 | 7 / +0.06 / +73 |
| USDJPY | 172 / -0.17 / -283 | 619 / -0.03 / -809 | 151 / -0.07 / -1,464 | 229 / +0.06 / +3,164 | 35 / +0.18 / +580 | 14 / +0.30 / +415 |
| XAUUSD | 68 / -0.18 / -122 | 189 / -0.07 / -72 | 143 / +0.32 / +3,497 | 365 / +0.05 / +5,081 | 58 / +0.46 / +2,354 | 13 / +0.85 / +972 |

## Per instrument (trailing-stop variant)

| instrument | 15m n / avgR / net USD | 1H n / avgR / net USD | 4H n / avgR / net USD | D n / avgR / net USD | W n / avgR / net USD | M n / avgR / net USD |
|---|---|---|---|---|---|---|
| AUDUSD | 302 / -0.39 / -3,125 | 620 / -0.22 / -2,249 | 162 / -0.08 / -1,949 | 176 / -0.25 / -12,349 | 28 / -0.04 / -113 | 7 / -0.15 / -85 |
| BTCUSD | 201 / -0.21 / -327 | 179 / +0.13 / -47 | 161 / +0.29 / +3,367 | 141 / +1.38 / +31,689 | 20 / +1.06 / +1,788 | 3 / +3.66 / +683 |
| EURUSD | 238 / +0.11 / -839 | 626 / -0.10 / -1,790 | 154 / +0.05 / +695 | 185 / +0.07 / +2,968 | 30 / +0.01 / -51 | 12 / -0.94 / -839 |
| GBPUSD | 251 / -0.14 / -2,168 | 591 / +0.01 / -709 | 137 / +0.27 / +2,245 | 182 / -0.06 / -975 | 33 / +0.04 / +60 | 10 / -0.17 / -67 |
| NZDUSD | 289 / -0.27 / -2,432 | 702 / -0.16 / -1,049 | 171 / -0.07 / -1,376 | 192 / +0.01 / -1,833 | 45 / -0.46 / -1,863 | 9 / -0.03 / +22 |
| USDCAD | 125 / +0.04 / +471 | 441 / -0.07 / -1,233 | 132 / +0.14 / +1,282 | 191 / +0.13 / -196 | 40 / -0.19 / -799 | 10 / -0.39 / -235 |
| USDCHF | 217 / -0.37 / -1,637 | 495 / -0.11 / -1,790 | 163 / -0.20 / -3,176 | 192 / -0.27 / -8,889 | 39 / -0.19 / -777 | 12 / -0.36 / -360 |
| USDJPY | 191 / -0.10 / +335 | 527 / -0.05 / -1,124 | 144 / -0.06 / -669 | 254 / -0.01 / +2,157 | 49 / -0.07 / -144 | 11 / +0.36 / +296 |
| XAUUSD | 37 / +0.04 / -19 | 105 / +0.09 / +98 | 120 / +0.45 / +3,492 | 277 / +0.16 / +7,085 | 40 / +0.97 / +2,890 | 7 / +0.71 / +487 |

## LEVEL 1 two-MA formula (per opportunity = position order + confirmation order, 1% risk budget)

| TF | MA pair | opportunities | orders (conf.) | win rate | avg R | t(avg R) | spread cost (R) | net USD | return | max DD | PF | skipped orders | random return mean [5–95%] | random avg R | share random ≥ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 15m | MA6/10 | 1070 | 1684 (614) | 18.7% | -0.119 | -4.33 | 0.150 | -7,375 | -73.8% | -77.3% | 0.55 | 81 | -70.8% [-78.9% – -64.4%] | -0.113 | 75% |
| 15m | MA10/20 | 574 | 937 (363) | 19.3% | -0.123 | -2.88 | 0.131 | -5,263 | -52.6% | -58.6% | 0.61 | 35 | -49.7% [-59.8% – -32.3%] | -0.118 | 50% |
| 1H | MA6/10 | 3691 | 5857 (2166) | 23.6% | -0.015 | -0.94 | 0.067 | -5,757 | -57.6% | -76.1% | 0.90 | 415 | -79.3% [-86.3% – -67.7%] | -0.042 | 0% |
| 1H | MA10/20 | 2113 | 3522 (1409) | 25.0% | +0.001 | +0.05 | 0.055 | -1,551 | -15.5% | -49.1% | 0.97 | 181 | -47.1% [-71.4% – -19.5%] | -0.029 | 5% |
| 4H | MA6/10 | 918 | 1474 (556) | 24.3% | -0.011 | -0.38 | 0.031 | -1,454 | -14.5% | -29.2% | 0.94 | 131 | -17.8% [-42.2% – +10.4%] | -0.022 | 35% |
| 4H | MA10/20 | 409 | 691 (282) | 26.7% | -0.094 | -2.40 | 0.028 | -3,323 | -33.2% | -42.6% | 0.70 | 92 | -21.7% [-32.9% – -7.9%] | -0.058 | 95% |
| D | MA6/10 | 749 | 1191 (442) | 25.4% | -0.025 | -0.92 | 0.010 | -1,998 | -20.0% | -39.8% | 0.88 | 337 | -7.3% [-20.7% – +18.4%] | -0.010 | 90% |
| D | MA10/20 | 363 | 604 (241) | 24.5% | +0.082 | +0.88 | 0.010 | +2,635 | +26.4% | -19.9% | 1.23 | 228 | +5.3% [-17.6% – +30.0%] | +0.018 | 15% |
| W | MA6/10 | 73 | 118 (45) | 24.7% | +0.204 | +1.32 | 0.005 | +1,518 | +15.2% | -5.1% | 2.03 | 147 | +4.8% [-6.2% – +15.3%] | +0.070 | 10% |
| W | MA10/20 | 20 | 33 (13) | 25.0% | -0.064 | -0.25 | 0.008 | -137 | -1.4% | -4.7% | 0.83 | 114 | +3.1% [-0.7% – +6.3%] | +0.147 | 95% |

**LEVEL 1 stability: first vs second half**

| TF | MA pair | H1 opps | H1 avg R | H1 PF | H2 opps | H2 avg R | H2 PF |
|---|---|---|---|---|---|---|---|
| 15m | MA6/10 | 500 | -0.149 | 0.53 | 570 | -0.093 | 0.61 |
| 15m | MA10/20 | 277 | -0.136 | 0.60 | 297 | -0.110 | 0.62 |
| 1H | MA6/10 | 1671 | -0.017 | 0.90 | 2020 | -0.014 | 0.91 |
| 1H | MA10/20 | 980 | +0.002 | 0.98 | 1133 | +0.001 | 0.96 |
| 4H | MA6/10 | 441 | +0.015 | 1.04 | 477 | -0.035 | 0.85 |
| 4H | MA10/20 | 220 | -0.093 | 0.71 | 189 | -0.095 | 0.68 |
| D | MA6/10 | 219 | +0.024 | 1.07 | 530 | -0.046 | 0.77 |
| D | MA10/20 | 92 | +0.089 | 1.29 | 271 | +0.080 | 1.21 |
| W | MA6/10 | 13 | -0.111 | 0.49 | 60 | +0.272 | 2.39 |
| W | MA10/20 | 2 | -0.572 | 0.00 | 18 | -0.007 | 0.97 |

**LEVEL 1 per instrument (opportunities / avg R / net USD)**

| instrument | 15m MA6/10 | 15m MA10/20 | 1H MA6/10 | 1H MA10/20 | 4H MA6/10 | 4H MA10/20 | D MA6/10 | D MA10/20 | W MA6/10 | W MA10/20 |
|---|---|---|---|---|---|---|---|---|---|---|
| AUDUSD | 139 / -0.14 / -1,390 | 81 / +0.04 / +317 | 462 / -0.08 / -2,387 | 253 / -0.03 / -832 | 109 / -0.09 / -947 | 47 / -0.11 / -523 | 67 / -0.13 / -871 | 38 / +0.05 / +132 | 7 / +0.22 / +138 | 1 / -0.29 / -28 |
| BTCUSD | 124 / -0.09 / -528 | 66 / -0.15 / -566 | 371 / +0.02 / +95 | 229 / +0.02 / +62 | 89 / +0.09 / +783 | 26 / -0.25 / -553 | 51 / +0.03 / +145 | 29 / +0.57 / +1,695 | 2 / +3.28 / +682 | 1 / -0.26 / -26 |
| EURUSD | 114 / -0.20 / -987 | 53 / -0.25 / -923 | 457 / +0.02 / -434 | 276 / -0.04 / -1,222 | 118 / -0.05 / -600 | 59 / -0.08 / -417 | 79 / -0.03 / -320 | 44 / +0.22 / +1,053 | 10 / -0.02 / -11 | 1 / -0.83 / -83 |
| GBPUSD | 125 / +0.04 / -89 | 75 / -0.01 / -281 | 454 / +0.02 / +187 | 253 / +0.04 / +755 | 126 / -0.00 / -56 | 59 / -0.16 / -904 | 82 / +0.05 / +503 | 45 / -0.14 / -688 | – | – |
| NZDUSD | 137 / -0.14 / -1,190 | 58 / -0.12 / -540 | 456 / -0.00 / -328 | 275 / -0.06 / -1,590 | 128 / -0.05 / -733 | 62 / -0.10 / -537 | 105 / -0.02 / -281 | 40 / -0.19 / -905 | 11 / -0.02 / -32 | 4 / -0.39 / -157 |
| USDCAD | 129 / -0.23 / -1,809 | 83 / -0.15 / -1,041 | 517 / -0.11 / -3,866 | 274 / +0.02 / -162 | 101 / -0.00 / -145 | 49 / -0.16 / -627 | 84 / -0.00 / -34 | 44 / +0.06 / +201 | 9 / +0.36 / +299 | 4 / +0.43 / +167 |
| USDCHF | 136 / -0.19 / -1,440 | 65 / -0.20 / -1,118 | 440 / -0.05 / -1,515 | 240 / +0.04 / +605 | 122 / +0.01 / +36 | 56 / -0.12 / -547 | 95 / -0.08 / -714 | 38 / -0.07 / -315 | 15 / -0.12 / -197 | 7 / -0.36 / -254 |
| USDJPY | 123 / -0.04 / +16 | 66 / -0.18 / -673 | 422 / +0.07 / +2,397 | 258 / +0.00 / +240 | 106 / -0.02 / -234 | 43 / +0.13 / +585 | 145 / -0.04 / -511 | 65 / +0.22 / +1,319 | 18 / +0.24 / +501 | 2 / +1.24 / +244 |
| XAUUSD | 43 / +0.01 / +42 | 27 / -0.22 / -438 | 112 / +0.01 / +93 | 55 / +0.13 / +593 | 19 / +0.25 / +442 | 8 / +0.29 / +200 | 41 / +0.02 / +85 | 20 / +0.07 / +142 | 1 / +1.37 / +137 | – |

## Method (what exactly was simulated)

**Data (Yahoo Finance, downloaded 2026-11-19):** EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD (`XXX=X`), XAUUSD
proxied by **gold futures GC=F** (roll gaps included), BTCUSD (`BTC-USD`). 15m = Yahoo limit **60 days → only ~2.5 months
of trading, statistically unreliable**; 1H = ~2.8 years (Feb 2024 → now; gold from Jul 2024, BTC from Nov 2024);
4H = resampled from 1H (same ~2.7 years); D = Yahoo max history (FX from 2003–2006, USDJPY 1996, gold 2000, BTC 2014);
W and M resampled from D. Bars with high/low inconsistent with open/close were clipped. The last (still forming) bar was
dropped. Yahoo FX daily data has occasional bad ticks; they were not removed.

**Signals (no lookahead):** at the close of bar i the app's own `phan_tich_khung` analyses the last 600 bars of the TF,
and the next larger frame (15m→1H, 1H→4H, 4H→D, D→W, W→M; M has none) using only data available at that moment.
For the 1H TF the 4H frame includes the forming 4H bar up to bar i (as the live app does); for the other TFs only
**completed** higher-frame bars are used (done to keep runtime within budget). Then `forex.ke_hoach_fx` gives BUY / SELL /
stand aside, SL (nearest swing ∓0.5 ATR, fallback 1.5 ATR) and TP = 3R exactly as in the app. The plan is re-evaluated
every bar on 4H/D/W/M and **every 2nd bar on 15m and 1H** (speed). First decision after 200 bars (W 100, M 60).

**Execution:** entry at the next bar's open; one position per instrument per TF; spread paid on entry
(EURUSD 1, GBPUSD 1.5, USDJPY 1, AUDUSD 1.2, USDCAD/USDCHF/NZDUSD 1.5 pips, XAU 30 points of 0.01, BTC 0.05% of price).
SL/TP are placed as **pip distances from the actual fill** (like the cBot reading `sl_pip/tp_pip`). Exit on SL/TP intrabar;
if both are touched in the same bar **SL is assumed first**; a gap through the level exits at the open. No swap/commission.
**Sizing:** `forex.khoi_luong` with 1% of current *balance* (compounding): lot = risk / (SL pips × pip value per lot),
floored to 0.01, min 0.01; the trade is **skipped** if actual risk > 1% (cBot rule). Pip value of USDJPY/USDCAD/USDCHF uses
the pair's own price at that moment. P&L converted to USD at exit price. All 9 instruments share one account per TF
(portfolio, several positions at once possible). Return and max drawdown use mark-to-market equity at every bar.
"Skipped" on 15m/1H is mostly *after* the account had collapsed (0.01 lot then risks > 1%).
**Trailing variant:** same entry and initial SL, no TP, stop trails the extreme since entry by 4·ATR(14), max hold 100 bars.
**Random baseline:** identical engine and entry bars (every bar where the app gave a Buy/Sell and the slot was free), but
direction by coin flip; same SL distance / 3R TP / sizing; 20 seeds. "Share random ≥" = fraction of random runs whose final
return ≥ the strategy's.
**R** = trade P&L / actual risk at entry. **t(avg R)** = mean R / standard error (|t| > 2 ≈ significant).
**Halves:** each TF's trading period split at its midpoint by entry time (no parameter was tuned on either half).

**LEVEL 1 two-MA formula (`l1.py`)** – operationalised from the course text:
* Signal MA / condition MA = SMA6/SMA10 or SMA10/SMA20 (both tested; the course's "choose by MA10 distance" rule not modelled).
* **Position order:** signal MA crossed above condition MA within the last 3 bars, and the bar closes bullish above both MAs;
  next-larger TF trend (app's `xu_huong` of the last completed higher bar) must be **up** (strictly in phase; mirror for SELL).
  SL = nearest swing low (fractal, 2 bars each side) below the condition MA within 40 bars (fallback lowest low of 10 bars).
* **Confirmation order (once):** while the position order is open and in profit, a further bullish close → enter next bar;
  SL = low of the most recent bar that dipped below the condition MA (if closer than 0.5 ATR, lowest low of 5 bars before it).
* **Risk:** 1% of balance per opportunity; position order 30% (0.3%), confirmation 70% (0.7%); cBot lot formula; an order is
  skipped if min lot would exceed its share.
* **Exits:** each order's SL intrabar; first close below the condition MA → close 50% of both orders at that close;
  signal MA crosses back below condition MA → close everything at that close. Same spread/fill conventions as above.
* **Random baseline:** same opportunity entry times and SL distances, random direction; MA-based exit bars are the same
  (they depend on the MAs, not on the position), SL mirrored. R per opportunity = P&L / 1% risk budget.
* TFs: 15m (optional), 1H, 4H, D, W (LEVEL 1 forex TFs). Opportunities start only when the higher-TF trend history exists
  (e.g. W needs M analysis ≥ 60 months → W trades from ~2008/2014).

## Caveats
* 15m (60 days) and the 1H/4H period (≈2.7 years, a strong gold/BTC uptrend) are short. D/W/M cover ~20 years but have
  few trades on W/M (100–300).
* Gold = futures continuous contract (roll jumps), BTC 24/7, Yahoo FX daily session boundaries ≈ UTC days.
* No swap, commission or slippage beyond the spread → real results would be somewhat worse.
* Exit assumptions are conservative (SL first). Results from a cloud Linux run; nothing was run in cTrader/TradingView.

## Files
* `trades.csv` – every trade (column `strategy` = app_plan / level1, `variant` = base / trail / L1_MA6/10 / L1_MA10/20).
* `equity_<TF>.csv` – app plan equity (base & trail) per TF; `equity_L1_<TF>.csv` – LEVEL 1 equity per TF.
* `results.json`, `results_l1.json` – all statistics incl. each random seed.

