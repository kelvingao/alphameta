# K-Line — Candlestick / OHLCV

Historical candlesticks and today's intraday minute curve for US equities and options via AlphaMeta (IBKR).

## Symbol Format

Stocks: plain ticker (`AAPL`, `NVDA`, `SPY`). Options are not supported for k-line.

## Modes

| Mode | Command | Use When |
|---|---|---|
| Latest N candles | `kline <SYMBOL> <PERIOD> <COUNT> [adj]` | "last 100 daily bars", "近一周走势" |
| History by date range | `kline <SYMBOL> <START> <END> <PERIOD>` | "NVDA 2024年日K", "Jan-Jun 2024" |
| Intraday today | `kline <SYMBOL> intraday` | "分时图", "today's intraday" |

Always discover current flags first:

```bash
curl "http://localhost:18080/api/v1/search?query=kline"
```

## Period Mapping

| Period | Aliases | Bar Size |
|---|---|---|
| `1m` | `minute` | 1 minute |
| `5m` | — | 5 minutes |
| `15m` | — | 15 minutes |
| `30m` | — | 30 minutes |
| `1h` | `hour` | 1 hour |
| `day` | `d`, `1d` | 1 day |
| `week` | `w` | 1 week |
| `month` | `m`, `1mo` | 1 month |

## Workflow

1. **Resolve symbol** — plain ticker
2. **Determine mode** — intraday vs history vs latest N:
   - Explicit "intraday" or "today" → intraday mode
   - Date-like first argument (YYYY-MM-DD, "today", "yesterday") → history mode
   - Otherwise → latest N candles mode
3. **Map time windows** — use trading-day counts:
   - "1-week" → `day, 5`
   - "1-month" → `day, 22`
   - "3-months" → `day, 66`
   - "6-months" → `day, 126`
   - "1-year" → `day, 252`
   - "today / intraday" → intraday mode
4. **Execute** via POST /api/v1/execute
5. **Interpret** — translate OHLCV to prose

## CLI Examples

```bash
# Latest 100 daily bars
curl ... -d '{"cmd": "kline AAPL day 100"}'

# Last 200 5m candles with split+dividend adjustment
curl ... -d '{"cmd": "kline NVDA 5m 200 adj"}'

# History by date range (daily)
curl ... -d '{"cmd": "kline AAPL 2025-01-01 2025-06-30 day"}'

# Today's intraday 1m chart
curl ... -d '{"cmd": "kline NVDA intraday"}'
```

## Output

The API returns `result.bars[]` with fields: `date`, `open`, `high`, `low`, `close`, `volume`, `average`.

```json
{
  "success": true,
  "request_id": "req-xxx",
  "result": {
    "symbol": "AAPL",
    "period": "day",
    "count": 5,
    "adjust": "none",
    "bars": [
      {
        "date": "2026-05-08",
        "open": 287.86,
        "high": 294.76,
        "low": 287.5,
        "close": 293.86,
        "volume": 39300184,
        "average": 293.118,
        "barCount": 258450
      }
    ]
  },
  "execution_time_ms": 2558
}
```

Variations by mode:
- **history**: `result` has `start`, `end` instead of `count`
- **intraday**: `date` is ISO 8601 datetime (e.g. `2026-05-14T09:30:00`), no `adjust` field

Always present as prose — never raw JSON:

```
**{Symbol} — {Period} ({N} bars, {date range})**
Range: ${high} ~ ${low}  |  Close-to-close: ${first_close} → ${last_close} ({sign}{X.Y%})
Volume: avg {X} shares/day — {volume pattern note}
Trend: {1-2 sentence summary of price action, key levels, and pattern}
```

### Examples

```
**NVDA — Daily (5 bars, May 6–12)**
Range: $196.16 ~ $223.75  |  Close-to-close: $207.26 → $219.48 (▲ +5.9%)
Volume: avg 126M shares/day — elevated throughout
Trend: Strong uptrend from $196 support, 5 consecutive green candles.
```

```
**NVDA — 1m Intraday (111 bars, May 14)**
Range: $229.36 ~ $233.22  |  Open: $231.34 → Now: $230.26 (▼ -0.5%)
Volume: heavy in first 2 minutes (1.4M shares), then tapered to ~10K/min
Trend: Opened with a spike to $233.22, then gradual selloff through the morning.
```

**Intraday output** should mention the opening spike/drop, session high/low, and whether volume confirms the trend. For multi-day history, highlight the directional bias, key support/resistance levels, and any volume anomalies.

**Net move** = `(last_close - first_close) / first_close` — always close-to-close, with ▲/▼ direction arrows.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "`day 30` is roughly one month" | 30 trading bars ≈ 6 calendar weeks. For one calendar month use `day 22` |
| "Net move = (last open − first open) / first open" | Always use close-to-close: `(last_close − first_close) / first_close` |
| "I'll pass the raw JSON to the user" | Raw JSON is unreadable. Must translate to prose: range high/low, net change, volume, trend |
| "Count = calendar days" | Count = number of bars, not days. `day 5` = 5 daily bars covering ~7 calendar days |
| "Intraday works for any past date" | Intraday mode only supports today. For historical minute data use history mode with `1m` period |
| "Count is the exact number of bars returned" | Count is a **minimum** — for longer periods (week/month) IBKR may return more bars than requested |

## Key Behaviours

- **Intraday is today-only** — calling intraday on a past date returns empty data. For historical minute bars use `kline <SYMBOL> <START> <END> 1m`
- **Data availability varies by instrument** — options, some ETFs, and crypto may return empty or very short histories. Verify with `quote` first
- **All modes include extended hours** — `useRTH=False` is hardcoded on the backend; the command does NOT accept a `useRTH` flag (any `useRTH` token is silently ignored). Mention this if the user expects strict trading-session data
- **`adj` only affects price fields** — split + dividend adjusted open/high/low/close; volume is never adjusted. Flag syntax only (`--adjust` prefix NOT supported)
- **Count is a minimum** — IBKR may return more bars than requested for week/month periods
- **History may include one extra bar** — IBKR includes the bar containing the start timestamp (e.g. `kline AAPL 2026-05-01 2026-05-07 day` may include a bar dated `2026-04-30`). Always compute the actual date range from the returned data

## Error Handling

| Situation | Reply |
|---|---|
| Service not running | Start the service: `alphameta --ibkr` |
| `error.code == "COMMAND_ERROR"` | Surface `error.message` verbatim |
| No data for the range | Expand the date range or switch to a shorter period |
| Empty intraday for past date | Intraday is today-only; use `kline <SYMBOL> <START> <END> 1m` instead |
