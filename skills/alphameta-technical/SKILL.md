---
name: alphameta-technical
description: 'Price technical indicators via AlphaMeta — MACD, RSI, KDJ, Bollinger Bands, EMA crossover, ADX, ATR, OBV computed from OHLCV kline data. Use when: "MACD", "RSI", "KDJ", "布林带", "布林", "ADX", "ATR", "OBV", "技术指标", "金叉", "死叉", "超买", "超卖".'
---

# AlphaMeta Technical

> **Response language**: match the user's input language (Simplified Chinese / Traditional Chinese / English).

See the [alphameta](../alphameta) skill for server setup and command execution syntax.

---

## Workflow

When the user asks for technical analysis on a symbol:

1. **Fetch 252 daily kline data** and save to a temp file
2. **Compute 8 indicators** via inline Python + pandas
3. **Present results** — composite buy/sell/neutral signal with indicator details

### Step 1: Fetch kline

```bash
curl -X POST "http://127.0.0.1:18080/api/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kline <SYMBOL> day 252"}' \
  > /tmp/<SYMBOL>_kline.json
```

Reuse the saved file on subsequent calls. Only re-fetch if the user requests a different symbol, timeframe, or explicitly asks for fresh data.

### Step 2: Compute indicators

Run the inline Python script from [references/technical.md](references/technical.md) against the saved kline data. The script computes 8 indicators, votes each ±1/0, and outputs a JSON result.

### Step 3: Format output

| Indicator | Value | Signal |
|---|---|---|
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

---

## Indicator Reference

| Indicator | Parameters | Bullish Signal | Bearish Signal |
|---|---|---|---|
| MACD | (12, 26, 9) | Histogram rising & positive | Histogram falling & negative |
| RSI | 14 | < 30 (oversold) | > 70 (overbought) |
| KDJ | (9, 3, 3) | J < 20 | J > 80 |
| Bollinger | (20, 2) | Price < lower band | Price > upper band |
| EMA cross | 50 / 200 | 50 above 200 (golden cross) | 50 below 200 (death cross) |
| ADX | 14 | ADX > 25 & DI+ > DI- | ADX > 25 & DI- > DI+ |
| ATR | 14 | Expanding (>1.1× SMA) | Contracting (<0.9× SMA) |
| OBV | 5-day | OBV rising | OBV falling |

- 7 directional indicators vote +1 / 0 / -1; ATR (vote=0) provides non-directional volatility context
- Composite: ≥ +3 → Buy, ≤ -3 → Sell, otherwise → Neutral

---

## Error Handling

| Situation | Response |
|---|---|
| `error.code == "COMMAND_ERROR"` | Surface `error.message` verbatim |
| File `/tmp/<SYMBOL>_kline.json` not found | Re-run step 1 to fetch the data first |
| No data returned | Symbol may not support historical data; try a different symbol |
| Insufficient history (< 60 bars) | Request more periods with `kline <SYMBOL> day 500` |
| `ModuleNotFoundError: pandas` | Run `pip install pandas` |

---

## Reference

For the complete Python code and detailed workflow, see [references/technical.md](references/technical.md).
