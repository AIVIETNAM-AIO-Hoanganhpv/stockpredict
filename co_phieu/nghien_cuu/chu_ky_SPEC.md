# SPEC – market phase filter + sector rotation (chosen on 2008–2019, tested once on 2020–2026)

All rules are causal: everything is computed at the **close of day t** and traded at the **open of day t+1**.
Inputs: `prices: dict[str, pd.DataFrame]` (daily, columns `open high low close`, adjusted, DatetimeIndex), `value20: dict[str, pd.Series]`
(20-day average traded value, VND), `sector: dict[str, str]` (ICB `nganh` from `ma_vn.csv`), `tnx: pd.Series` (Yahoo `^TNX` daily close).

## 0. Universe
`liquid(s, t) = value20[s][t] >= 1e9 and stock s has >= 60 bars of history and a close on day t`.

## 1. Market phase (approach 1, the core of the best strategy)
```python
def market_index(prices, liquid) -> pd.Series:
    """Equal-weight index of liquid stocks.
    r_t = mean over stocks s that were liquid on t-1 and have a close on t of  clip(close_t/close_prev - 1, -0.30, +0.40),
    close_prev = the stock's last known close before t.  I_t = prod(1 + r)."""

def breadth50(prices, liquid, t) -> float:
    """share of liquid stocks (with >= 50 bars) whose close > their own SMA50 (on ffilled close)."""

def classify_market(I: pd.Series, br50: pd.Series, ma_s=20, ma_l=100, b=0.60) -> pd.Series:
    MS, ML = I.rolling(ma_s).mean(), I.rolling(ma_l).mean()
    LT = MS > ML                     # long-term trend up
    S  = (I > MS) & (br50 >= b)      # short-term strength
    phase = np.select(
        [LT & S, LT & ~S, ~LT & S & (I > ML), ~LT & ((I > MS) | (br50 >= b))],
        ["Uptrend", "Distribution", "Accumulation-late", "Accumulation"], default="Downtrend")
    phase[ML.isna()] = "Downtrend"
    return phase

def macro_risk_off(tnx: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    """US 10y yield rose > 0.75 percentage points over 3 months.
    m = tnx.resample('ME').last(); d = m - m.shift(3)
    flag for month M is used from the 1st calendar day of month M+1 (publication lag), ffilled to daily."""

risk_on = phase.isin(["Uptrend", "Accumulation-late", "Accumulation"]) & ~macro_risk_off
```
So the strategy is out of the market only in **Distribution** (MA20>MA100 but index < MA20 or breadth < 60 %) and **Downtrend**
(MA20<MA100, index < MA20 and breadth < 60 %), or when the US 10y yield jumped > 0.75 pp in 3 months.
No smoothing (a phase is used from the first day). This flips about 17 times a year.

Phase colors for charts:
| phase | color | | phase | color |
|---|---|---|---|---|
| Uptrend | `#2ca02c` (green) | | Distribution | `#ffbb78` (light orange) |
| Accumulation-late | `#98df8a` (light green) | | Downtrend | `#d62728` (red) |
| Accumulation | `#ff9896` (light red/pink) | | | |

## 2. Sector ranking (approach 2; use only together with the phase filter)
```python
def sector_index(prices, liquid, sector) -> pd.DataFrame:
    """per ICB sector: equal-weight daily return of its stocks liquid on t-1 (same clip as above), cumulated."""

def rank_sectors(SI: pd.DataFrame, t, liquid, sector, ma50, look=63, min_n=3) -> pd.Series:
    """For sectors with >= 3 liquid stocks on t:
       ret  = SI[sec][t] / SI[sec][t-look] - 1          (63 trading days ~ 3 months)
       br   = share of the sector's liquid stocks with close > own SMA50
       score = rank(ret) + rank(br)   (ranks across sectors, ascending, ties = average) -> sort descending."""
```
Holdings: the **top 2 sectors**; buy **every liquid stock in them, equal weight, max 20 % per stock** (the rest stays in cash).
Rebalance (to equal weight, new ranking) on the **last trading day of every month** while risk-on, and on every day the
market switches from risk-off to risk-on (ranking computed that day). On a switch to risk-off: sell everything at the next open.

## 3. Best strategy = 1 + 2 ("regime + sector rotation")
Capital 1,000,000,000 VND; fees buy 0.15 %, sell 0.15 % + 0.1 % tax. TEST 2020-01 → 2026-11: CAGR +19.5 %, max DD −23 %.
Simpler and almost as good: **regime + whole liquid basket** (all liquid stocks equal weight, rebalanced monthly while risk-on): TEST +16.0 %, max DD −22 %.

## 4. Per-stock cycle estimate (approach 3) – for display only, it has NO predictive value
```python
def swing_lows(df, k=10) -> np.ndarray:          # bool; low[i] < min(low[i-k:i]) and low[i] <= min(low[i+1:i+k+1]); known at i+k
def cycle_estimate(df, k=10, m=6) -> dict:
    """lows confirmed by today (index <= today-k). Need >= 4 distances.
       T = median of the last m distances (bars) between consecutive lows; disp = IQR/T;
       z = (today - last_low) / T; expected-low window = last_low + [0.7T, 1.3T]; expected top = last_low + 0.5T."""
```
Test result: the stock's own T predicts the next low no better than a shuffled T from another stock (median error 10.5 vs 11.0 bars,
corr(T, next gap) = 0.03), and a single constant (28 bars) is better (9.0). Buying in the window was not better than buying outside it.

## 5. Exits (take-profit) – what the test says
For "risk-on + stock buy" entries (liquid stock, a 3-bar swing low just confirmed, higher than the previous swing low, close > previous close,
close > SMA50, market risk-on), the exit chosen on TRAIN was the **default**: hold until the market turns risk-off (sell next open),
with an initial stop at the entry swing low − 0.5·ATR(14) (intraday, fill at the stop or the open if it gaps below). Max hold 250 bars.
No amplitude, Fibonacci, time, Stochastic or MACD take-profit beat it on TRAIN; in TEST it made +14.2 %/yr (max DD −23 %).
Definitions used (for the app to display, single-stock DataFrame, pivots k=5 confirmed after 5 bars):
- A = swing low before B, B = last confirmed swing high, C = entry swing low (k=3), require C > A and index(C) > index(B).
- Amplitude / measured move (AB=CD): target = C + r·(B − A), r ∈ {0.618, 1.0, 1.272, 1.618, 2.0, 2.618} (Fib projection; r=1 is AB=CD).
- Fib extension of AB: A + r·(B − A), r ∈ {1.272, 1.618, 2.618}. Resistance: nearest confirmed swing high > 1.01·entry.
- Fib retracement stop: B − 0.618·(B − A) or B − 0.786·(B − A).
- Fib time: exit at the close of bar entry + round(r·(index(B) − index(A))), r ∈ {0.618, 1, 1.618}; typical up-wave = median of the last 6 (low→next high) durations.
- Stochastic (14,3,3): %K = SMA3(100·(C − LL14)/(HH14 − LL14)), %D = SMA3(%K); sell next open when %K crosses below %D with max(%K_t, %K_{t−1}) > 80.
- MACD (12,26,9) EMA-based; sell next open on MACD crossing below signal.

## Dài hạn (long-term rule: typical hold 9–12 months, max 12–24 months)
Chosen on 2008–2019 (TRAIN +9.5 %/yr) and tested once (TEST 2020–2026: +14.7 %/yr, max DD −30 %, turnover 1.5×/yr).
It beats equal-weight buy & hold, but **not** the short-term phase filter (+16 %, DD −22 %). The sample is small (≈7 non-overlapping 12-month periods in TEST).
```python
def long_term_entries(t_month_end) -> list[str]:
    """At the LAST trading day of each month (close):
       market risk_on (section 1) AND stock liquid (value20 >= 1e9) AND sector(stock) in top-2 of rank_sectors(..., look=63) at that day.
       Buy at the next open. Portfolio: max 10 positions x 10 % of equity, most liquid (value20) first, one position per stock,
       no new buys when 10 positions are open. Do not sell because the market turns risk-off."""

def long_term_exit(df_daily, entry_idx, H=252) -> int:
    """Monthly bars = calendar months of df_daily (close = last daily close of the month).
       Exit at the next open after a COMPLETED month whose close < SMA10 of monthly closes (10-month moving average);
       otherwise sell at the close of bar entry_idx + H - 1 (H = 252 bars ≈ 12 months; 378/504 are allowed, results were similar).
       No price target, no % stop (in TEST the -25 % stop added nothing)."""
```
In TEST the median actual hold was ≈ 5 months, because the 10-month-SMA exit fires first in weak markets. Win rate 35 %; the average trade
(+9 %) comes from a few big winners. No weekly/monthly take-profit was better on TRAIN: Stochastic, MACD, +50 %/+100 % targets and
AB=CD/Fib 1.618 weekly projections were all tested.
For display: weekly AB=CD target = C + r·(B − A). B = last weekly swing high (k = 2, confirmed 2 completed weeks later), A = the weekly swing low before B,
C = lowest daily low since B's week, valid only if C > A. r = 1.0 (AB=CD) or 1.618.
