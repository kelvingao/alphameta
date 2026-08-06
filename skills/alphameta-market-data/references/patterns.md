# K-Line Pattern Recognition

Identifies 15 classic candlestick patterns from OHLCV data and produces a composite bullish/bearish/neutral signal.

## Workflow

1. **Fetch OHLCV data** via kline API (200 daily bars for sufficient context):

   ```bash
   curl -X POST "http://127.0.0.1:18080/api/v1/execute" \
     -H "Content-Type: application/json" \
     -d '{"cmd": "kline <SYMBOL> day 200"}'
   ```

2. **Run the Python analysis** on the returned `result.bars[]`
3. **Report** detected patterns (most recent first), each with date + name + interpretation + composite signal

## Python Analysis Script

```python
import pandas as pd, json, sys

data = json.loads(sys.stdin.read())  # list of OHLCV dicts
df = pd.DataFrame(data)
df = df.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"})
df[["o", "h", "l", "c", "v"]] = df[["o", "h", "l", "c", "v"]].apply(pd.to_numeric)

body = (df["c"] - df["o"]).abs()
rng = df["h"] - df["l"]
upper = df.apply(lambda r: r["h"] - max(r["c"], r["o"]), axis=1)
lower = df.apply(lambda r: min(r["c"], r["o"]) - r["l"], axis=1)
bull = df["c"] > df["o"]

signals, score = [], 0

# --- single-bar patterns (check last 5 bars) ---
for i in range(max(0, len(df) - 5), len(df)):
    r = df.iloc[i]
    b = body.iloc[i]
    u = upper.iloc[i]
    lo = lower.iloc[i]
    rg = rng.iloc[i]
    if b < 0.05 * rg:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "十字星/Doji", 0))
    elif lo > 2 * b and u < 0.1 * b and not bull.iloc[i]:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "锤子线/Hammer", +1))
    elif lo > 2 * b and u < 0.1 * b and bull.iloc[i]:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "锤子线/Hammer(bullish)", +1))
    elif lo > 2 * b and u < 0.1 * b and i > 0 and df["c"].iloc[i - 1] < df["c"].iloc[i]:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "吊颈线/Hanging Man", -1))
    elif u > 2 * b and lo < 0.1 * b and (bull.iloc[i - 1] if i > 0 else False):
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "射击之星/Shooting Star", -1))
    elif u > 2 * b and lo < 0.1 * b:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "倒锤线/Inverted Hammer", +1))
    elif b > 0.9 * rg and bull.iloc[i]:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "光头光脚阳线/Bullish Marubozu", +1))
    elif b > 0.9 * rg and not bull.iloc[i]:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "光头光脚阴线/Bearish Marubozu", -1))

# --- two-bar patterns ---
for i in range(max(1, len(df) - 5), len(df)):
    p, c_ = df.iloc[i - 1], df.iloc[i]
    if not bull.iloc[i - 1] and bull.iloc[i] and c_["o"] < p["c"] and c_["c"] > p["o"]:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "看涨吞没/Bullish Engulfing", +2))
        score += 2
    elif bull.iloc[i - 1] and not bull.iloc[i] and c_["o"] > p["c"] and c_["c"] < p["o"]:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "看跌吞没/Bearish Engulfing", -2))
        score -= 2
    elif not bull.iloc[i - 1] and bull.iloc[i] and c_["o"] < p["l"] and c_["c"] > (p["o"] + p["c"]) / 2:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "刺透线/Piercing Line", +1))
        score += 1
    elif bull.iloc[i - 1] and not bull.iloc[i] and c_["o"] > p["h"] and c_["c"] < (p["o"] + p["c"]) / 2:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "乌云盖顶/Dark Cloud Cover", -1))
        score -= 1

# --- three-bar patterns ---
for i in range(max(2, len(df) - 5), len(df)):
    a, b_, c_ = df.iloc[i - 2], df.iloc[i - 1], df.iloc[i]
    sb = body.iloc[i - 1]
    if not bull.iloc[i - 2] and sb < 0.3 * body.iloc[i - 2] and bull.iloc[i] and c_["c"] > (a["o"] + a["c"]) / 2:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "早晨之星/Morning Star", +2))
        score += 2
    elif bull.iloc[i - 2] and sb < 0.3 * body.iloc[i - 2] and not bull.iloc[i] and c_["c"] < (a["o"] + a["c"]) / 2:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "暮色之星/Evening Star", -2))
        score -= 2
    elif bull.iloc[i - 2] and bull.iloc[i - 1] and bull.iloc[i] and c_["c"] > b_["c"] > a["c"]:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "三白兵/Three White Soldiers", +2))
        score += 2
    elif not bull.iloc[i - 2] and not bull.iloc[i - 1] and not bull.iloc[i] and c_["c"] < b_["c"] < a["c"]:
        signals.append((df["time"].iloc[i] if "time" in df.columns else df["date"].iloc[i], "三黑鸦/Three Black Crows", -2))
        score -= 2

for _, _, s in signals:
    score += s

composite = "看多/Bullish" if score >= 2 else ("看空/Bearish" if score <= -2 else "中性/Neutral")
print(f"Composite score: {score}  →  {composite}")
for ts, name, s in signals:
    print(f"  {ts}  {name}  ({'+' if s >= 0 else ''}{s})")
```

## Output Template

```
**NVDA — K线形态分析 (最近 200 根日线)**

| 日期 | 形态 | 信号 |
|------|------|:----:|
| 2026-05-14 | 光头光脚阳线/Bullish Marubozu | +1 |
| 2026-05-13 | 三白兵/Three White Soldiers | +2 |

**综合信号: 看多/Bullish (score +3)**

解释: 连续出现强势看涨形态，多头动能强劲。
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll scan all 200 bars for patterns" | Only the last 5 bars matter for actionable signals. The 200 lookback is needed for EMA/rolling calculations only. |
| "score +2 from engulfing and score +2 from three soldiers = +4" | Correct — multi-bar patterns are pre-weighted; single-bar scores are added separately. |

## Important Notes

- **Only the last 5 bars matter** for actionable signals. The 200-bar lookback provides context for EMA/rolling calculations
- **Patterns need trend context** — a hammer after a long downtrend is bullish; a hammer at the top of a trend is unreliable
- **Low-volume patterns are less reliable** — cross-reference with volume if available
- **Doji is neutral** — indecision, not reversal. Only meaningful at trend extremes

## Error Handling

| Situation | Reply |
|---|---|
| Service not running | Start the service: `alphameta --ibkr` |
| `error.code == "COMMAND_ERROR"` | Surface `error.message` verbatim |
| No data returned | Symbol may not support historical data |
