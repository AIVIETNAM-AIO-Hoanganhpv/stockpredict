# SPEC – exit / sell plan and top estimate for one position (from research2, 2026-11-19)

Scope: one stock, daily OHLC DataFrame `df` (adjusted prices, index = trading dates, columns open/high/low/close),
one position (entry date, entry price, tool stop). Everything uses data up to the **close of the current day** only.
Honesty requirements (must be shown in the UI next to the numbers):
- "Trailing stop 4 ATR: better than the fixed 3R target in 2006–2019 and 2020–2026 tests (+1 pp per trade) but not
  statistically significant; the gain comes from strong trend years. Median trade still loses (about −1.1 ATR)."
- "The top price/time are statistical ranges for any stock, not a forecast. No method tested (Fibonacci, 3R, tool
  tp1, RSI, divergence) predicted tops better than these ranges."

## 1. Constants
```python
ATR_N        = 14      # Wilder ATR
TRAIL_K      = 4.0     # chandelier multiple
MAX_BARS     = 120     # time exit (trading bars, entry bar = bar 1)
PART_R       = 3.0     # optional partial at entry + 3R (see 5.3)
PART_FRAC    = 0.5
NEAR_STOP_K  = 0.5     # warning band, ATR
# empirical distributions (tool entries 2006–2026; random days give the same within ~0.2 ATR)
TOP_Q_ATR    = {25: 0.65, 50: 1.9, 75: 4.7, 90: 9.5}       # next top = ref + q*ATR   (zigzag 10 %)
TOP_REACH    = {1: 0.67, 2: 0.48, 3: 0.37, 4: 0.29, 6: 0.18}  # P(next top >= ref + k*ATR)
TOP_T_BARS   = {25: 1, 50: 6, 75: 18, 90: 44}               # bars from ref to that top
HOLD_Q_BARS  = {25: 6, 50: 15, 75: 29, 90: 44}              # bars held under this exit (all trades)
WIN_HOLD_Q   = {25: 25, 50: 35, 75: 50}                     # bars held, winning trades
EXIT_Q_ATR   = {10: -1.9, 25: -1.6, 50: -1.1, 75: 0.3, 90: 4.0}  # (exit - entry)/ATR_entry
WIN_EXIT_ATR = {25: 1.1, 50: 2.6, 75: 6.0}                  # winners only
```

## 2. Indicators
```python
pc  = close.shift(1).fillna(close)
tr  = max(high-low, |high-pc|, |low-pc|)
atr = Wilder(tr, 14)       # atr[0..12]=NaN, atr[13]=mean(tr[0..13]), atr[t]=atr[t-1]+(tr[t]-atr[t-1])/14
```

## 3. Inputs at entry
- `entry_bar` e = the bar whose **open** filled the buy (normally the day after the 'Mua' signal);
  `entry` = fill price; `atr0` = ATR at the signal bar (e − 1).
- `stop0` = tool `cat_lo` (zone low − 0.5 ATR, rounded) if it is < entry, else `entry − 1·atr0`.
  (Research option, post-hoc and optimistic: `stop0 = min(tool stop, entry − 2·atr0)` gave +0.3 pp more; not the default.)
- `R = entry − stop0` (must be > 0, else no trade).

## 4. Daily update (run after each close t ≥ e)
```python
HH[t]   = max(entry, max(high[e..t]))                      # highest high since entry, incl. today
trail   = HH[t] - TRAIL_K * atr[t]
stop[t+1] = max(stop[t], trail)      # stop[e] = stop0; never lowered; this is tomorrow's stop
bars_held = t - e + 1
```
Execution next day (t+1): a stop-loss sell order at `stop[t+1]`; if the day opens below it, sell at the open.
On the entry day the stop is `stop0`. If `bars_held == MAX_BARS` → sell at that day's close.
(Do not tighten the stop on RSI/overbought/Fib/`dh_*` signals – tested: lowers return.)

## 5. Outputs

### 5.1 Trailing stop level (updated daily)
`stop[t+1]` (round down to the price step: HOSE 10/50/100 đ by price band, HNX/UPCoM 100 đ). Also report
`dist_stop = (close[t] − stop[t+1]) / atr[t]` and `lock_in = (stop[t+1]/entry − 1)` (profit locked if > 0).

### 5.2 Status for a held position (evaluate in this order at close t)
1. **SELL ALL** if any:
   - `low[t] <= stop[t]` (stop was hit today – position should already be closed at `min(open[t], stop[t])`);
   - `close[t] < stop[t+1]` (closed below tomorrow's stop → sell at tomorrow's open);
   - `bars_held >= MAX_BARS`.
   Reason text: "chạm stop", "đóng cửa dưới stop", "hết 120 phiên".
2. **SELL PART** (optional mode, default ON only if the user wants to reduce risk) – first day with
   `high[t] >= entry + PART_R·R` and no partial sold yet → sell `PART_FRAC` at `entry + 3R` (limit) ; the rest keeps
   the same trailing stop. Must display: "Bán bớt giảm dao động nhưng trong kiểm định làm lãi trung bình giảm
   ≈0.5 %/lệnh". After the partial, status returns to HOLD/SELL ALL rules.
3. **HOLD** otherwise. Sub-flag **HOLD – near stop** if `dist_stop < NEAR_STOP_K`.

### 5.3 Sell price targets (bands, not forecasts)
Reference `ref` = `entry` before the first new high, afterwards `close[t]` (random-day distribution is the same), `a = atr[t]`.
- Next-top band: `T25 = ref + 0.65a`, `T50 = ref + 1.9a`, `T75 = ref + 4.7a`, `T90 = ref + 9.5a`.
- Probability table for the UI: P(reach ref+1a)=67 %, +2a 48 %, +3a 37 %, +4a 29 %, +6a 18 %.
- "Expected sell price" under the exit rule (from entry): `entry + EXIT_Q_ATR[q]·atr0` → P25/P50/P75 =
  entry −1.6 / −1.1 / +0.3 ATR; if the trade becomes a winner, typical exit entry + 1.1 / 2.6 / 6.0 ATR.
- If the tool's `tp1`/`tp2` are shown, label them "mục tiêu tham khảo – chỉ đạt ~20 % số lần".
- Optional partial target (5.2): `entry + 3R`.

### 5.4 Expected sell date range
Convert trading bars to dates with the exchange calendar (Mon–Fri minus VN holidays; fallback `pd.bdate_range`).
- From entry: P25/P50/P75/P90 = e + 6 / 15 / 29 / 44 bars (all trades); winners e + 25 / 35 / 50 bars;
  hard limit e + 119 bars (bar 120).
- Next top time from `ref` day: + 1 / 6 / 18 / 44 bars (P25/50/75/90).
- For an open position already held `b` bars, show the remaining hard limit `MAX_BARS − b` and, if in profit
  (`stop[t+1] > entry`), the winners' range shifted: max(b, 25)…50 bars.

### 5.5 Reference implementation
```python
import numpy as np, pandas as pd

def wilder_atr(df, n=14):
    h, l, c = df.high.to_numpy(float), df.low.to_numpy(float), df.close.to_numpy(float)
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
    atr = np.full(len(tr), np.nan)
    if len(tr) >= n:
        atr[n - 1] = tr[:n].mean()
        for i in range(n, len(tr)):
            atr[i] = atr[i - 1] + (tr[i] - atr[i - 1]) / n
    return atr

def ke_hoach_ban(df, entry_date, entry_price, tool_stop=None, partial=False, k=4.0, max_bars=120):
    """df: daily open/high/low/close up to today. Returns status + levels as of the last close."""
    df = df.sort_index(); atr = wilder_atr(df)
    o, h, l, c = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    e = df.index.get_loc(pd.Timestamp(entry_date)); a0 = atr[max(e - 1, 0)]
    stop = tool_stop if tool_stop is not None and tool_stop < entry_price else entry_price - a0
    R = entry_price - stop; hh = entry_price; part_day = None
    status, reason, t = "HOLD", "", e
    for t in range(e, len(df)):
        if l[t] <= stop:                                    # today's stop (set yesterday) was hit
            status, reason = "SELL ALL", f"chạm stop {stop:.0f}"; break
        if partial and part_day is None and h[t] >= entry_price + 3 * R:
            part_day = t
        hh = max(hh, h[t])
        stop = max(stop, hh - k * atr[t])                   # tomorrow's stop
        if t - e + 1 >= max_bars:
            status, reason = "SELL ALL", "hết 120 phiên"; break
        if c[t] < stop:
            status, reason = "SELL ALL", "đóng cửa dưới stop"; break
    b = t - e + 1; at = atr[t]
    if status == "HOLD":
        if part_day == t:
            status, reason = "SELL PART", f"bán {PART_FRAC:.0%} tại {entry_price + 3 * R:.0f} (3R)"
        elif (c[t] - stop) / at < NEAR_STOP_K:
            status = "HOLD – near stop"
    ref = entry_price if hh <= entry_price else c[t]
    return {"status": status, "reason": reason, "stop_next": stop, "bars_held": b, "bars_left": max_bars - b,
            "top_band": {q: ref + m * at for q, m in TOP_Q_ATR.items()},
            "top_reach_prob": {f"+{x}ATR": p for x, p in TOP_REACH.items()},
            "top_time_bars": TOP_T_BARS, "sell_date_bars_from_entry": {**HOLD_Q_BARS, "max": max_bars - 1},
            "partial_target": entry_price + 3 * R if partial else None}
```
(Uses the constants of section 1. SELL PART is reported on the day the 3R level is first touched. Round prices to the exchange step.)

## 6. Not recommended (tested, no out-of-sample value)
Fixed 2R/3R/4R targets as the main exit; MA20 close exit; selling on RSI>75/80, close > MA20 + 3–4 ATR,
Fib 1.272/1.618 touch, bearish divergence, `dinh_muc`/`dinh_so`/`dh_*`; point forecasts of the top from Fibonacci,
3R, tp1/tp2 or 52-week high; waiting for a limit fill in the lower half of the support zone.
