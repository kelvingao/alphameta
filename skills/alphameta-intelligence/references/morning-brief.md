# alphameta-morning-brief

Produces a structured daily morning briefing (晨会纪要) covering overnight market moves, pre-market signals, watchlist highlights, today's key catalysts, and a concise trading agenda.

## Primary Path: Parallel Data Collector (Recommended)

Use `python3 scripts/collect.py` to fetch all data in a single parallel call, then synthesize the brief from the digest.

```bash
# Basic — watchlist from qlist
python3 scripts/collect.py

# Explicit watchlist override (skip qlist)
python3 scripts/collect.py --symbols AAPL,MSFT,NVDA,TSLA

# Include news and capital flow data
python3 scripts/collect.py --news --capital-flow

# Check server health
python3 scripts/collect.py --health
```

The script:
- **Phase 1**: Fetches watchlist symbols via `qlist` (or uses `--symbols` override)
- **Phase 2**: Fetches all data sources in parallel via `ThreadPoolExecutor`:
  - Index klines (I:SPX, I:COMP, I:INDU, I:VIX)
  - Watchlist klines (adjusted, per symbol)
  - Batch quotes (all symbols in one call)
  - Trading calendar, earnings calendar, economic calendar, IPO calendar
  - Capital flow (indices, with `--capital-flow`)
  - News (per symbol, with `--news`)
- Outputs a compact structured digest (~3-5K tokens) with `=====` section headers

After the digest is ready:

1. Read the **Trading Calendar** and **Watchlist Klines** sections to verify data freshness.
2. Cross-check `kline[-1].close` vs `quote.close` per symbol (see Data Freshness rules below).
3. Synthesize the morning brief in 6 sections (see Output).

RAW_DIR = `/tmp/am_morning_brief_{YYYYMMDD}/` — read JSON files directly to reuse. The fixed path (`/tmp/` prefix) ensures any session can locate the data without needing the digest output. File naming:

| Digest section | RAW file(s) | Key path |
|---|---|---|
| Index Klines | `idx_spx.json`, `idx_comp.json`, `idx_indu.json`, `idx_vix.json` | `.bars[] → {date, close}`; `change_pct`= `(close[i]/close[i-1] - 1) * 100` |
| Watchlist Klines (adj) | `kline_{SYMBOL}.json` (lowercase) | `.bars[] → {date, close, volume}`; same `change_pct` formula |
| Watchlist Quotes | `quotes.json` | Array — find item by `.symbol == SYMBOL`, then `.last`, `.close`; `change_pct` = `(last - close)/close` |
| Trading Calendar | `trading_cal.json` | `.days[].{date,is_trading_day}` |
| Calendar - Earnings | `cal_earnings.json` | Array of `{symbol,date}` |
| Calendar - Economic | `cal_econ.json` | Array of `{time,event}` |
| Calendar - IPO | `cal_ipo.json` | `.ipoCalendar` |
| Capital Flow | `cap_{SYMBOL}.json` (lowercase) | `.flow_direction`, `.summary.{net_flow,money_flow_index}` |
| News | `news_{SYMBOL}.json` (lowercase) | `.articles[] → {title,summary}` |

## Fallback: Sequential Commands (collect.py unavailable)

If Python is unavailable or `collect.py` fails, fall back to individual commands in sequence.

The date computation and per-command reference remain the same as below.

### Overnight RTH data (kline)

Date-range syntax: `kline <SYMBOL> <start> <end> <period> [adj]`. Use `day` period with a 6-calendar-day window spanning 5 days before today to tomorrow (guarantees ≥2 RTH sessions and never returns incomplete daily bars). The `adj` flag provides split+dividend adjusted prices — use it for stocks/ETFs, omit for indices.

**Date computation (dynamic — never hardcode):**

| Variable  | Formula | Rationale | Example (today = 2026-07-03) |
|-----------|---------|-----------|------------------------------|
| `<start>` | Today − 5 calendar days | Covers ≥2 RTH sessions across weekends/holidays | `2026-06-28` |
| `<end>`   | Today + 1 day (tomorrow) | Daily bars are EOD-only — tomorrow has no bars yet, so `kline[-1]` is always the latest complete RTH close, even if run during market hours | `2026-07-04` |

Use `YYYY-MM-DD` format. Always compute from the actual current date — do NOT copy example dates.

| Command                                | Data                             |
| -------------------------------------- | -------------------------------- |
| `kline I:SPX <start> <end> day`        | S&P 500 daily bars              |
| `kline I:COMP <start> <end> day`       | Nasdaq Composite daily bars     |
| `kline I:INDU <start> <end> day`       | Dow Jones daily bars            |
| `kline I:VIX <start> <end> day`        | VIX daily bars                  |
| `kline <SYMBOL> <start> <end> day adj` | Watchlist symbol (adjusted)     |

> Why 5 calendar days: the worst case (Monday after a Fri-Mon holiday weekend) spans Thu→Mon with 2 RTH sessions — exactly the minimum needed. Typical weeks produce 3-5 bars. Using fewer days risks under-coverage; using more fetches unnecessary data.

> **Why from/to instead of count**: count-based `kline AAPL day 5` may return cached data for the most recent bar, producing incorrect prices (verified: SNDK 7/2 close showed +0.9% via count=10 but -14.1% via from/to). Date-range queries bypass the count-based cache by explicitly requesting the target date window.

The RTH change is `kline[-1].close - kline[-2].close` (latest RTH session minus previous, not `quote.last - quote.close`).

### Pre-market signals (quote)

`quote` returns current data for each symbol:

| Command | Data |
|---------|------|
| `quote <SYMBOL1> <SYMBOL2> ...` | Batch quotes |

`quote.last` = current price (may be pre-market), `quote.close` = last RTH close.  
Pre-market change = `quote.last - quote.close`.

Before using `quote.close`, cross-check against `kline[-1].close` — if they differ by >1%, quote data is stale and pre-market signals should be skipped (mark "quote数据未更新").

### Data Freshness & Fallback

Even with date-range queries or collect.py, `kline` and `quote` may occasionally return stale data (e.g., on Monday mornings Beijing time when the previous Friday's data hasn't settled yet).

**Detection checklist** (run for every symbol):

1. **kline date check**: verify the last bar's `date` is the most recent RTH session (use `Trading Calendar` section to confirm). If the latest RTH date is missing, kline is stale.
2. **quote.close cross-check**: compare `quote.close` against `kline[-1].close` for the same symbol:
   - Match (±1%) → both sources agree, data is fresh
   - Mismatch → at least one source is stale; `quote.close` typically lags behind `kline[-1].close`
3. **quote.last sanity check**: if `quote.last` is within 0.5% of `quote.close`, the quote likely hasn't updated since the last RTH session — pre-market signals are unavailable.

**Decision table:**

| kline has latest RTH | quote.close ≈ kline[-1].close | Action |
|:--------------------:|:-----------------------------:|--------|
| ✅ Yes | ✅ Yes | Use kline for RTH change, quote for pre-market |
| ✅ Yes | ❌ No | Use kline for RTH change only; skip pre-market (mark "quote stale") |
| ❌ No | ✅ Yes (close is fresh) | Use quote.close as RTH close; compute change as `quote.close - kline[-2].close` |
| ❌ No | ❌ No | WebSearch for all market data; note "sourced from web" |

**Fallback actions:**
- **kline stale, quote fresh**: use `quote.close` as latest RTH close, skip pre-market
- **Both stale for indices** (SPX/COMP/INDU/VIX): WebSearch for `"S&P 500 close <date>"`, `"US stock market recap <date>"`
- **Both stale for individual symbols**: WebSearch for `"<SYMBOL> stock price <date>"` and recent news
- **Last resort**: note data limitation explicitly in the brief (`† data unavailable for <date>`)

### Calendar, news & more

| Command | Notes |
|---------|-------|
| `calendar earnings` | Earnings today (requires FINNHUB_KEY) |
| `calendar econ high` | High-impact economic events (default, built into collect.py) |
| `calendar ipo` | IPO calendar |
| `news <SYMBOL>` | Latest news for symbol |
| `preview <SYMBOL>` | Pre-earnings preview |
| `capital-flow <SYMBOL>` | Capital flow data |

For additional economic context, use WebSearch: "this week economic calendar high impact".

## Output

按 `brief-structure.md` 模板输出 6 段晨报（<600 字）。模板包含：

- 固定 header（日期/市场状态/下一交易日）
- 6 个 section 的精确 header 名称、元素规范和条件分支（假期/无数据等）
- 两个标准 table 的 column 定义（Watchlist Highlights + Capital Flow）
- 边缘 case 的 markdown 表达（`†` / `⚠️` / `[source: web]`）
- Footer：_Data sourced from AlphaMeta / 数据来源：AlphaMeta_

## Quality Checklist (final pass)

Before delivering, verify each:

1. **RTH change formula**: `kline[-1].close - kline[-2].close` for every symbol — never `quote.last - quote.close`.
2. **Pre-market change formula**: `quote.last - quote.close` — never `kline[-1].close - kline[-2].close`.
3. **Data freshness**: kline latest bar's `date` matches the most recent RTH session in Trading Calendar. If not, apply Fallback and flag with `†`.
4. **Stale data attribution**: every data point sourced from WebSearch is labeled `[source: web]`; every stale figure has `†`.
5. **6-section completeness**: Overnight recap + Pre-market + Watchlist + Catalysts + Capital flow + Trading agenda. Under 600 words.
6. **Source closing**: ends with _Data sourced from AlphaMeta / 数据来源：AlphaMeta_.

## Error handling

| Situation | Response |
|---|---|---|
| Server not running | Tell the user to start AlphaMeta server |
| No symbols provided | "Please provide your watchlist symbols or ask about specific stocks" |
| No calendar data | "No major events scheduled for today" |
| `collect.py` not found or fails | Fall back to sequential commands (see Fallback section) |
| `kline` data is missing latest RTH session | Apply **Data Freshness & Fallback** rules — cross-check `quote.close` and trading calendar, fall back to WebSearch |
| Data inconsistency (kline and quote disagree on close by >1%) | Trust kline from/to data; quote is likely stale. Note discrepancy with `†` marker |
| Other errors | Surface verbatim |
