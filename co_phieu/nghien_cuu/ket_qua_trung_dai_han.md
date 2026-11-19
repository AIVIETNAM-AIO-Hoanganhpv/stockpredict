# Backtest of GreenView "Cổ phiếu trung/dài hạn" (`st_daihan`), whole VN market 2000-07 → 2026-11 (run 2026-11-19)

## Verdict (read this first)
**No edge. Neither v2 (current rules) nor v1 (previous rules) beats buy & hold, the market-phase filter, or random entries in a reliable way.**

- **v2 (main, ADX 25)** trades very rarely: 340 trades in 26 years over all 1,499 symbols (about 1 trade per symbol every 40 years;
  281 symbols ever trade). Average trade +1.2 % (9 months) / +1.9 % (10 years), median −7.6 % / −8.8 %, only 20–25 % of trades win.
  Portfolio (1 bn VND): **TEST 2014–2026 −3.3 %/yr (9 months) and −5.1 %/yr (10 years)**, max drawdown −51 % / −67 %.
  Same period: equal-weight basket buy & hold **+7.3 %/yr**, market-phase filter **+10.6 %/yr** (max DD −28 %).
  Random entries on the same days do as well or better (the real result is at the 45th / 29th percentile of 200 random runs).
- **v2 filters remove good trades with the bad ones.** Going from "no Fibo filter" to v1 to v2 lowers the average trade (TEST, all symbols, 9 months):
  +5.6 % → +5.3 % → +1.0 %. v2 does raise the median trade (−7.6 % vs −12 % for random entries), because it buys after a pullback
  with a closer stop, but it loses the big winners, so the mean and the money result get worse.
- **v1 (old rules) 10 years, ADX 25** is the only row that looks good in TEST (+10.8 %/yr, 94th percentile of random) but it is **not
  reliable**: one stock (PHR, +0.84 bn VND) makes most of it — without PHR it is +2.4 %/yr; the full period is +0.4 %/yr; neighbouring
  settings jump around (ADX 0: +17.4 %, ADX 20: +5.1 %, ADX 30: +9.0 %); the 9-month version is −2.4 %/yr (13th percentile of random).
- **ADX filter**: no consistent effect. Higher ADX gives fewer trades and a similar or lower return. 25 is not better than 0, 20 or 30.
- **Per symbol** (100 % of capital in one stock): v2 beats that stock's own buy & hold in 32 % of symbols in TEST — the same as random entries (32 %)
  and the same as simply staying in cash (most symbols never trade). On liquid symbols: 21 %.
- The GreenView sanity cases reproduce exactly (see "Check against the JS"). MWG 2026-01-30 (the motivating bad entry) is rejected under v2.

Caveats: survivorship bias (symbols delisted before ~2024 are missing, so everything — benchmarks too — is optimistic); no ceiling/floor
(limit-up/down) locks, so stops and exits assume a fill at the open; adjusted prices; before 2006 there are only 4–15 priced symbols
and **no symbol passes the 1 bn VND liquidity filter before 2006**, so the portfolio is in cash 2000–2006 (TRAIN portfolio numbers are
mostly 2007–2013). Liquidity uses adjusted close × volume, which understates old traded values.

## Setup (details in SPEC.md)
- 1,505 VN symbols (`bt_tung_ma/raw`), earliest 2000-07-28, end 2026-11-19. Coverage per year: tables.md "Data coverage"
  (listed: 5 in 2000, 23 in 2005, 236 in 2008, 671 in 2013, 1,505 in 2026; liquid symbols per day: 0 until 2005, 24–125 in 2008–2014, ~300–380 since 2021).
- Split: TRAIN 2000-07 → 2013-12, TEST 2014-01 → 2026-11. Nothing chosen on TEST (ADX 25 / profit ≥ 10 % / stop ≤ 15 % are the user's defaults).
- v2 entry filter: monthly AND weekly strict Fibo-1.0 targets ≥ close +10 % (confirmed wave peak, pullback ≥ 23.6 %) and close ≤ C + 50 % of C→B (weekly wave).
  v1: monthly target (else weekly) ≥ +10 %, new wave may use the running bar's high.
- Exit: monthly MACD+Sto sell, or max hold 274 / 3,653 days, or stop. Exit reasons per lot (v2 9 m): stop 59 %, monthly sell 22 %, max hold 19 %;
  (v2 10 y): stop 68 %, monthly sell 31 %. Median holding 82–94 days for all versions.

## Portfolio, 1 bn VND (risk 20 %, max 5 names, liquidity ≥ 1 bn VND/day)
| strategy | TRAIN CAGR | TRAIN max DD | **TEST CAGR** | TEST max DD | TEST trades | FULL CAGR | FULL max DD | random runs ≥ real (TEST) |
|---|---|---|---|---|---|---|---|---|
| **v2, 9 months, ADX 25** | −0.8 % | −30 % | **−3.3 %** | −51 % | 59 | −1.9 % | −51 % | 56 % |
| **v2, 10 years, ADX 25** | −1.3 % | −35 % | **−5.1 %** | −67 % | 50 | −3.2 % | −67 % | 71 % |
| v1, 9 months, ADX 25 | −1.6 % | −47 % | −2.4 % | −79 % | 169 | −3.5 % | −79 % | 87 % |
| v1, 10 years, ADX 25 | +0.1 % | −51 % | +10.8 % | −55 % | 93 | +0.4 % | −62 % | 6 % |
| no Fibo filter, 9 months, ADX 25 | −2.0 % | −47 % | +5.7 % | −59 % | 161 | +0.9 % | −59 % | |
| no Fibo, no ADX, 9 months | −2.7 % | −53 % | +7.6 % | −70 % | 179 | +0.1 % | −68 % | |
| EW liquid basket buy & hold | −8.4 % | −88 % | **+7.3 %** | −59 % | | −1.0 % | −88 % | |
| market-phase filter (chu_ky) | +11.5 % | −38 % | **+10.6 %** | −28 % | | +11.1 % | −38 % | |

All ADX thresholds (portfolio TEST CAGR): v2 9 m: off +2.5 %, 20: −0.2 %, 25: −3.3 %, 30: −2.2 %; v2 10 y: +4.2 / +12.1 / −5.1 / −4.5 %;
v1 9 m: +5.0 / +5.7 / −2.4 / +3.8 %; v1 10 y: +17.4 / +5.1 / +10.8 / +9.0 %. The jumps between neighbours (only 40–180 trades in 13 years)
show how noisy these numbers are. Random-entry portfolio (200 runs, TEST): v2 9 m mean −2.6 % (5–95 %: −7.9 … +2.7 %); v2 10 y mean −2.9 %
(−8.6 … +3.4 %). **Sizing**: other risk/N settings do not change the picture (v2 TEST between −0.1 % and −5.1 %/yr; the sizing chosen on
TRAIN gives v2 9 m −0.4 %, v2 10 y −1.1 %). **Concentration**: v2 9 m without its best symbol (HHS): TEST −2.9 %; top-5: HHS, TSC, DBC, MSN, DRC.
v1 10 y without PHR: TEST +2.4 % (from +10.8 %), FULL −3.6 %.

Per year (FULL run): v2 is flat or negative in most years; v2 made +62 % (9 m) / +83 % (10 y) in 2021 and lost −21 % / −37 % in 2022
and −26 % / −37 % in 2025. EW basket and phase filter per year: tables.md.

## Per symbol (100 % of capital per symbol), ADX 25
| | trades | trades / 4 yrs / symbol | avg trade | median trade | win | % symbols beating own B&H | same, random entries (200 runs) |
|---|---|---|---|---|---|---|---|
| **v2 9 m, FULL** | 340 (281 symbols) | 0.1 | +1.2 % | −7.6 % | 25 % | 39.7 % | 39.6 % |
| **v2 9 m, TEST** | 298 | 0.1 | +1.0 % | −7.6 % | 24 % | 32.2 % | 31.9 % |
| **v2 10 y, FULL** | 338 | 0.1 | +1.9 % | −8.8 % | 20 % | 39.8 % | 39.6 % |
| **v2 10 y, TEST** | 296 | 0.1 | +1.2 % | −8.9 % | 20 % | 32.0 % | 31.8 % |
| v1 9 m, TEST | 3,053 | 0.8 | +5.3 % | −11.2 % | 29 % | 32.6 % | 32.5 % |
| v1 10 y, TEST | 2,644 | 0.7 | +6.9 % | −13.4 % | 23 % | 32.7 % | 31.7 % |
| no Fibo, ADX 25, 9 m, TEST | 3,274 | 0.8 | +5.6 % | −11.0 % | 30 % | 32.5 % | |

Random entries vs real (average trade, % of 200 random runs ≥ real; low = real better): v2 9 m FULL 26 %, TEST 22 %; v2 10 y FULL 30 %,
TEST 21 %; v1 9 m TEST 73 %; v1 10 y TEST 24 %. None is below 5 %, so the average trade is not better than random.
The median trade is better than random for v2 (0 % of random runs reach it) but that does not turn into money (portfolio above).
Strategy median CAGR per symbol is 0 % because most symbols never trade; buy & hold median CAGR: +2.8 % (FULL), +5.5 % (TEST).
Liquid symbols only (292): v2 9 m TEST average trade −0.2 %, beats own B&H in 21 % of symbols (B&H median +9.2 %/yr). Full tables: tables.md.

## Check against the JS (sanity)
- `repro.py` runs the real GreenView JS (`DEFS.st_daihan`, Chromium) and the Python port on the same bars. Lot lists (days and prices) are
  **identical in 141/141 cases for v1 and 141/141 for v2** (47 symbols × {9 m ADX 25, 10 y ADX 25, 9 m ADX 0}, full history).
  Two fixes were needed to get there: (1) in `dayTuan` the JS compares the weekly pivot low with the **weekly close** (not the daily close);
  (2) moving averages are computed with the JS running-sum formula — with pandas, flat prices of illiquid stocks gave float ties that flipped
  a few crosses.
- With data from 2021-09-01 (as in GreenView), defaults (v1 rules, 9 months, ADX 25, lai 10, catMax 15) the port gives exactly the trades
  you listed: FPT 2024-02-02 @65,759 + 2024-02-05 @66,940 → 2024-11-05 @101,071 (max hold), 2024-11-14 @104,794 → stop 2024-11-20 @98,487;
  VJC 2025-08-18 @111,996 + 2025-08-22 @108,073 → 2026-05-20 @132,302 (max hold); SSI 2025-10-14 @30,834 → stop 2025-10-27 @25,590.
- On full history (v1) FPT and VJC are the same; SSI gets one extra trade (2023-08-25/28, stopped 2023-10-30/31) because with data only
  from 2021-09 the monthly MACD/Sto are not warmed up until ~2024 (no monthly "UP" possible → no đồng pha). MWG's 2024 trade exits
  differently for the same reason.
- **Under v2 none of FPT, VJC, SSI, MWG has a trade since 2021-09.** MWG 2026-01-30 (v1 entry 2026-02-02 @90,465, stopped 2026-03-06):
  v1 monthly new wave A 31,931 / B 90,757 (daily high of the running week) / C 87,259 → target 146,085. Under v2 the monthly strict wave
  gives no target, the weekly target 93,575 is only +3.7 %, and the close 90,271 is above the pullback limit 84,441 → rejected (3 reasons).

## Files (in this folder)
- `RESULT.md` (this), `SPEC.md` (exact rules), `tables.md` (all tables), `ket_qua_dai_han.xlsx` (sheets: per symbol ADX 25 both holds
  v2 + v1 with Vietnamese columns; all lots ADX 25 both holds v2 + v1; portfolio per year; portfolio summary).
- Code: `dh.py` (strategy port), `repro.py` + `js_run.js` (JS check; `GreenView_v1.html` = git HEAD build, `GreenView_v2.html` = current),
  `mat.py` (matrices), `persym_dh.py` (per symbol + random), `engine_dh.py` / `port.py` (portfolio + random), `bench.py`, `report.py`.

---

## v3 = v2 + closing-price stop (added 2026-11-19, user's choice; JS `R.catDong` in `DEFS.st_daihan`)
Rule change: no intraday stop. Exit everything at the next open if any lot has (a) a weekly close below its stop, checked on the
last session of each COMPLETED week, or (b) a daily close ≤ its fill × 0.85. The stop level and the entries are the same as v2.

**Verdict: v3 is a little less bad than v2, but there is still no edge.** In the portfolio TEST it is −1.3 %/yr (9 months) and
−0.1 %/yr (10 years), against +7.3 % for buy & hold and +10.6 % for the phase filter. It sits at the 57th / 68th percentile of 200
random-entry runs. The closing-price stop gives the trades more room: the average trade rises from about +1 % to about +3.4 % (TEST),
and the win rate from 24 % to 31 %. The price is bigger single losses: the worst stopped lot is −30 % (v2: −23 %), and 5 % of stopped
lots lose more than −22 %.

**Check against the JS:** the lot lists are identical in 141/141 cases (47 symbols × 3 settings, full history, current
GreenView build `GreenView_v3.html`). Your test cases match: SAB in 2023-03-14 → out 2023-04-10 (Cắt lỗ); VHM in 2026-02-24 →
out 2026-03-04 (Cắt lỗ); GMD in 2026-03-30 → still open on 2026-11-19. The v1 and v2 results above did not change on re-run.

### Portfolio, 1 bn VND (risk 20 %, max 5 names)
| strategy | TRAIN CAGR | **TEST CAGR** | TEST max DD | TEST trades | FULL CAGR | FULL max DD | random ≥ real (TEST) |
|---|---|---|---|---|---|---|---|
| **v3, 9 months, ADX 25** | −0.6 % | **−1.3 %** | −48 % | 57 | −0.3 % | −48 % | 43 % |
| **v3, 10 years, ADX 25** | −0.6 % | **−0.1 %** | −54 % | 46 | 0.0 % | −54 % | 33 % |
| v2, 9 months, ADX 25 | −0.8 % | −3.3 % | −51 % | 59 | −1.9 % | −51 % | 56 % |
| v2, 10 years, ADX 25 | −1.3 % | −5.1 % | −67 % | 50 | −3.2 % | −67 % | 71 % |
| EW basket buy & hold | −8.4 % | +7.3 % | −59 % | | −1.0 % | −88 % | |
| market-phase filter | +11.5 % | +10.6 % | −28 % | | +11.1 % | −38 % | |

- **ADX threshold (portfolio TEST CAGR; off / 20 / 25 / 30):**
  - v3 9 months: +6.0 / +1.9 / −1.3 / −0.6 %.
  - v3 10 years: +8.9 / +18.1 / −0.1 / −1.2 %.
  - These jumps come from only 40–80 trades in 13 years, so they are noise, not a signal.
- **Sizing:** every risk/N setting gives v3 TEST between −1.3 % and +0.5 %/yr. The sizing chosen on TRAIN gives −0.4 % (9 months) and −1.1 % (10 years).
- **Concentration:**
  - v3 10 years: TEST −2.7 %/yr without PET.
  - v3 9 months: TEST −1.1 %/yr without HHS.
- **Per year:**
  - 2021: +59 % (9 months) / +79 % (10 years).
  - 2022: −16 % / −28 % (v2: −21 % / −37 %).
  - 2025: −23 % / −22 %.

### Per symbol (100 % of capital per symbol), ADX 25, all 1,499 symbols
| | trades | trades / 4 yrs / symbol | avg trade | median | win | % symbols beating own B&H | random entries: same | random runs ≥ real avg trade |
|---|---|---|---|---|---|---|---|---|
| **v3 9 m, TEST** | 296 | 0.1 | +3.4 % | −7.1 % | 31 % | 32.2 % | 31.9 % | 9 % |
| **v3 10 y, TEST** | 294 | 0.1 | +3.3 % | −8.8 % | 25 % | 32.0 % | 31.9 % | 18 % |
| v3 9 m, FULL | 338 | 0.1 | +3.1 % | −7.7 % | 31 % | 39.6 % | 39.6 % | 14 % |
| v3 10 y, FULL | 336 | 0.1 | +3.6 % | −9.1 % | 25 % | 39.6 % | 39.7 % | 30 % |
| v2 9 m, TEST | 298 | 0.1 | +1.0 % | −7.6 % | 24 % | 32.2 % | 31.9 % | 22 % |

- The v3 9-month average trade in TEST is better than 91 % of random runs. That is the closest any version gets to "better than random", but:
  - it is not below the usual 5 % bar;
  - TRAIN goes the other way (75 % of random runs are better);
  - it does not show up in the portfolio.
- On liquid symbols v3 TEST average trade is +0.5 % (9 months) / +0.8 % (10 years). Only 13 % of the symbols that traded beat their own buy & hold (B&H median +9.2 %/yr).
- Exit reasons per lot:
  - v3 9 months: stop 54 %, monthly sell 24 %, max hold 21 %.
  - v3 10 years: stop 63 %, monthly sell 35 %.

Excel: new sheets `v3 cat lo dong cua - tung ma` and `v3 cat lo dong cua - lenh`. The other sheets now include v3 rows. All v3 tables are in `tables.md`.

---

## v4 = market phase as the main rule (added 2026-11-19, user's choice). Code: `v4prep.py`, `v4.py`, `v4report.py`, `phase.py`; all tables in `tables_v4.md`
Rules:
- **Phase gate.** Use the VN market phase from the phase-filter benchmark, recomputed from 2000. When the phase is bad, sell everything at the next open and buy nothing.
- **Candidates** on a good-phase day, all of these:
  - đồng pha D/W/M;
  - weekly ADX(14) ≥ 25 with DI+ > DI− (also tested: off, 20, 30);
  - liquidity ≥ 1 bn VND per day;
  - a stop level exists.
  - The ≥ 10 % Fibo condition is dropped.
- **Variants:**
  - (a) also the daily trigger (2MA or Mua1/Mua2) on a bullish candle;
  - (b) = (a) plus the v2 "chờ hồi" pullback rule when a strict weekly wave exists;
  - (c) no daily trigger.
- **Sizing.** N = 5 or 10 names, equal weight (equity ÷ N at the open), one lot per stock. Free slots are filled at the next open from candidates ranked by 6-month return or by weekly ADX. The ranking was picked on TRAIN by Sharpe.
- **Exits** (at the next open):
  - monthly MACD+Sto sell;
  - v3 closing stop (weekly close below the stop, or daily close ≤ fill × 0.85);
  - max hold 274 days or 3,653 days.
- Fees as before; 1 bn VND.

**Verdict.**
- **The market phase does the work, not the stock rules.**
- **No v4 setting beats the plain phase filter** (hold the equal-weight liquid basket when the phase is good): TEST +10.6 %/yr, max drawdown −28 %, FULL +11.1 %/yr.
- **The user's setting, (a) ADX 25:** TEST +5.4 %/yr (N 5) and +5.2 %/yr (N 10); FULL +2.0 % and +1.6 %/yr; TRAIN −1.2 % and −1.7 %/yr. Random picks from the same pool do the same or better (42 % and 83 % of 200 runs ≥ real).
- **(b) with the pullback rule is worse:** TEST +0.5 % (N 5) and +2.3 % (N 10).
- **(c) without the daily trigger is the best v4:** TEST +8.4 % (N 5) and +11.2 % (N 10); FULL +6.1 % and +6.7 %; TRAIN +4.0 % and +2.6 %. Max drawdown is −36 % / −40 %.
  - It is still below the phase filter on FULL (+11.1 %) and has a deeper drawdown.
  - Against random picks from the same pool it is borderline: 7.5 % of runs beat it in TEST (N 10), 9.5 % on FULL, but 56 % in TRAIN. So it is not a reliable stock-picking edge.
- **Why the stock rules barely matter:**
  - The gate flips about 15 times a year, so the average holding is only 16–20 days. The 9-month and 10-year versions are therefore identical: max hold, and almost never the monthly sell, is ever reached.
  - With the daily trigger, the pool averages 1 candidate per good day (median 0), so N slots are rarely full. The portfolio is invested only 15–19 % of the time, against 37 % for the phase filter.
- **ADX threshold:** no clear effect. For (c) N 10, TEST is: off +14.2 %, 20 +12.2 %, 25 +11.2 %, 30 +10.9 %. Turning ADX off is the best, and TRAIN agrees (+5.2 %).
- **Concentration (FULL):**
  - (a) N 5 without SHS: TEST +4.0 %.
  - (c) N 10 without CTP: TEST +10.0 %, FULL +6.2 %.
  - Top-5 contributors for (c) N 10: CTP, L40, HID, APS, VOS.
- **Per year, (c) N 10 vs the phase filter:**
  - 2021: +76 % vs +56 %.
  - 2022: −9 % vs +6 %.
  - 2023: −23 % vs +7 %.
  - 2024: +53 % vs +11 %.
  - 2025: +43 % vs +20 %.

| strategy (ADX 25, TRAIN-picked ranking) | TRAIN | **TEST** | FULL | TEST max DD | FULL max DD | random runs ≥ real (TEST) |
|---|---|---|---|---|---|---|
| v4 (a) daily trigger, N 5 | −1.2 % | **+5.4 %** | +2.0 % | −34 % | −35 % | 42 % |
| v4 (a) daily trigger, N 10 | −1.7 % | **+5.2 %** | +1.6 % | −23 % | −31 % | 83 % |
| v4 (b) + pullback rule, N 10 | +0.1 % | +2.3 % | +1.2 % | −29 % | −29 % | 31 % |
| v4 (c) no trigger, N 5 | +4.0 % | +8.4 % | +6.1 % | −36 % | −36 % | 26 % |
| v4 (c) no trigger, N 10 | +2.6 % | +11.2 % | +6.7 % | −40 % | −40 % | 7.5 % |
| phase filter + EW basket | +11.5 % | **+10.6 %** | +11.1 % | −28 % | −38 % | |
| EW buy & hold | −8.4 % | +7.3 % | −1.0 % | −59 % | −88 % | |

**Phase series for GreenView:**
- `pha_2000.json` holds [date, phase] at each change point, 516 changes from 2000-07-28 to 2026-10-29.
  - Phase names are the same as `co_phieu/dudoan/chu_ky.py`: "Tăng", "Tích luỹ cuối", "Tích luỹ", "Phân phối", "Giảm".
  - "Good" (nên cầm cổ phiếu) = Tăng, Tích luỹ cuối or Tích luỹ (`PHA_TOT`), except when the US 10-year yield rose more than 0.75 points in 3 months. That exception covers 5 % of days, and no yield data exists before 2005.
  - Because of that exception the phase name alone does not decide "good". `pha_2000_tot.json` gives [date, phase, tot] at every change of either.
- **Caveat:** before 2006 no stock passes the liquidity filter, so the index is flat and the phase is "Giảm" until 2006-03.
- Excel: new sheets `v4 pha thi truong - tong hop`, `v4 so voi ngau nhien`, `v4 theo nam`, `v4 danh sach lenh`.

---

## v5 = "only sell in profit, never at a loss" (added 2026-11-19, user's choice). Code: `v5.py`, `v5report.py`; all tables in `tables_v5.md`
Rules:
- **Entries** as in v4: good phase only; candidates = đồng pha + weekly ADX ≥ 25 with DI+ > DI− + liquidity ≥ 1 bn VND per day.
  - (a) also needs the daily trigger; (c) has no trigger.
  - Ranking by weekly ADX (the v4 pick made on TRAIN).
- **Sizing:** max 10 names; each new position = 10 % of equity (or the cash left).
- **Sell reasons:** the phase is bad (active every bad day), or a monthly MACD+Sto sell (stays pending once it fires).
  - A reason executes at the next open only if the position is in net profit at that close: close × (1 − 0.25 %) > fill × (1 + 0.15 %).
  - No stop loss. After 10 years the position is sold at the next open whatever the price. A losing position keeps its slot.

**Verdict.**
- **v5 "wins" on almost every closed trade but loses as a portfolio.**
  - 89–96 % of closed trades are in profit (average +7 % to +12 %).
  - The losers are never sold: they pile up and lock the slots.
- **Worse than the plain phase filter in every period:**
  - (a): TRAIN −0.7 %, TEST +4.2 %, FULL +0.3 %/yr, max drawdown −53 %.
  - (c): TRAIN +1.9 %, TEST +5.8 %, FULL +2.9 %/yr, max drawdown −37 %.
  - Phase filter: +11.5 / +10.6 / +11.1 %/yr, max drawdown −38 %. TEST is also below EW buy & hold (+7.3 %).
- **Random picks from the same pool:**
  - (c): random runs do as well (mean TEST +5.8 %; 70 % of runs ≥ real on FULL).
  - (a): TEST is better than random (1.5 % of runs ≥ real), but FULL is not (63 %) and the level, +4.2 %/yr, is low.
- **Stuck capital:**
  - On 2026-11-19 all 10 open positions are at a loss, in both variants: unrealized −1.32 bn VND for (a) and −1.85 bn for (c). Final equity is 1.08 bn and 2.13 bn.
  - Worst positions: DIC −93 %, APC −94 %, TJC −84 % (TRAIN), FIR −90 % (TEST).
  - On average 30 % of capital sits in losing positions (TEST ≈ 50 %).
  - All 10 slots hold losers on 21–25 % of all days (36–39 % of TEST days). Since 2013 that happens in every year (14 years for (a), 16 for (c)), so most of the time the strategy cannot buy anything new.
- **Holding time:** median 33–39 days for closed trades, average 205–244 days because of the long stuck positions.
- **Concentration:** without its best symbol (DLG / CSC), FULL is +0.1 % / +2.9 %.
- **Per year:** 2022 −45 % (a) and −24 % (c), against +6 % for the phase filter. Losers cannot be cut, so the crash is held to the bottom.

| | TRAIN | TEST | FULL | max DD FULL | closed trades in profit | open at end with a loss (unrealized) | random runs ≥ real (TEST / FULL) |
|---|---|---|---|---|---|---|---|
| v5 (a) daily trigger | −0.7 % | +4.2 % | +0.3 % | −53 % | 89 % of 151 | 10 of 10 (−1.32 bn) | 1.5 % / 63 % |
| v5 (c) no trigger | +1.9 % | +5.8 % | +2.9 % | −37 % | 94 % of 206 | 10 of 10 (−1.85 bn) | 48 % / 71 % |
| phase filter | +11.5 % | +10.6 % | +11.1 % | −38 % | | | |
| EW buy & hold | −8.4 % | +7.3 % | −1.0 % | −88 % | | | |

**Per symbol (100 % of capital in one stock, same rules):**
- (a): 525 of 1,505 symbols trade. Of these, 84 % have every closed trade in profit, but 18 % are now stuck in an open losing trade (median −58 %). Only 39 % of symbols beat their own buy & hold (36 % of the traded ones).
- (c): 710 symbols trade. 67 % have every closed trade in profit, 38 % are stuck in a losing trade (median −55 %), and 38 % beat buy & hold.

**Survivorship stress (read this):**
- The data has **no symbol that stopped trading before 2024**. Delistings from 2000–2023 are simply missing.
- 182 symbols stop before 2026-10-20 (33 in 2024, 14 in 2025, 135 in 2026; some are only suspended or sparse).
- In the main run, a position in a stock that stops trading is valued at its last close for ever and keeps its slot.
- Stress run: write such positions off to 0 on the day after their last trade.
  - (c) FULL drops to +2.6 %/yr (max drawdown −40 %); worst position PCG −100 %.
  - (a) is unchanged: it held none of these stocks.
- Because older delisted stocks (often the ones that fell and never recovered) are missing, **"never sell at a loss" is flattered here**. In reality some stuck positions would have gone to zero.

Excel: new sheets `v5 chi ban khi lai - tong hop`, `v5 danh sach lenh`, `v5 theo nam`, `v5 tung ma`.
