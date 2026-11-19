# SPEC – LEVEL 1 rules as backtested (causal; implementable on one stock's daily DataFrame + market series)

Reference implementation: `sig.py` (signals, stops, exits per stock) and `engine.py` (portfolio and sizing).
TEST 2020–2026 result: about +2.6 to +5.2 %/yr per timeframe and +6.7 %/yr for D+W+M combined, **below buy & hold (+9.9 %)**. See RESULT.md.

## 0. Inputs
- `df`: daily DataFrame of one stock, columns `open high low close` (adjusted), DatetimeIndex, own trading sessions only.
  If `open` is missing, use the previous close. Clip `high`/`low` so that they contain open and close.
- `liquid[t]`: 20-day average traded value ≥ 1e9 VND.
- Market: `I` = equal-weight index of liquid stocks (the VNINDEX proxy) and `risk_on[t]` = the bt_chuky phase filter (see `bt_chuky/SPEC.md` §1).

## 1. Timeframe bars
- D = daily.
- W = resample `W-FRI`: open = first, high = max, low = min, close = last. The bar's end day = the stock's last session in the week.
- M = calendar month, built the same way.
- A W/M bar is usable only when its period is over (today ≥ period end). The forming bar is never used.
- Indicators on each TF's bars: `MA6, MA10, MA20` = SMA of close; `ATR14` = SMA14 of the true range; `hug = SMA20(|close − MA10|) / ATR14`.

## 2. MA pair (signal MA / condition MA)
- Fixed: `(6, 10)` or `(10, 20)`.
- Adaptive (text: "if MA10 hugs price use MA10/MA20, else MA6/MA10"):
  - at bar j use `(10, 20)` if `hug[j] ≤ H_tf`, otherwise `(6, 10)`.
  - `H_tf` = median of `hug` over liquid TRAIN bars: D 0.874, W 0.848, M 0.820.
- The pair chosen at the position-order bar is kept for the whole episode.
- Chosen on TRAIN: D adaptive, W (6, 10), M (10, 20).

## 3. Position order (lệnh vị thế), at the close of TF bar j
1. Cross: `sig[x] > cond[x]` and `sig[x−1] ≤ cond[x−1]` for some x with `j − x ≤ 2`, and `sig > cond` on every bar from x to j.
2. Bar j is an up candle: `close[j] > open[j]`, and `close[j] > sig[j]` and `close[j] > cond[j]`.
3. Only one position order per cross. No new episode while one is live on this stock and TF.
   An episode ends at the full exit or when all its lots are stopped.

**Stop (đáy gần nhất dưới MA điều kiện):**
- Go back from j to the most recent bar k with `low[k] < cond[k]`. Look back at most 30 bars; if there is none, there is no trade.
- Extend k backwards while `low < cond` (one contiguous run).
- `stopP` = the minimum low of that run. It must be < `close[j]`.

**Fill:** at the next daily open. Skip the trade if `open ≤ stopP`.

## 4. Confirmation order (lệnh xác nhận)
- Trigger: the first TF bar m > j, before any partial or full exit signal and while the position lot is still open, with
  `close[m] > open[m]`, `close[m] > fill price of the position order` (in profit) and `close[m] > cond[m]`. At most one per episode.
- **Stop:**
  - Scan back from m over up to 20 bars with `low < cond`.
  - Take the most recent such bar whose low is at least 0.25·ATR14 below `cond` (text: "if too close to the MA, step back a few candles").
  - If none qualifies, take the lowest low among those bars. If there are no such bars at all, use `stopP`.
  - Must be < `close[m]`.
- **Fill:** at the next daily open (skip if open ≤ stop).

## 5. Exits (signals at the TF bar close, executed at the next daily open; stops intraday on daily bars)
- **Stops:** each lot keeps its own fixed stop.
  - Each day, if `low < stop` the lot is sold at `min(open, stop)`.
  - Open-time exits are processed before stops; the entry day itself is checked too.
- **Default ("q50" / "q70"):**
  - On the first TF close < `cond`: reduce every open lot to 50 % (or 30 %) of its original shares, rounded down to 100. This happens once.
  - On the first TF bar with `sig < cond` (cross-down): sell everything.
- **"q0" (BÍ KÍP 1, experienced trader):** no partial sale; hold until the cross-down or the stop. *Chosen for D and M.*
- **"bk3" (BÍ KÍP 3, for W and M trades):** lower TF = D for a W trade, W for an M trade.
  - Lower-TF pullbacks = runs of lower-TF closes below the lower-TF MA of the same condition period.
    Count those that start after the bottom (lowest daily low) of the trade's stop run.
  - When the 3rd or a later one starts (after the signal bar), keep 30 %.
  - Trade-TF close < `sig` → keep 50 %.
  - Trade-TF close < `cond` (or cross-down) → sell everything.
  - Keep levels are "at most x of the original shares", so they are never increased. *Chosen for W.*

## 6. Đồng pha (filters at the position-order bar)
- **Bigger-TF trend:**
  - D trade: the last completed W bar of the stock has `MA10 > MA20`.
  - W trade: the last completed M bar has `MA10 > MA20`.
  - M trade: always true (the market is the bigger TF).
- **Market filter** (one of):
  - `none`.
  - `phase`: `risk_on[t]`.
  - `idx`: equal-weight index `MA10 > MA20` on the last completed bar of the trade TF.
  - Chosen: D `idx`, W `none`, M `none`.
- **GĐ2 probe** (option, chosen for W):
  - If the bigger TF is not up, still allow the trade when there have been ≥ 2 down legs before it (see §7), with zone factor 0.3.
  - Without the probe option, trades against the bigger TF are skipped.
- `liquid` must hold at the position bar and the confirmation bar.

## 7. Leg counting (on the trade TF, condition MA of the episode)
- Pullbacks = maximal runs of bars with `close < cond`. Low of a pullback = the minimum low in the run.
  Use the last up to 12 runs ending at or before bar j.
- `up` = number of consecutive higher pullback lows going back from the latest one. **leg = up + 1**.
  A lower low resets the count to leg 1.
- `down_legs` = number of consecutive lower pullback lows going back from the latest one (used by the GĐ2 probe: ≥ 2).
- **Zone factor f:**
  - if the bigger TF is up and leg scaling is on: leg 1–2 → 1.0, leg 3 → 0.6, leg 4 → 0.4, leg ≥ 5 → 0.3. Leg scaling off → 1.0.
  - GĐ2 probe (bigger TF not up): 0.3.
  - Note: the text's "leg 1 = small TF up, big TF not yet" is the probe case (30 %).

## 8. Position sizing (account size A = equity at the previous close, VND)
- Stop money per opportunity:
  - D: 5 % (low) or 8 % (high) of A.
  - W: 8 % or 12 %.
  - M: 12 % or 20 %.
  - Chosen: D 5 %, W 12 %, M 12 %.
- Split equally over N names (N = 10 chosen): `zone = pct · A / N · f`.
- Position order money = 0.3 · zone. Confirmation money = 0.7 · zone.
- `shares = floor(money / (signal_close − stop) / 100) · 100`. Then cap by cash: `floor(cash / (fill · 1.0015) / 100) · 100`. Skip if < 100.
- At most N live stocks per TF. Same-day candidates are ranked by 20-day traded value (descending).
  D, W and M run side by side in one account, each with its own N slots.
- Fees: buy 0.15 %; sell 0.15 % + 0.1 % tax. No margin.
- Example (text): A = 1 bn, 8 % → 80 M stop money (N = 1): position order 24 M / (19,000 − 17,900) = 21,800 shares, rounded down to 100s.
  The text shows "2,200", which looks like a slip.

## 9. Output per signal (as in `now.json`)
`ma, tf, signal_bar, entry_ref (= signal close), stop, risk_pct, leg, down_legs_before, bigger_tf_up, probe_GD2, liquid,
allowed_by_chosen_rules, zone_factor, stop_money_vnd, shares, value_vnd`; for live setups also `fraction_still_held`, `gain_pct` and the confirmation's entry and stop.
