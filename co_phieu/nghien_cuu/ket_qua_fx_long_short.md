# Backtest: symmetric LONG/SHORT "đồng pha + ADX" – forex, gold, crypto (10,000 USD, 1 % risk)

Run 2026-11-19. Rules: `SPEC.md`. Code: `core.py`, `sim.py`, `report.py`. All tables: `tables.md`. Excel: `ket_qua_fx_long_short.xlsx`.
Headline config (fixed before running, user's choice): regime ON, ADX(14) of TF+1 ≥ 25 with DI in the trade direction, no take-profit.

## Verdict (plain)

* **No edge was found on any timeframe or asset class.** On the TEST period (last 40 % of each TF's history, nothing chosen on it),
  the headline strategy beat at most 86–92 % of random-entry runs (same eligible bars, same stops/exits/sizing) – never ≥ 95 % – and
  no TEST t-statistic of avg R reaches 2. Where it lost, random entries usually lost the same way.
* **Forex majors lose on every TF ≥ 1H** (TEST: 1H −4.7 %, 4H −13.1 %, D −5.6 % over 10.7 years, W −2.8 %). 15m was +3.6 % in
  one month (26 trades) – exactly the random average.
* **Gold: too few trades to say anything** (TEST 0–9 trades per TF). D gold lost in both halves and was worse than 98 % of random runs
  (−0.45 R/trade over 22 years); buy & hold gold made +10 %/yr.
* **Crypto D is the only cell positive in TRAIN and TEST** (TEST 26 trades, +0.66 R, +14 % in 3.5 years = +3.9 %/yr, max DD −14 %), but
  random entries on the same bars did the same (52nd percentile) and BTC buy & hold made +27.5 %/yr (with −53 % DD). The filter
  (đồng pha + regime) carries the result, not the 2MA / MACD-Sto trigger. Crypto 1H: TEST +1.2 % vs random average +26 % (worst of 200).
  Crypto 4H TEST: 16 trades, 0 winners, −13.6 %.
* **It trades very rarely.** All three timeframes plus ADX ≥ 25 plus the regime leave e.g. ~2 trades/year on D for 7 FX pairs together,
  0.7/yr on W, 0.8/yr on gold D. Returns are therefore tiny in both directions (D/W CAGR between −0.5 % and +3.9 %).
* **Regime filter: no consistent benefit.** ADX 25, TEST, regime ON vs OFF: better in 7 of 15 TF×class cells, worse in 6, equal in 2.
  **ADX threshold: no consistent pattern** (off/20/25/30 change the trade count much more than the result; for crypto D, ADX off was best).
  Of the 16 variants, the one best on TRAIN lost money on TEST in 9 of 14 cases.
* **Long vs short:** no side is reliably better. Shorts were positive in some cells (forex 15m train, crypto 15m/D), negative in others
  (crypto 1H TEST −0.30 R, gold D −0.94 R). Sample sizes per side are 0–100 trades.
* **3R take-profit variant:** same picture (TEST crypto 1H improves to +33 % but that equals random; forex 1H −10.6 %).
* **No account was wiped out**, but the headline lost −42 % peak-to-trough on forex 1H (FULL, 2.8 years), and without the ADX filter
  crypto 15m and forex 1H fell to 48–49 % of start (max DD −52…−56 %) – flagged "hỏng nặng". Small DDs elsewhere come from
  1 % risk and very few trades, not from the strategy working.
* **Bottom line: do not trade this with real money on the strength of this test.** At best it is a low-frequency trend filter whose
  results are indistinguishable from random entries inside the same filter; on forex it loses after spread.

## Data per timeframe (Yahoo Finance; Binance blocked from this environment → no longer intraday crypto history)

| trade TF | bigger TFs used | tradable span (forex / gold / crypto) | TRAIN / TEST split |
|---|---|---|---|
| 15m | 1H, 4H | 2026-08-28 / 09-11 / 09-21 → 2026-11-19 (**~2–3 months**) | ~5–7 weeks / ~4 weeks |
| 1H | 4H, D | 2024-02 / 2024-07 / 2024-11 → 2026-11 (**~2–2.8 yrs**) | 2025-10 / 2025-12 / 2026-02 |
| 4H | D, W | same as 1H (4H built from 1H) | same |
| D | W, M | 2000 (USDJPY; others 2007–09) / 2004 / 2018 (BTC; other coins 2021–23) → 2026-11 | 2016-03 / 2017-09 / 2023-05 |
| W | **M only** (no TF above M) | same as D | same |

## Headline – TEST period (regime ON, ADX ≥ 25, no TP)

| TF | class | trades | win | avg R | PF | return / CAGR | max DD | final USD | long n / avgR | short n / avgR | random pct [mean final] | buy & hold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 15m | forex | 26 | 31% | +0.15 | 1.26 | +3.6% tot | −6% | 10,360 | 8 / +0.77 | 18 / −0.12 | 53% [10,366] | – |
| 15m | gold | 5 | 40% | +0.72 | 2.58 | +3.0% tot | −2% | 10,300 | 0 | 5 / +0.72 | 32% [10,529] | XAU −9.8% tot |
| 15m | crypto | 21 | 29% | +0.43 | 1.80 | +8.2% tot | −14% | 10,816 | 12 / −0.49 | 9 / +1.64 | 86% [10,205] | BTC −21% tot |
| 1H | forex | 91 | 33% | −0.04 | 0.90 | −4.3%/yr | −21% | 9,530 | 39 / −0.01 | 52 / −0.06 | 37% [9,960] | – |
| 1H | gold | 9 | 22% | +0.19 | 1.45 | +2.0% tot | −4% | 10,205 | 3 / −0.78 | 6 / +0.67 | 62% [10,048] | XAU −11% tot |
| 1H | crypto | 62 | 23% | +0.07 | 1.03 | +1.2% tot | −29% | 10,120 | 13 / +1.49 | 49 / −0.30 | **0%** [12,586] | BTC −20% tot |
| 4H | forex | 37 | 19% | −0.37 | 0.50 | −11.9%/yr | −17% | 8,690 | 16 / −0.49 | 21 / −0.28 | 28% [8,935] | – |
| 4H | gold | 2 | 0% | −1.00 | 0 | −1.6% tot | −6% | 9,836 | 1 / −1.00 | 1 / −1.00 | 72% [9,778] | XAU −11% tot |
| 4H | crypto | 16 | 0% | −0.91 | 0 | −13.6% tot | −17% | 8,641 | 10 / −1.00 | 6 / −0.77 | 68% [8,551] | BTC −17% tot |
| D | forex | 22 | 23% | −0.29 | 0.60 | −0.5%/yr | −10% | 9,443 | 11 / −0.40 | 11 / −0.18 | 10% [10,526] | – |
| D | gold | 7 | 14% | −0.34 | 0.43 | −0.3%/yr | −4% | 9,712 | 6 / −0.23 | 1 / −1.00 | 2% [9,971] | XAU +12.3%/yr, DD −30% |
| D | crypto | 26 | 38% | +0.66 | 2.00 | +3.9%/yr | −14% | 11,428 | 21 / +0.55 | 5 / +1.09 | 52% [11,418] | BTC +27.5%/yr, DD −53% |
| W | forex | 7 | 0% | −0.62 | 0 | −0.3%/yr | −3% | 9,722 | 2 / −1.03 | 5 / −0.46 | 15% [9,867] | – |
| W | gold | 0 | – | – | – | 0 | 0 | 10,000 | 0 | 0 | – | XAU +12.7%/yr |
| W | crypto | 13 | 38% | −0.11 | 0.75 | −0.4%/yr | −7% | 9,843 | 11 / −0.04 | 2 / −0.55 | 75% [9,700] | BTC +28.6%/yr, DD −53% |

TRAIN, FULL, the 3R-TP variant, the regime × ADX grid, per-symbol results, year-end equity and swap sensitivity are in `tables.md`
(and the Excel sheet `Tong_hop`). "random pct" = share of 200 random-entry runs ending with less or equal equity than the strategy.

## Regime and ADX (TEST final equity, no TP; from 10,000)

| TF | class | reg ON: ADX off / 20 / 25 / 30 | reg OFF: ADX off / 20 / 25 / 30 |
|---|---|---|---|
| 1H | forex | 11,277 / 9,328 / 9,530 / 10,246 | 11,877 / 9,680 / 8,988 / 10,350 |
| 1H | crypto | 11,780 / 10,316 / 10,120 / 10,702 | 15,525 / 10,703 / 10,809 / 11,493 |
| 4H | forex | 8,230 / 8,756 / 8,690 / 8,514 | 8,940 / 9,411 / 8,815 / 8,118 |
| 4H | crypto | 8,175 / 8,573 / 8,641 / 8,641 | 6,929 / 7,976 / 8,428 / 8,516 |
| D | forex | 7,769 / 8,723 / 9,443 / 9,681 | 7,425 / 9,188 / 9,779 / 9,331 |
| D | crypto | 16,836 / 11,926 / 11,428 / 10,090 | 21,849 / 11,863 / 11,436 / 10,008 |
| W | forex | 9,880 / 10,149 / 9,722 / 9,719 | 9,166 / 10,260 / 9,604 / 9,729 |

On D forex a higher ADX threshold mainly means fewer losing trades (fewer trades in total), not positive results.

## Costs, swap
Spreads as in `../bt_fx` (EURUSD/USDJPY 1 pip … gold 30 points, BTC/ETH 0.05 %, other coins 0.10 %). Swap was 0 in the main runs;
charging 2 %/yr (forex), 4 %/yr (gold), 20 %/yr (crypto CFD) of notional lowers TEST finals by 0–4 % of the account
(e.g. crypto D 11,428 → 10,995; forex 1H 9,530 → 9,212). Real swaps differ by broker and direction.

## Caveats
* **Short intraday history**: 15m = ~2–3 months (TEST ≈ 4 weeks), 1H/4H ≈ 2–2.8 years. Results there are anecdotes, not evidence.
* **Very few trades** on D/W and on gold (single digits per period) → wide uncertainty; a few trades decide the sign.
* **Survivorship**: the coin list (ETH, BNB, SOL, XRP, DOGE, ADA) is today's large caps; dead coins are absent → crypto results are biased up.
* **Yahoo data quality**: FX daily has occasional bad ticks; gold = GC=F futures (roll gaps); FX/gold day close assumed at 00:00 UTC
  (conservative by ~2 h); timestamps UTC.
* **Account size**: with 10,000 USD, 0.01 lot of gold (1 oz) often risks > 1 % on D/4H/W stops → those signals were skipped (7 on gold D,
  15 on gold 4H; see `tables.md`). No margin/leverage limit modelled; no commission or slippage beyond the spread.
* Stops are checked on X bars (not tick data); if stop and TP fall in one bar the stop is assumed first.

## Three example trades (check on a chart; times UTC, bar = opening time)
1. **LONG, signal exit** – XAUUSD D: signal bar 2020-06-16 (đồng pha D/W/M up, ADX W ≥ 25, DXY below SMA200 → longs allowed),
   filled 2020-06-17 at 1735.6, stop 1671.7 (swing low), lot 0.01, risk 64 USD; MACD+Sto sell signal on the weekly bar →
   exit at the open of 2020-08-17 at 1956.4 → +221 USD = +3.46 R.
2. **SHORT, signal exit** – ADAUSD D: signal bar 2026-01-18 (bearish candle, MA5 crossed below MA10; D/W/M DOWN; ADX(W) 31.4,
   DI− 29.1 > DI+ 15.0; BTC below SMA200 → shorts only), sold 2026-01-19 at 0.375669, stop 0.42665 (swing high), 2,470.39 coins,
   risk 126 USD; mirrored (buy-type) MACD+Sto signal on W → covered at the open of 2026-03-02 at 0.273957 → +251 USD = +2.00 R.
3. **Stop** – XAUUSD 4H SHORT: signal bar 2026-07-01 04:00 (bearish, 2MA cross-down, 4H/D/W down, ADX(D) 38), sold at the
   08:00 open 3988.8, stop 4078.1, lot 0.01; the 12:00 bar's high 4131 hit the stop → −89 USD = −1.00 R.
