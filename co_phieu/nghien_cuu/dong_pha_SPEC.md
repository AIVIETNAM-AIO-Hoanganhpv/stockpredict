# SPEC – "Đồng pha" D/W/M strategy (enter on daily, hold and exit on weekly or monthly)

Reference code: `core.py` (`prepare`, `episodes`, `exit_events`). The UP rule is the same as GreenView
`greenview/src/js/stockpredict.js` (`xuHuongTang`, `App.dongPha`, `DEFS.st_dongpha`). Two small differences are listed at the end.

Input: one stock as a daily DataFrame `open, high, low, close` (adjusted), with one row per session, sorted by date.
Cleaning: a missing or ≤ 0 open is replaced by the previous close. `high = max(high, open, close)`, `low = min(low, open, close)`.
Nothing is ever read from a later bar. A signal is read at the bar close and filled at the **next daily open**.

## 1. Bars
- D = the daily rows.
- W = weeks ending Friday (`W-FRI`), built from the stock's own sessions: open = first open, high = max, low = min, close = last close.
- M = calendar months, built the same way.
- **Only completed W/M bars are used.** A week or month counts as completed once its calendar period has ended
  (in a live feed: the last session of the week or month has closed). On day *d*, the W/M state is the state of the last W/M bar
  whose last session is on or before *d*. On a Friday close, that week's bar is already complete.
- Tested as a variant only (not used): the partial bar up to *d*. MACD and Sto include the running bar; structure uses completed bars.

## 2. Indicators (TradingView definitions)
- `ema(x,n)`: alpha = 2/(n+1), seeded with the SMA of the first n values.
- MACD(12,26,9): `macd = ema(c,12) − ema(c,26)`, `signal = ema(macd,9)`, `hist = macd − signal`.
- Stoch(n,k,d): `raw = 100·(c − LL_n)/(HH_n − LL_n)`, `%K = sma(raw,k)`, `%D = sma(%K,d)`.
  Long Sto = (13,13,5). Short Sto = (8,5,3).
- Pivots on a TF with k = 3 (D) or k = 2 (W, M):
  - Bar *p* is a pivot high if `high[p] ≥ high[q]` for every q in [p−k, p+k]. A pivot low mirrors this with lows.
  - A pivot is known only at bar p+k (confirmed). Ties are allowed, so equal highs are both pivots.

## 3. "UP" on one timeframe (evaluated on each bar t of that TF)
Count the conditions that hold. **UP = at least 2 of the 3** (user decision; "all 3" was tested as a side row).
1. Structure: there are two confirmed pivot highs and two confirmed pivot lows (confirmation bar ≤ t), and
   last pivot high > previous pivot high **and** last pivot low > previous pivot low.
2. MACD line > signal line.
3. Long Sto %K > %D.

Reference only, not used in any rule: MA80% (at least 16 of the last 20 closes are above MA20) and Heikin-Ashi
(the last 3 HA candles are green; `ha_close = (o+h+l+c)/4`, `ha_open = (prev ha_open + prev ha_close)/2`, seeded with (o0+c0)/2).

## 4. Đồng pha
`dong_pha[d] = UP_D[d] AND UP_W[last completed week ≤ d] AND UP_M[last completed month ≤ d]`.

## 5. Daily buy signal (position order, 30 % of the trade's capital)
On day j, all of the following must hold: `dong_pha[j]`, a bullish candle (`close > open`), j ≥ 30, and one entry trigger.
The trigger depends on the variant:
- **2MA** (LEVEL 1 rules, adaptive pair):
  - Pair: if `sma(|c − MA10|, 20) / ATR14 ≤ 0.874`, use MA10/MA20. Otherwise use MA6/MA10.
    ATR14 = SMA14 of the true range.
  - The signal MA has crossed above the condition MA within the last 3 bars (the cross bar counts) and is still above it.
  - `close > signal MA` and `close > condition MA`.
  - Only the first qualifying bar per cross counts.
- **MACD+Sto**: Mua1 or Mua2 on the daily bar (definitions as in `bt_macd_sto/SPEC.md`):
  - Mua1 = bullish candle, short Sto %K crosses above %D, and the MACD histogram is < 0 and has risen for 2 bars.
  - Mua2 = bullish candle, and both Stos cross up on the same bar or within 1 bar of each other.
- **Either**: 2MA or MACD+Sto.

Order handling:
- Stop = the nearest confirmed daily pivot low (k = 3, confirmed by j) with a low below `close[j]`, searched back up to 60 bars.
  If there is none, use the lowest low of the last 10 bars. Skip the trade if `stop ≥ close[j]`.
- Fill at `open[j+1]`. Skip the trade if the fill is ≤ the stop.
- One trade at a time per stock (per trade type). A new position order needs a signal day on or after the previous trade's last exit day.

## 6. Confirmation order (70 %)
- This is the first day m > j, before the first exit or stop of the position order, where all of these hold:
  - `dong_pha[m]`;
  - `close[m] > position fill` (the position is in profit);
  - a confirmation trigger, which depends on the variant:
    - 2MA: a bullish candle that closes above the condition MA of the pair chosen at m;
    - MACD+Sto: XN1, XN2 or XN3 (XN2/XN3 touch threshold = 1 Sto point);
    - Either: either of the two.
- Stop = the same pivot rule, evaluated at m. Fill at `open[m+1]`, which must be > the stop.
- At most one confirmation order per trade. It follows the same exits as the position order.

## 7. Exits
Sell signal on a completed W bar ("lệnh tuần") or M bar ("lệnh tháng"): any of the mirrored MACD+Sto sell types, each on a bearish candle:
- SMua1: short Sto crosses down, and the histogram is > 0 and has fallen for 2 bars.
- SMua2: both Stos cross down (same bar, or within 1 bar).
- SXN1: SMua2 plus the falling-histogram condition.
- SXN2: short Sto crosses down, the histogram is falling, and the long Sto is touching (|%K − %D| ≤ 2, or it crossed down within 2 bars).
- SXN3: short Sto crosses down, the long Sto is touching, and MACD < signal after a cross-down within 10 bars.

Only W/M bars whose last session is on or after the fill day count. The exit fills at the **next daily open after that bar's last session**.

Two exit modes:
- **a**: sell everything at the first sell signal.
- **b**: sell 70 % at the first sell signal. Sell the rest at the next sell signal or at a MACD cross-down on the same TF, whichever comes first.

Stops are always active: if a daily low is ≤ a lot's stop, that lot exits at `min(open, stop)` that day.
Open-time exits are processed before the stop of the same day.

## 8. Sizing used in the tests
- Per symbol: 100 % of equity per trade (30 % position + 70 % confirmation), compounding, fees.
- Portfolio (VN, 1 bn VND, LEVEL 1 rules):
  - Stop money = risk × equity ÷ N. Risk choices: W 8 % or 12 %; M 12 % or 20 %.
  - Position order uses 30 % of the stop money and the confirmation order 70 %.
  - `shares = floor(money / (signal close − stop) / 100) × 100`, capped by cash.
  - At most N live names per trade type. Same-day signals are ranked by traded value. Liquidity: 20-day traded value ≥ 1 bn VND on the signal day.
- Fees: VN buy 0.15 %, sell 0.25 % (incl. 0.1 % tax). US, gold, BTC: 0.05 % per side.

## Differences from GreenView `DEFS.st_dongpha` (as of this run)
- 2MA entry: this backtest allows the bullish close up to 3 bars after the cross (LEVEL 1 rule). The JS version requires the cross on the same bar.
- Exit mode b: this backtest sells the rest at the next sell signal **or** a MACD cross-down. The JS version waits for the next sell signal only.
- Completed bars: the JS version always treats the last W/M bar of the data as unfinished. This backtest uses calendar completion.
