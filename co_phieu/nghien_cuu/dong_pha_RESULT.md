# "Đồng pha" D/W/M (enter on daily, hold and exit on weekly or monthly): out-of-sample backtest, 2026-11-19

Exact rules: `SPEC.md`. Code: `core.py`, `persym.py`, `port_lots.py`, `port.py`, `report.py`, `randsym.py`, `vjc.py`, `now.py`.
Full tables: `tables.md`. Runtime is about 2 minutes on 4 processes.

**UP rule = at least 2 of 3 conditions** (structure HH+HL, MACD > signal, long Sto %K > %D). This was the user's decision mid-run.
The "all 3" rule is kept as a side row: it makes all three TFs align on only 0.4 % of days, against 8.1 % with 2 of 3.
W/M use **completed bars only**. The partial-bar variant was tested and is reported, but it was not used.

## Verdict (read this first)
- **The đồng pha filter and the daily entry signal show no reliable edge.**
  - The 1 bn VND portfolio's headline TEST result, **+16.9 %/yr (2020-01 → 2026-11)**, comes almost entirely from **one trade**:
    HQC, a monthly trade opened May 2020, made +1.87 bn of the +1.92 bn TEST profit (97 %).
  - **Without HQC the same portfolio makes +3.9 %/yr. Without HQC and VIC, +1.5 %/yr.** The max drawdown is −61 % (−41 % without HQC).
- **Benchmarks over the same TEST period:**

  | benchmark | TEST CAGR |
  |---|---|
  | equal-weight basket buy & hold | +9.8 % (DD −60 %) |
  | market phase filter | +16.0 % (DD −22 %) |
  | LEVEL 1 | +6.7 % |
  | MACD+Sto D+W | −1.5 % |

  The phase filter got the same return with a third of the drawdown, and without luck from a single stock.
- **Key control: random entries on đồng pha days**, with the same stops, confirmations, exits and sizing.
  - Portfolio: random W+M averages +6.6 %/yr in TEST (5–95 %: −2.9 … +17.8 %).
  - Per type, the real signal is not separable from random:
    - weekly (lệnh tuần): +4.2 % real vs +3.6 % random; 30 % of random runs do better;
    - monthly (lệnh tháng): +11.1 % real vs +6.7 % random; 35 % of random runs do better.
  - Per symbol (VN liquid, 10 seeds), the real weekly signal has a higher **mean** TEST trade (+8.0 % vs +5.8 %).
    But its **median** trade is worse (−3.6 % vs −3.0 %, all 10 seeds better), its win rate is lower (29.5 % vs 32.2 %),
    and its 2 %-trimmed mean is +3.3 % vs +2.6 %. So any edge sits in a few outliers. The monthly signal shows no difference.
- **The alignment itself is not an edge either.** Buying the first day đồng pha starts (same exits) lost **−6.6 %/yr in TEST**
  (−77 % DD) in the portfolio. Dropping the D UP requirement (W and M only) gave −2.1 %/yr.
  - Per symbol, the alignment-only entry did about as well as, or better than, the daily signals (W +7.2 %/trade, M +19.0 %/trade).
    The daily trigger adds nothing systematic.
- **Settings do not carry over.**
  - TRAIN→TEST rank correlation across the 96 portfolio variants: W −0.08, M −0.40.
  - The TRAIN-best per-symbol choice (2MA entry, exit b) beat buy & hold in TEST on only **28 % of VN liquid stocks**,
    and on **1 of 22** global symbols (BTC).
- **Entries are far from bottoms and exits far from tops.**
  - VN liquid: the median entry is **+18.8 % above the lowest low within ±20 sessions** (+35 % within ±60).
  - The median exit is **14 % below the highest high within ±20 sessions** (−19 to −21 % within ±60).
  - Alignment needs the monthly bar to turn first, so the start of a move is always missed.
  - VJC shows this: bottom 59.3k on 2025-04-09; entry 2025-08-18 at about 109–112k (+84–89 % above the bottom).
- Data caveats:
  - Survivorship bias (delisted VN stocks are missing) flatters everything, the benchmarks included.
  - Limit-up/limit-down lock-outs and slippage are not modelled.
  - The last session (2026-11-19) may be incomplete.
  - Nothing here was run on TradingView or GreenView itself.

## Setup
- **VN portfolio:**
  - Data: `bt_level1/data.npz` (891 stocks, adjusted daily OHLC, 2006-06 → 2026-11-19).
  - Account: 1 bn VND, cash only, lots of 100. Fees: buy 0.15 %, sell 0.15 % + 0.1 % tax.
  - Sizing: stop money per LEVEL 1. Liquidity: 20-day traded value ≥ 1 bn VND at the signal.
  - Grid, per trade type: 3 entry signals × 2 exits × completed/partial bars × 2 risk levels (W 8/12 %, M 12/20 %) × N 5/10.
  - Selection: best TRAIN (2008–2019) CAGR/volatility among completed-bar variants with ≥ 30 trades. TEST was run once.
  - **Chosen:**
    - lệnh tuần = "either" signal, exit a (all at the first W sell), 8 %, N = 10;
    - lệnh tháng = MACD+Sto signal, exit a, 20 %, N = 5.
  - Both types run in one account.
- **Per symbol, standalone:**
  - Universe: 1,505 VN listed stocks from `bt_tung_ma/raw`, of which 292 are liquid (≥ 1 bn/day median over the last 250 sessions, ≥ 2 years of data).
    Plus gold (GC=F), BTC-USD and the 20 US stocks/ETFs.
  - Sizing: 100 % of capital per trade.
  - Split: VN TRAIN = entries before 2020 and TEST = 2020+. Other symbols: first and second half of their bars.
  - Selection: best TRAIN pooled average % per trade among completed-bar variants.
  - Chosen: VN = 2MA entry with exit b, for both W and M. Global = "either" entry with exit b, for both W and M.

## Portfolio results (VN, 1 bn VND)
| strategy | TRAIN CAGR | **TEST CAGR** | TEST total | **TEST maxDD** | TEST trades | TEST win | TEST avg %/trade | TEST hold (cal. days) | TEST exposure |
|---|---|---|---|---|---|---|---|---|---|
| chosen lệnh tuần (W) | +6.7 % | **+4.2 %** | +33 % | −31 % | 257 | 25 % | −0.3 % | 81 | 59 % |
| chosen lệnh tháng (M) | +6.9 % | **+11.1 %** | +107 % | −59 % | 58 | 17 % | −1.6 % | 187 | 69 % |
| **chosen W+M, one account** | +6.3 % | **+16.9 %** | +193 % | **−61 %** | 303 | 25 % | +4.0 % | 97 | 79 % |
| same, without HQC | | +3.9 % | | −41 % | 295 | | | | |
| same, without HQC and VIC | | +1.5 % | | −41 % | 292 | | | | |
| random entries on đồng pha days, W+M (mean of 20) | +5.6 % | +6.6 % (5–95 %: −2.9…+17.8) | | −51 % | 293 | 26 % | +2.6 % | | |
| alignment-only (buy the first đồng pha day), W+M | +0.7 % | **−6.6 %** | −38 % | −78 % | 384 | 22 % | −0.5 % | 85 | 92 % |
| W & M aligned, no D UP needed | −3.8 % | −2.1 % | | −72 % | 373 | 21 % | | | |
| partial W/M bars (same settings) | +6.3 % | +5.0 % | +40 % | −46 % | 304 | 27 % | +2.2 % | 103 | 86 % |
| "all 3 conditions" UP rule (side row) | −3.5 % | −0.2 % | | −61 % | 79 | 22 % | −3.2 % | | |
| signal = 2MA for both types | −0.2 % | +14.5 % | | −58 % | 267 | | | | |
| signal = MACD+Sto for both types | +7.8 % | +14.8 % | | −56 % | 270 | | | | |
| signal = either for both types | +3.3 % | +8.3 % | | −62 % | 289 | | | | |
| EW liquid basket buy & hold | −7.4 % | +9.8 % | +90 % | −60 % | | | | | 100 % |
| market phase filter (bt_chuky) | +15.0 % | **+16.0 %** | +177 % | **−22 %** | | | | | |
| LEVEL 1 D+W+M (bt_level1) | | +6.7 % | +56 % | −35 % | | | | | |
| MACD+Sto D+W plain (bt_macd_sto) | | −1.5 % | −10 % | −35 % | | | | | |

Notes on the portfolio table:
- Random control, real vs random TEST: W 4.2 vs 3.6 (30 % of random runs ≥ real); M 11.1 vs 6.7 (35 % ≥ real); W+M 16.9 vs 6.6 (10 % ≥ real).
  On TRAIN, W+M was 6.3 vs 5.6 (35 % ≥ real).
- The 10 largest TEST trades were HQC M (+1,874 M), VIC M (+595 M), VGI W (+288 M), SBT M, LPB W, VHM M, VPI W, MBB W, LHG W and ACV M.
  The top 5 together are 160 % of the net profit.
- The median TEST CAGR across the whole grid is W +4.3 % and M +9.0 %. The M figures mostly reflect the 2020–21 and 2025 rallies.
- Every signal combination lands between +8 and +15 % in TEST. The spread between combinations comes from which stock happened to catch a big move.

### Per year (FULL run, chosen settings, %)
| year | chosen W | chosen M | chosen W+M | alignment-only | EW basket | phase filter | LEVEL 1 | MACD+Sto |
|---|---|---|---|---|---|---|---|---|
| 2009 | −2.0 | +0.8 | −1.5 | +8.8 | +81.3 | +100.0 | −0.7 | +5.9 |
| 2010 | −7.5 | −8.3 | −15.6 | −15.7 | −18.2 | +18.7 | +3.0 | +7.7 |
| 2011 | −0.4 | −4.4 | −3.6 | −34.1 | −52.8 | −10.4 | −4.7 | −1.7 |
| 2012 | −2.3 | +1.6 | +5.8 | +40.2 | +16.0 | +40.9 | +0.4 | +27.9 |
| 2013 | +10.1 | +49.2 | +42.7 | +49.9 | +13.0 | +21.6 | +3.5 | +27.0 |
| 2014 | +15.9 | −9.0 | −9.7 | +8.5 | +24.1 | +38.7 | +33.6 | +32.0 |
| 2015 | +10.7 | +19.0 | +0.6 | −12.4 | −4.6 | −7.8 | +7.8 | +18.0 |
| 2016 | +2.4 | −1.5 | +4.2 | −25.1 | −2.6 | −11.9 | +6.6 | −8.4 |
| 2017 | +50.3 | +36.6 | +60.8 | +44.5 | +31.2 | +16.9 | +37.7 | +32.5 |
| 2018 | +4.4 | +3.2 | +1.1 | −30.2 | −10.2 | +1.6 | −7.3 | +3.8 |
| 2019 | +8.7 | +10.7 | +11.7 | +19.6 | +1.0 | +0.9 | +15.5 | −5.7 |
| 2020 | +24.5 | +59.6 | +54.5 | +39.1 | +41.2 | +35.5 | +28.1 | −9.3 |
| 2021 | +34.8 | +174.4 | +57.6 | +96.5 | +100.7 | +58.3 | +65.9 | +29.7 |
| 2022 | −20.2 | −27.1 | −33.1 | −51.5 | −50.0 | +7.8 | −33.2 | −17.5 |
| 2023 | −9.5 | −23.5 | −19.2 | −12.3 | +31.4 | +7.0 | +5.4 | −8.2 |
| 2024 | +33.8 | +8.0 | +19.7 | −7.3 | +8.1 | +7.7 | +14.8 | −6.1 |
| 2025 | +6.2 | −1.7 | +27.6 | −9.3 | +13.4 | +20.0 | +2.0 | +56.6 |
| 2026 (to 11-19) | −18.5 | −17.9 | −13.7 | −27.6 | −16.3 | −13.4 | −10.5 | −10.2 |

Full-period chosen W+M (2008 → 2026-11): **+7.0 %/yr, DD −53 %**. Same period: phase filter +15.4 %/yr, basket −1.5 %/yr.
The 2022 bear market cost −33 %. The monthly exit reacts too slowly, and the đồng pha filter does not keep the account out of a falling market.

## Per-symbol standalone (100 % capital per trade)
VN liquid stocks (292). TRAIN = entries before 2020, TEST = 2020+. The "avg" columns are pooled over all trades.

| variant | TRAIN trades | TRAIN avg %/trade | TEST trades | **TEST avg %/trade** | TEST % of stocks beating B&H | TEST median CAGR (B&H +10.0 %) | full win % | median hold (sessions) |
|---|---|---|---|---|---|---|---|---|
| **lệnh tuần, chosen (2MA, exit b)** | 546 | 8.7 | 725 | **8.0** | **28 %** | −0.5 % | 32 % | 62 |
| random entry, same exits | 438 | 8.0 | 657 | 4.8 | 26 % | 0.0 % | 35 % | 73 |
| alignment-only entry | 1,255 | 8.9 | 1,834 | 7.2 | 32 % | +1.8 % | 31 % | 79 |
| partial W/M bars | 673 | 7.9 | 888 | 9.7 | 29 % | 0.0 % | 32 % | 67 |
| all-3 rule, either signal | 34 | 12.2 | 56 | 1.8 | 24 % | 0.0 % | 30 % | 36 |
| **lệnh tháng, chosen (2MA, exit b)** | 445 | 27.7 | 566 | **16.2** | **28 %** | −0.8 % | 24 % | 158 |
| random entry, same exits | 350 | 25.9 | 512 | 10.8 | 28 % | −0.1 % | 25 % | 170 |
| alignment-only entry | 829 | 29.9 | 1,059 | 19.0 | 31 % | +2.7 % | 25 % | 195 |
| partial W/M bars | 524 | 26.0 | 679 | 16.9 | 30 % | 0.0 % | 25 % | 172 |
| all-3 rule, either signal | 34 | 30.9 | 55 | −4.5 | 24 % | 0.0 % | 16 % | 53 |

- The random row above is a single seed. With 10 seeds (`randsym.py`), the TEST trade returns compare as follows:

  | type | statistic | real | random mean | random runs ≥ real |
  |---|---|---|---|---|
  | W | mean | +8.0 % | +5.8 % | 0/10 |
  | W | median | −3.6 % | −3.0 % | 10/10 |
  | W | win rate | 29.5 % | 32.2 % | |
  | W | 2 %-trimmed mean | +3.3 % | +2.6 % | 1/10 |
  | M | mean | +16.2 % | +13.5 % | 1/10 |
  | M | median | −5.9 % | −5.5 % | 9/10 |
  | M | trimmed mean | +7.7 % | +6.8 % | 2/10 |

  On TRAIN, real and random are equal: W mean 8.7 vs 8.4, M 27.7 vs 26.6.
- All 1,467 VN stocks with ≥ 2 years of data (80 % illiquid): W +5.7 %/trade and M +13.1 %/trade. 33 % beat buy & hold in TEST.
- The typical trade loses: the median trade is negative, the win rate is 24–32 %, and the average comes from a few large winners.
  Most stocks spend only 8 % (W) to 16 % (M) of the time invested.

**Gold, BTC, 20 US** (TRAIN = first half, TEST = second half; chosen = "either" entry, exit b):

| | TEST trades | TEST avg %/trade | random | alignment-only | symbols beating B&H in TEST |
|---|---|---|---|---|---|
| lệnh tuần | 352 | +4.7 | +4.1 | +6.9 | 1/22 (BTC) |
| lệnh tháng | 196 | +27.5 | +32.3 | +37.1 | 1/22 (BTC) |

- Gold full period: W −1.4 %/yr, M +2.3 %/yr, against buy & hold +10.5 %/yr.
- BTC: W +35.8 %/yr against buy & hold +50 %. M took one trade (+7,256 %).
- US stocks: W +0.2 to +6.2 %/yr against buy & hold +10 to +40 %/yr. Per-symbol table: `glob.md`.

## How close to bottoms and tops (median, chosen variants)
| group | type | trades | entry above low ±20 sessions | exit below high ±20 | entry above low ±60 | exit below high ±60 |
|---|---|---|---|---|---|---|
| VN liquid | W | 1,271 | +18.8 % | 13.9 % | +35.0 % | 19.3 % |
| VN liquid | M | 1,011 | +18.6 % | 14.2 % | +35.0 % | 21.1 % |
| VN liquid, alignment-only | W / M | | +18.4 % | 13.7–13.9 % | +31.7 % | 19.3–20.8 % |
| Gold, BTC, US | W | 610 | +10.5 % | 8.9 % | +19.8 % | 12.1 % |
| Gold, BTC, US | M | 347 | +10.5 % | 11.2 % | +20.1 % | 15.3 % |

## Worked example: VJC 2025–2026 (bottom 2025-04-09 low 59.3k, top 2025-11-26 high 169.2k)
- **When each timeframe turned UP after the bottom:**
  - D turned UP on 2025-04-23.
  - W turned UP on 2025-06-13. The structure condition was false all spring; MACD crossed up that week.
  - M turned UP only on **2025-07-31**, when the July bar closed at 93.2k.
  - So the first đồng pha day was 2025-07-31, with the price already +57 % above the bottom.
- **Đồng pha windows:** 31/7–12/8, 14–25/8, 28–29/8, 17–23/10, 31/10–4/11, 21/11–5/12/2025, 25/12/2025–9/1/2026, and 12–23/6/2026.
- **Daily signals inside those windows:** only one, MACD+Sto Mua on 2025-08-15 (close 112.0k).
  No 2MA cross happened inside an aligned window, so the chosen per-symbol VN variant (2MA) took **no trade**.
- **Trades in variants that use the MACD+Sto signal:**
  - Entry 2025-08-18 at 112.0k (or 109.2k on average with the confirmation order). That is **+84–89 % above the bottom**.
  - Lệnh tuần, exit a: sold 2025-09-22 at 105.0k, a −2 to −4 % loss. Price then ran to 169.2k.
  - Lệnh tuần, exit b: 70 % sold 2025-09-22 at 105.0k and the rest on 2026-01-19 at 116.1k, +5.8 % in total.
    The last part sold 31 % below the top.
  - Lệnh tháng (no monthly sell signal yet): still held at 137.2k (+6.6 % / +25 % with confirmation), 19 % below the top.
- **For comparison:**
  - Alignment-only (buy 2025-08-01 at 97.3k): +18.8 % (W) and +40.4 % (M, still open).
  - Partial bars (aligned from 2025-07-24, entry 93.7k): +23.4 % (W) and +45.8 % (M).
- In short, the method caught about a quarter of the 59k → 169k move at best, and lost money in its strictest weekly form.

## Reference indicators (MA80 % and Heikin-Ashi)
| TF | UP share of bars | MA80 % true when UP / not UP | HA 3 green when UP / not UP |
|---|---|---|---|
| D | 43 % | 29 % / 25 % | 45 % / 12 % |
| W | 44 % | 33 % / 25 % | 50 % / 13 % |
| M | 42 % | 38 % / 22 % | 54 % / 16 % |

HA agrees with UP about half the time. MA80 % hardly separates UP from not UP on D.

## Files
- `dong_pha_tung_ma.xlsx`: sheets "Tổng hợp", "Lệnh tuần", "Lệnh tháng" (per symbol, chosen variant) and "Danh sách lệnh"
  (3,239 trades, VN liquid + global, with entry-above-bottom and exit-below-top %).
- `ket_qua_dong_pha.json`: same format as `ket_qua_tung_ma.json`, with keys `dong_pha_w` and `dong_pha_m`.
- `now.json`: 303 VN liquid stocks with their current D/W/M state (2 of 3, components, MA80, HA), đồng pha, today's signals and suggested stop.
  - On 2026-11-19: D UP 75, W UP 155 (week ending 14/11), M UP 48 (October).
  - Only **2 stocks are in đồng pha (VIC, VPI)**, and **neither has a daily buy signal today**.
- `tables.md`: all tables, including the 96-variant TRAIN grid.
- `glob.md`: global per-symbol table.
