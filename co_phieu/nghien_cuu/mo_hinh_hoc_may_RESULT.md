# Does anything beat random / buy-and-hold for VN stocks? (research 2026-11-19)

## Setup
- Data: `features_full.pkl` (891 stocks, delisted excluded → survivorship bias). Calendar complete only from 2010,
  so the study runs 2010-01 → 2026-11. Panel: every 10 trading days, every stock with a tool row with
  20-day avg traded value ≥ 1 bn VND within the last 10 bars (= "liquid universe", 30–520 stocks/date).
  80,784 rows, 421 dates. Price-to-date mapping checked (stock-level corr of forward vs. later realised return 0.992).
- Features at bar i only (returns 1–250d, 12-1/6-1 momentum, distance to 52w high/low, vol 20/60, MA20/50/200
  position & slope, gaps, limit-up/down counts, MAX, skew, ATR%, log traded value, tool scores), cross-sectional
  percentile ranks per date, market medians/breadth.
- Target: return from **open i+1** to close i+H (H = 20, 60), **net of fees** (0.15% buy, 0.15% sell + 0.1% tax).
  Picks locked at the ceiling the next day (unbuyable) are skipped.
- Split: train 2010–2016 (175 dates), validate 2017–2019 (75), **TEST 2020-01-01 → 2026-11 (171 dates)**,
  touched only once for the pre-selected candidates. Training rows whose target window crosses a split are purged.
- Portfolio test: every H days (non-overlapping) buy top-N (10 or 30) equal weight, hold H days. Baseline = equal
  weight of ALL liquid stocks the same day (the "random" portfolio, also pays fees). Numbers averaged over the
  H/10 staggered start offsets. ~85 periods for H=20, ~27 for H=60. Excess = portfolio − baseline per period.

## Baselines, TEST 2020–2026 (per 20-day period, net of fees)
| | mean return | note |
|---|---|---|
| EW all liquid stocks (baseline) | +0.72% | cum +35%, max DD −54% |
| Median stock (VNINDEX-like proxy) | −0.75% | returns are right-skewed: most stocks lag the average |
| Random top-10 | +0.79% (excess +0.07%, t 0.17) | sanity check |

## TEST results (H=20, top-10, every 20 days)
| candidate | how chosen | excess/20d | hit vs base | t | max DD | years >0 |
|---|---|---|---|---|---|---|
| Tool buy signal (all "Mua/Mua mạnh") | current tool | **−0.94%** | 39% | −1.46 | −58% | 1/7 |
| Tool score, top-10 | current tool | +0.38% | 54% | 0.56 | −59% | 4/7 |
| Near 52-week high, top-10 | best simple rule on train+valid (t 2.4 / 3.2) | +0.12% | 49% | 0.16 | −54% | 4/7 |
| same, top-30 | | +0.59% | 55% | 1.20 | −42% | – |
| 52w-high + low-vol rank | 2nd best on valid (t 3.7) | −0.11% | 50% | −0.12 | −24% | 4/7 |
| 12-1 momentum | classic anomaly | −1.11% | 43% | −1.53 | −81% | 2/7 |
| LightGBM, all features, fixed (trained ≤2019) | tuned on valid | +1.06% | 60% | 1.67 | −23% | 5/7 |
| **LightGBM, all features, yearly retrain** | walk-forward | **+1.07%** | **64%** | **2.09** (2.70 / ~1.5 by offset) | −46% | **7/7** |
| LightGBM, price only, yearly retrain | walk-forward | +0.99% | 63% | 1.79 | −51% | 6/7 |
| Deploy variant B (price + ranks + market, no age) * | post-hoc | +1.15% | 61% | 1.90 | −49% | 6/7 |
| Deploy variant A (single-stock price only) * | post-hoc | +1.02% | 60% | 1.69 | −29% | 5/7 |

\* variants A/B were defined after seeing the test (dropped hard-to-reproduce features); treat as optimistic.

H=60 (top-10, ~27 periods): tool buy signal −2.5%/60d (t −1.24); near-52w-high +0.6% (t 0.24);
LightGBM yearly retrain +1.6–1.7% (t 0.9–1.1). Nothing is significant at 60 days.

Per-year excess, H=20 top-10 (%):
| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| Tool buy signal | −3.03 | −1.98 | 1.12 | −0.79 | −1.02 | −0.44 | −0.53 |
| Tool score top-10 | −1.40 | 1.20 | −0.61 | −1.94 | 2.96 | 1.14 | 1.44 |
| Near 52w high | −1.17 | 1.10 | 1.51 | −2.12 | 1.68 | 0.22 | −0.34 |
| LGB all, yearly | 0.17 | 0.54 | 2.03 | 0.59 | 1.87 | 1.16 | 1.19 |
| LGB price, yearly | −0.95 | 0.91 | 2.26 | 0.32 | 1.88 | 1.14 | 1.55 |
| Variant B | 0.76 | 0.10 | 2.79 | −0.17 | 1.66 | 1.70 | 1.32 |

Walk-forward 2017–2026 (10 years, yearly retrain, top-10/20d): LGB all +1.32%/20d, hit 66%, 10/10 years
positive, t ≈ 3.2 per offset; near-52w-high +0.63% (t 1.6); tool score +0.72% (t 1.9); random +0.25% (t 1.0).

Calibration on TEST (score decile per date → mean 20d excess): LightGBM (price, fixed) is monotonic-ish:
D1 −1.5%, D2 −0.7%, D3 −0.5%, D4 −0.3%, D5 −0.1%, D6 +0.5%, D7 +0.5%, D8 +0.6%, D9 +0.5%, D10 +1.0%.
The bottom decile is the most reliable (it is avoided). Even in D10 a stock beats the average only ~51% of
the time — the edge is in the mean, so it needs ≥10 stocks. The current tool score has **no** monotonic
relation (D1 −0.35%, D10 +0.25%, hit ~43–45% flat). Model importance: distance to 52w high (rank), 60d
volatility (low is better), listing age, ATR%, gaps, market 20/60d return.

## Robustness / caveats
- Liquidity: restricting picks to ≥ 10 bn VND/day weakens everything (LGB +0.45–0.9%, t 0.7–1.6).
  Much of the edge is in smaller (1–10 bn/day) stocks where slippage is larger than modelled.
- 2022 contributes the most; without it test excess ≈ +0.8%/20d.
- Excess is vs. an EW basket that also pays fees each period. Versus a passive, never-rebalanced basket
  subtract ≈ 0.4%/period of turnover cost → net edge ≈ +0.6%/20d at best.
- ~20 simple rules and ~10 ML variants were looked at; a t ≈ 2 after this much search is weak evidence.
  Simple rules that looked strong in 2010–2019 (52w high, t 2.4/3.2) failed out of sample.
- Survivorship: delisted stocks are missing (likely make true baseline lower; effect on excess unclear).
- Tool features are up to 9 bars stale in this panel (tool was sampled every 10 bars).

## Verdict
- **The current tool's buy signal does not beat random; it is slightly worse** (−0.9%/20d vs the
  equal-weight liquid basket, 1 of 7 test years positive). Tool score ranking ≈ random.
- **Simple momentum / 52-week-high rules: no robust out-of-sample edge** (strong 2010–19, ~0 in 2020–26).
- **Only a cross-sectional LightGBM ranker (yearly retrain) shows a modest, fairly consistent edge**:
  ≈ +1.0–1.1% per 20 days over the random basket, hit 60–64%, positive in 6–7 of 7 test years,
  t ≈ 1.7–2.1 (borderline vs. the t>2 bar), mostly from avoiding the worst stocks and from smaller liquid
  names. It is a *weak* signal, useful as a filter/ranking factor over ≥10 stocks, not a per-stock prediction.

## Files
- `build_panel.py` (panel), `common.py` (backtest/stats), `rules.py` (train/valid screen), `ml.py` (tuning,
  fixed + walk-forward), `final.py` (TEST), `variants.py` (deployable variants), `train_deploy.py` (export)
- Logs/results: `final_log.txt`, `ml_log.txt`, `rules_tv.pkl`, `final_test.pkl`, `variants.pkl`
- Deliverable: `mo_hinh.py` + `mo_hinh_model.json` (pure numpy/pandas tree evaluator, no lightgbm/network;
  verified identical to LightGBM predictions, `verify.py`).
  - `diem_mo_hinh(df)` → score 0–100, bucket, expected 20/60d excess and hit rate (from 2017–2026 out-of-sample).
  - `xep_hang({ma: df})` → cross-sectional ranking for one day. Feed it the daily full-market scan
    (all stocks with ≥ 260 bars; it keeps those with 20d avg traded value ≥ 1 bn VND on the latest common date,
    needs ≥ 30, ideally 100–500 stocks); it computes per-date percentile ranks and market medians itself.
    Takes ~0.5 s for 260 stocks.
