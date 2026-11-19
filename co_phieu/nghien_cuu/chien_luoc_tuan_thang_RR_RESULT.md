# Month + Week trend consensus, daily timing, tight stop, 1:10–1:30 targets — portfolio backtest (2026-11-19)

## Verdict (read this first)
- **The strategy does not work out of sample.** The variant chosen on 2008–2019 (best of 330) made **+15.0 %/yr in TRAIN but −1.3 %/yr in TEST 2020-01 → 2026-11-17** (total −8.5 %, max drawdown −43 %).
  In the same TEST period an equal-weight basket of liquid stocks made **+8.5 %/yr** (total +75 %, max DD −60 %).
  It is **worse than buy & hold** in TEST. It is a bit better than the current app rule (−3.0 %/yr).
- The TRAIN result looks good only because the TRAIN market was very bad (EW basket −8.9 %/yr) and the M/W filter kept the strategy in cash in 2008–2012. It does not show skill: across all 330 variants, the TRAIN rank barely predicts the TEST rank (Spearman 0.13). The median variant made −0.4 %/yr in TEST, and only 13 of 330 (3.9 %) beat the EW basket.
- **Tight stop + 1:10–1:30 target behaves as expected: very low win rate.** Targets were hit about as often as needed to break even, and no more:
  10–15R: 10 %, 15–20R: 8 %, 20–30R: 2–5 %, fixed 10R/20R/30R: 10 % / 5 % / 2–3 %. Break-even before fees is roughly 1/(1+R:R) = 9 % / 5 % / 3 %.
  The best variant won 12.5 % of trades in TEST; the median trade is −1.13R; 87 % of trades end at the initial stop.
- The **Month + Week consensus filter did not help in TEST**. With the same entry and exit, TEST CAGR was −1.3 % with the M+W filter, −0.5 % with the M filter only, and **+6.0 %** with no filter (TRAIN: 15.0 / 8.4 / 6.3 %).
  The filter only reduced the TRAIN drawdown, which mostly came from 2008–2011.
- Structure targets (previous weekly/monthly swing high, Fibonacci 1.272/1.618 of the last weekly/monthly swing) with the 10–30 R:R filter were **worse than plain fixed-R targets** in TRAIN. They also produce few trades, because most structure targets give R:R < 10.
- A 4·ATR trailing stop did not improve the best variants in TRAIN (median over the grid: same) and did not help in TEST.

## Setup
- Data: `features_full.pkl`, 891 stocks (delisted stocks are missing, so **survivorship bias** makes every number, including the benchmarks, optimistic). Daily adjusted OHLC, no volume.
  Dates per bar were rebuilt from the tool rows (exact for 98 % of liquid bars from 2011; before 2010 they are approximate to within a few days).
- Universe/liquidity: a bar is tradable only if a tool row with 20-day traded value ≥ 1 bn VND exists within the last 10 bars (rows exist only for liquid stocks).
- **M/W consensus**: the app's `phan_tich_khung(frame, 'M'/'W').xu_huong == 1` on **the last COMPLETED monthly and weekly bar** (week W-FRI, calendar month; a bar counts as complete at the close of its last session). There is no partial bar, so no lookahead.
  Weekly frame = last 150 weekly bars (gives the same result as full history in a check). Monthly frame = full history, and fewer than 40 months means no trend, i.e. no trade.
  Volume = 0, so the app's MFI vote is skipped (no volume in the data).
- Daily triggers (signal at close t, buy at **open t+1**):
  E1 = close crosses above the last confirmed daily swing high (pivot k=3).
  E2 = a **higher daily swing low** (pivot k=3) is confirmed today and today's close > yesterday's close.
  E3 = close crosses above EMA20.
- Stops:
  `sw2`/`sw5` = last confirmed daily swing low (k=3, used only 3 bars after the pivot) − 0.2/0.5 ATR(14). The trade is skipped if the open gaps to less than ½ of the planned risk.
  `p2`/`p3`/`p5` = 2/3/5 % below the fill.
  Stop first if a bar touches both; a gap through the stop fills at the open.
- Targets:
  TW/TM = most recent confirmed weekly/monthly swing high (k=2) above the price.
  F127/F162 = A + 1.272/1.618·(B − A), where B = last confirmed weekly swing high and A = the swing low before it. F127M/F162M = the same on monthly bars.
  ANY = the nearest of these six. The structure variants keep a trade only if 10 ≤ (target − close)/(close − stop) ≤ 30.
  Also tested: fixed 10R/20R/30R from the fill, and NONE.
  Each target was run with or without a trailing stop of 4·ATR below the highest high since entry (applied from the next bar). Max hold is 250 bars.
- Portfolio: 1,000,000,000 VND, risk 1 % of equity (at the previous close) per trade, `shares = floor(risk/(fill−stop)/100)·100`, capped at 20 % of equity per position and by cash (no margin).
  One position per ticker. Signals each day are processed by (M score + W score) descending.
  Fees: buy 0.15 %, sell 0.15 % + 0.1 % tax. Not modelled: ceiling/floor lock-outs, price ticks.
- Split: parameters were chosen **only on TRAIN 2008-01 → 2019-12** (fresh capital, open positions closed 2019-12-31). **TEST 2020-01 → 2026-11-17** was run once with fresh capital. FULL = one continuous run from 2008.
- Grid: 3 entries × 5 stops × 11 targets × 2 trailing options = **330 variants**. The best was chosen by TRAIN CAGR.
- Baselines:
  (a) equal-weight basket of all liquid stocks, bought on the first session of each year and held to year end (fees paid).
  (b) index proxies: daily-rebalanced equal-weight index, and a traded-value-weighted index (there is no real VNINDEX in the data; cap weights are not available).
  (c) the current app rule: tool rows with muc Mua/Mua mạnh, buy next open, stop = zone − 0.5 ATR (else −1 ATR), TP 3R, 60 bars, same sizing.
  Caveat: tool rows exist only every 10 bars, so (c) sees about 1/10 of daily signals.

## Chosen variant (by TRAIN): **E2 + 3 % stop + fixed 10R target (= +30 %), no trailing, max 250 bars**
With a 3 % stop, the 20 % position cap always binds. In practice this is "up to 5 positions of 20 %", and the real risk is 0.6 % of equity per trade.

### TEST 2020-01-01 → 2026-11-17 (out of sample)
| | CAGR | total | max DD | trades | win | avg R | median R | avg hold (bars) | target hit | exposure |
|---|---|---|---|---|---|---|---|---|---|---|
| **Chosen strategy** | **−1.3 %** | −8.5 % | −43.2 % | 773 | 12.5 % | +0.12 | −1.13 | 15.0 | 11.4 % | 84 % |
| (c) current app rule | −3.0 % | −18.9 % | −57.9 % | 798 | 29.7 % | −0.02 | −1.05 | 17.3 | 25.1 % | 75 % |
| (a) EW liquid basket, yearly | **+8.5 %** | +75.1 % | −59.7 % | – | – | – | – | – | – | 100 % |
| (b) EW daily index | +7.6 % | +66.0 % | −67.0 % | – | – | – | – | – | – | 100 % |
| (b) traded-value-weighted index | +4.1 % | +32.0 % | −68.0 % | – | – | – | – | – | – | 100 % |

### TRAIN 2008-01-01 → 2019-12-31 (in sample, used for selection)
| | CAGR | total | max DD | trades | win | avg R | avg hold | target hit | exposure |
|---|---|---|---|---|---|---|---|---|---|
| Chosen strategy | +15.0 % | +435 % | −21.0 % | 566 | 17.8 % | +0.75 | 18.3 | 17.0 % | 49 % |
| (c) app rule | −2.1 % | −22.4 % | −40.3 % | 613 | 29.2 % | −0.01 | 17.4 | 26.3 % | 44 % |
| (a) EW basket | −8.9 % | −67.5 % | −82.2 % | | | | | | |
| (b) EW daily / value-weighted | −9.3 % / −14.7 % | −69 % / −85 % | −84 % / −88 % | | | | | | |

### FULL 2008-01 → 2026-11-17 (one continuous run; mostly in-sample, do not read it as a forecast)
| | CAGR | total | max DD | trades | win | avg R | target hit | exposure |
|---|---|---|---|---|---|---|---|---|
| Chosen strategy | +9.8 % | +480 % | −35.4 % | 1,366 | 14.2 % | +0.34 | 13.4 % | 62 % |
| (c) app rule | −2.3 % | −35.4 % | −56.7 % | 1,411 | 29.1 % | −0.03 | 25.2 % | 55 % |
| (a) EW basket | −2.9 % | −43.0 % | −82.2 % | | | | | |
| (b) EW daily / value-weighted | −3.5 % / −8.3 % | −49 % / −81 % | −84 % / −90 % | | | | | |

### Per-year returns (FULL run; 2026 = to 17 Nov)
| year | strategy | app rule | EW basket | EW daily idx | value-w idx |
|---|---|---|---|---|---|
| 2008 | 0.0 % | −9.6 % | −72.0 % | −75.3 % | −75.7 % |
| 2009 | −3.8 % | +8.2 % | +72.7 % | +81.2 % | +64.8 % |
| 2010 | −9.9 % | −18.2 % | −17.9 % | −18.6 % | −24.7 % |
| 2011 | −4.4 % | −9.5 % | −52.9 % | −53.8 % | −56.2 % |
| 2012 | +1.1 % | +4.9 % | +15.5 % | +16.9 % | +7.8 % |
| 2013 | +57.0 % | +1.3 % | +9.5 % | +23.9 % | +18.1 % |
| 2014 | +27.5 % | +35.6 % | +24.2 % | +14.0 % | +6.6 % |
| 2015 | +8.7 % | −15.5 % | −4.7 % | +4.1 % | −7.3 % |
| 2016 | +48.3 % | −7.5 % | −1.7 % | −7.9 % | −20.7 % |
| 2017 | +55.5 % | +25.8 % | +32.4 % | +32.1 % | +28.2 % |
| 2018 | +9.5 % | −17.6 % | −11.7 % | −13.7 % | −12.8 % |
| 2019 | +16.1 % | −8.3 % | +1.5 % | +1.4 % | −0.1 % |
| 2020 | −3.2 % | +17.0 % | +39.7 % | +43.8 % | +35.7 % |
| 2021 | +24.9 % | +53.8 % | +95.7 % | +107.6 % | +74.2 % |
| 2022 | −15.2 % | −32.1 % | −50.8 % | −57.4 % | −59.2 % |
| 2023 | −4.9 % | −4.8 % | +25.1 % | +25.4 % | +30.0 % |
| 2024 | +12.7 % | +6.6 % | +8.2 % | +18.4 % | +14.2 % |
| 2025 | +24.8 % | −5.5 % | +12.3 % | +18.5 % | +31.8 % |
| 2026 | −20.9 % | −28.9 % | −14.6 % | −25.7 % | −30.1 % |

TEST-only run of the strategy (fresh capital in 2020): 2020 −1.2 %, 2021 +29.1 %, 2022 −16.2 %, 2023 −4.3 %, 2024 +3.1 %, 2025 +18.8 %, 2026 −26.9 %.
It beat the EW basket only in 2022 (by losing less) and 2025.

## Best variant of each target family (chosen on TRAIN) and its TEST result
| target | entry | stop | trail | TRAIN CAGR | TRAIN DD | TRAIN trades | TRAIN hit | **TEST CAGR** | TEST DD | TEST trades | TEST win | TEST hit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed 10R | E2 | 3 % | – | 15.0 % | −21 % | 566 | 17.0 % | **−1.3 %** | −43 % | 773 | 12.5 % | 11.4 % |
| fixed 30R | E2 | 3 % | 4 ATR | 12.1 % | −30 % | 621 | 1.1 % | **−2.6 %** | −55 % | 867 | 16.8 % | 0.8 % |
| fixed 20R | E2 | 3 % | – | 11.8 % | −35 % | 440 | 8.4 % | **+5.5 %** | −50 % | 569 | 9.7 % | 6.9 % |
| structure ANY, R:R 10–30 | E2 | 2 % | 4 ATR | 11.8 % | −28 % | 664 | 10.4 % | **−2.4 %** | −48 % | 997 | 12.7 % | 7.0 % |
| no target, trailing only | E2 | swing − 0.2 ATR | 4 ATR | 11.1 % | −32 % | 592 | – | **−0.7 %** | −54 % | 766 | 27.7 % | – |
| Fib 1.618 weekly | E2 | 2 % | 4 ATR | 7.9 % | −21 % | 414 | 8.9 % | −5.7 % | −57 % | 691 | 13.6 % | 6.4 % |
| prev monthly high | E2 | 2 % | 4 ATR | 6.2 % | −25 % | 243 | 9.5 % | −4.7 % | −51 % | 469 | 10.4 % | 5.1 % |
| Fib 1.618 monthly | E3 | 2 % | 4 ATR | 5.3 % | −24 % | 682 | 6.0 % | −1.9 % | −49 % | 923 | 14.6 % | 4.6 % |
| Fib 1.272 monthly | E2 | 2 % | 4 ATR | 1.7 % | −13 % | 245 | 6.9 % | +1.5 % | −46 % | 472 | 12.5 % | 6.8 % |
| prev weekly high | E2 | swing − 0.5 ATR | – | 1.1 % | −9 % | 8 | – | −1.1 % | −18 % | 25 | 8 % | 4 % |
| Fib 1.272 weekly | E2 | swing − 0.5 ATR | – | 0.8 % | −7 % | 12 | – | −2.7 % | −25 % | 49 | 8 % | 6 % |

Grid medians (330 variants): TRAIN +0.7 %/yr, TEST −0.4 %/yr. Best TEST variants (post-hoc, for information only) all had weak TRAIN results (0–5 %/yr), so they could not have been picked.
Entry E2 (higher swing low) was the best trigger in both periods. Swing-low stops held up slightly better in TEST than % stops (grid median +0.6 to +1.3 %/yr vs −1.9 to −3.5 %/yr).

## Do the M/W consensus filter and the targets add anything? (same entry and exit, TRAIN | TEST CAGR)
| filter | E2 + 3 % stop + 10R | E2 + swing stop + 4 ATR trail |
|---|---|---|
| Month AND Week up (spec) | 15.0 % \| −1.3 % | 11.1 % \| −0.7 % |
| Month up only | 8.4 % \| −0.5 % | 11.4 % \| −4.8 % |
| no trend filter | 6.3 % \| **+6.0 %** | 13.7 % \| +0.8 % |

## How often are 1:10–1:30 targets reached? (all candidate trades, every entry and stop, pooled, no portfolio limits)
| R:R bucket | TRAIN n | TRAIN target hit | TEST n | TEST target hit | TEST win | TEST avg R | median hold |
|---|---|---|---|---|---|---|---|
| structure target, R:R 10–15 | 10,469 | 9.6 % | 23,213 | 9.8 % | 10.8 % | +0.12 | 4 bars |
| structure target, R:R 15–20 | 2,282 | 7.2 % | 5,276 | 7.7 % | 8.4 % | +0.18 | 3 |
| structure target, R:R 20–30 | 595 | 2.0 % | 1,425 | 4.8 % | 6.3 % | −0.05 | 3 |
| fixed 10R | 36,321 | 10.9 % | 81,163 | 10.1 % | 14.9 % | +0.16 | 10 |
| fixed 20R | 36,321 | 4.5 % | 81,163 | 4.8 % | 12.1 % | +0.28 | 10 |
| fixed 30R | 36,321 | 2.3 % | 81,163 | 2.8 % | 11.3 % | +0.33 | 10 |

The average per-trade return is about 0 % (−0.2 % to +2 %). A small positive average R comes from a few large winners. With fees, sequencing and the 20 % cap, it does not turn into portfolio profit in TEST.
Most trades are stopped out within 3–10 sessions: a 2–3 % stop (or a swing low a few % away) sits inside normal daily noise (median daily ATR ≈ 3–4 %).
For the chosen variant in TEST, 87 % of trades ended at the initial stop and 11.4 % at the target.

## Caveats
- 330 variants were tested and the best was picked on TRAIN. The TRAIN numbers are optimistic by construction.
- Survivorship bias: delisted stocks are missing. Prices are adjusted. Dates before 2010 are approximate. There is no real VNINDEX, only proxies.
- Data until 2026-11-17. 2026 is a partial year.
- The M/W trend uses the app's scoring without the MFI vote (no volume). With real volume the app's W/M labels can differ slightly.
- Not modelled: ceiling/floor lock (stops can fill worse than modelled on floor days), T+2 settlement, slippage.

## Files
- `SPEC.md`: exact rules of the chosen variant (plus the optional structure-target and trailing rules).
- `equity_best_full.csv`, `equity_best_test.csv`: strategy equity (date, equity).
- `equity_app_*.csv`, `equity_bh_ew_yearly_*.csv`, `equity_idx_ew_daily_*.csv`: baselines.
- Code: `prep.py` (dates, M/W trend, targets), `bt.py` (engine), `run_all.py` (grid → `all.pkl`, `table.pkl`), `baselines.py`, `analyze.py`.
