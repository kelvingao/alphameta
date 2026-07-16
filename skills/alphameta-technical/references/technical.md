# Price Technical Indicators

Computes eight classic technical indicators from OHLCV data and produces a composite buy / sell / neutral signal via a multi-dimensional voting mechanism.

## Workflow

1. **Fetch 252 daily candles and save to a temp file:**

   ```bash
   curl -X POST "http://127.0.0.1:18080/api/v1/execute" \
     -H "Content-Type: application/json" \
     -d '{"cmd": "kline <SYMBOL> day 252"}' \
     > /tmp/<SYMBOL>_kline.json
   ```

   > Save the raw response to `/tmp/<SYMBOL>_kline.json`.
   > On subsequent calls (computing patterns, different indicators, or rechecking),
   > **reuse this file instead of re-fetching**. Only re-fetch if the user requests
   > a different symbol, timeframe, adjustment mode, or explicitly asks for fresh data.

2. **Compute indicators from the saved data:**

   ```bash
   cat /tmp/<SYMBOL>_kline.json | python3 << 'PYEOF'
   import pandas as pd, json, sys

   data = json.loads(sys.stdin.read())  # from result.bars[]
   df = pd.DataFrame(data)
   df = df.rename(columns={"open":"o","high":"h","low":"l","close":"c","volume":"v"})
   df[["o","h","l","c","v"]] = df[["o","h","l","c","v"]].apply(pd.to_numeric)

   votes = {}

   # EMA helper
   def ema(s, n): return s.ewm(span=n, adjust=False).mean()

   # --- MACD (12, 26, 9) ---
   ema12 = ema(df["c"], 12); ema26 = ema(df["c"], 26)
   macd = ema12 - ema26; signal = ema(macd, 9); hist = macd - signal
   votes["MACD"] = +1 if hist.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2] else (
                   -1 if hist.iloc[-1] < 0 and hist.iloc[-1] < hist.iloc[-2] else 0)

   # --- RSI (14) ---
   delta = df["c"].diff(); gain = delta.clip(lower=0); loss = (-delta).clip(lower=0)
   avg_g = gain.ewm(alpha=1/14, adjust=False).mean()
   avg_l = loss.ewm(alpha=1/14, adjust=False).mean()
   rsi = 100 - 100 / (1 + avg_g / avg_l.replace(0, 1e-9))
   rsi_last = rsi.iloc[-1]
   votes["RSI"] = -1 if rsi_last > 70 else (+1 if rsi_last < 30 else 0)

   # --- KDJ (9, 3, 3) ---
   low9  = df["l"].rolling(9).min(); high9 = df["h"].rolling(9).max()
   rsv   = (df["c"] - low9) / (high9 - low9 + 1e-9) * 100
   K = rsv.ewm(alpha=1/3, adjust=False).mean()
   D = K.ewm(alpha=1/3, adjust=False).mean()
   J = 3*K - 2*D
   votes["KDJ"] = +1 if J.iloc[-1] < 20 else (-1 if J.iloc[-1] > 80 else 0)

   # --- Bollinger Bands (20, 2) ---
   mid = df["c"].rolling(20).mean(); std = df["c"].rolling(20).std(ddof=0)
   upper_bb = mid + 2*std; lower_bb = mid - 2*std
   c_last = df["c"].iloc[-1]
   votes["Bollinger"] = +1 if c_last < lower_bb.iloc[-1] else (
                        -1 if c_last > upper_bb.iloc[-1] else 0)

   # --- EMA cross (50 / 200) ---
   e50 = ema(df["c"], 50); e200 = ema(df["c"], 200)
   votes["EMA_cross"] = +1 if e50.iloc[-1] > e200.iloc[-1] else -1

   # --- ADX (14) ---
   tr = pd.concat([df["h"]-df["l"], (df["h"]-df["c"].shift()).abs(),
                   (df["l"]-df["c"].shift()).abs()], axis=1).max(axis=1)
   dm_plus  = (df["h"]-df["h"].shift()).clip(lower=0)
   dm_minus = (df["l"].shift()-df["l"]).clip(lower=0)
   dm_plus  = dm_plus.where(dm_plus > dm_minus, 0)    # mutual exclusion
   dm_minus = dm_minus.where(dm_minus > dm_plus, 0)
   atr14 = tr.ewm(alpha=1/14, adjust=False).mean()
   di_plus  = 100 * dm_plus.ewm(alpha=1/14, adjust=False).mean() / atr14
   di_minus = 100 * dm_minus.ewm(alpha=1/14, adjust=False).mean() / atr14
   dx = (di_plus - di_minus).abs() / (di_plus + di_minus + 1e-9) * 100
   adx = dx.ewm(alpha=1/14, adjust=False).mean()
    votes["ADX"] = +1 if adx.iloc[-1] > 25 and di_plus.iloc[-1] > di_minus.iloc[-1] else (
                   -1 if adx.iloc[-1] > 25 and di_minus.iloc[-1] > di_plus.iloc[-1] else 0)

    # --- ATR (14) ---
    atr_sma = atr14.rolling(14).mean()
    atr_ratio = atr14.iloc[-1] / atr_sma.iloc[-1]
    votes["ATR"] = 0  # non-directional volatility measure
    atr_sig = "expanding" if atr_ratio > 1.1 else ("contracting" if atr_ratio < 0.9 else "normal")

    # --- OBV ---
   obv = (df["v"] * df["c"].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))).cumsum()
   votes["OBV"] = +1 if obv.iloc[-1] > obv.iloc[-5] else (-1 if obv.iloc[-1] < obv.iloc[-5] else 0)

   # --- Composite ---
   total = sum(votes.values())
   signal = ("买入/Buy" if total >= 3 else "卖出/Sell" if total <= -3 else "持观望/Neutral")

   print(json.dumps({
     "symbol": "<SYMBOL>",
     "period": "day",
     "bars": len(df),
     "composite": {"total": total, "signal": signal},
     "indicators": [
       {"name": "MACD",        "value": round(hist.iloc[-1], 4),  "vote": votes["MACD"],       "signal": "bullish" if votes["MACD"] > 0 else ("bearish" if votes["MACD"] < 0 else "neutral")},
       {"name": "RSI(14)",     "value": round(rsi_last, 1),       "vote": votes["RSI"],        "signal": "oversold" if rsi_last < 30 else ("overbought" if rsi_last > 70 else "neutral")},
       {"name": "KDJ",         "value": round(J.iloc[-1], 1),     "vote": votes["KDJ"],        "signal": "oversold" if J.iloc[-1] < 20 else ("overbought" if J.iloc[-1] > 80 else "neutral")},
       {"name": "Bollinger",   "value": round(c_last, 2),         "vote": votes["Bollinger"],  "signal": "oversold" if votes["Bollinger"] > 0 else ("overbought" if votes["Bollinger"] < 0 else "neutral")},
       {"name": "EMA50/200",   "value": round(e50.iloc[-1], 2),   "vote": votes["EMA_cross"],  "signal": "bullish" if votes["EMA_cross"] > 0 else "bearish"},
        {"name": "ADX(14)",     "value": round(adx.iloc[-1], 1),   "vote": votes["ADX"],        "signal": "trending" if adx.iloc[-1] > 25 else "choppy"},
        {"name": "ATR(14)",     "value": round(atr14.iloc[-1], 2), "vote": votes["ATR"],        "signal": atr_sig},
        {"name": "OBV",         "value": int(obv.iloc[-1]),        "vote": votes["OBV"],        "signal": "inflow" if votes["OBV"] > 0 else "outflow"}
     ]
   }, indent=2))
   PYEOF
   ```

3. **Parse the JSON output** — present indicator values, signals, and composite verdict to the user.

## Output

Present the indicator results as a table, using the JSON values parsed from the Python output:

| Indicator | Value | Signal |
|-----------|-------|--------|
| MACD | hist value | Bullish/Neutral/Bearish |
| RSI(14) | numeric | Oversold/Neutral/Overbought |
| KDJ | numeric | Oversold/Neutral/Overbought |
| Bollinger | price position | Oversold/Neutral/Overbought |
| EMA 50/200 | alignment | Bullish/Bearish |
| ADX(14) | numeric | Trending/Choppy |
| ATR(14) | numeric | Expanding/Normal/Contracting |
| OBV | numeric | Inflow/Outflow |
| **Composite** | total: N | **Buy/Sell/Neutral** |

Always cite the data source: AlphaMeta / Interactive Brokers.

## Error Handling

| Situation | Response |
|---|---|
| `error.code == "COMMAND_ERROR"` | Surface `error.message` verbatim |
| File `/tmp/<SYMBOL>_kline.json` not found | Re-run step 1 to fetch the data first |
| No data returned | Symbol may not support historical data; try a different symbol |
| Insufficient history (< 60 bars) | Request more periods with `kline <SYMBOL> day 500` |
| `ModuleNotFoundError: pandas` | Run `pip install pandas` |
