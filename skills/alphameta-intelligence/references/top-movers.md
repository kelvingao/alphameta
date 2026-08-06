# Top Movers / 异动扫描

Identifies stocks with significant price or volume movements and correlates them with recent news or events.

## Current Status

AlphaMeta does not have a dedicated top-movers scanner that correlates price movements with news. The closest available commands:

| Need | AlphaMeta Command | Status |
|---|---|---|
| Current price & change | `quote <symbol>` | ✅ Works — provides `close` (prev close), `last` (current), `bid`/`ask` |
| Capital flow | `capital-flow <symbol>` | ✅ Works — net flow, MFI |
| Price history | `kline <symbol> day <count>` | ✅ Works |
| Market strength signals | `advice` | ❌ Broken (server error) |
| News for a specific mover | `news <symbol>` | ❌ Returns empty |

## Single-Symbol Workflow

1. Identify a specific symbol from user input.
2. Run `quote <symbol>` to get current price and compute `change_pct = (last - close) / close`.
3. For deeper analysis, run `kline <symbol> day 5` for price trend context, `capital-flow <symbol>` for flow direction.

**Note**: Automated top-mover discovery (scanning all symbols and ranking by movement) is not available via the current AlphaMeta API. Ask the user for a specific symbol to analyze, or proceed to the **Automated Top Movers Discovery** below.

---

## Automated Top Movers Discovery / 自动异动发现

When the user asks **"what's moving today"**, **"top gainers"**, **"biggest movers"**, or **"今天什么股票在涨/跌"**, use WebSearch to discover current movers, then enrich with AlphaMeta.

### Step 1 — Market & Session Selection

Determine which market and session the user wants:

| Market | Session | Timing (Beijing) |
|---|---|---|
| 🇺🇸 US (NYSE/Nasdaq) | Pre-market | ~17:00–21:30 |
| 🇺🇸 US | Regular hours | 21:30–04:00 (next day) |
| 🇺🇸 US | After-hours | 04:00–08:00 |
| 🇪🇺 EU | Regular hours | 15:00–23:30 (Beijing) |

If no market is specified, default to **US market regular hours** (most commonly requested).

### Step 2 — WebSearch Discovery

Construct targeted search queries based on the selected market and session:

**US Market:**

| Session | WebSearch Query |
|---|---|
| Pre-market movers | `"US stock market top gainers today premarket"` or `"premarket biggest movers today"` |
| Regular hours gainers | `"US stock market top gainers today"` or `"S&P 500 biggest gainers today"` |
| Regular hours losers | `"biggest stock losers today NYSE Nasdaq"` |
| By volume | `"most active stocks today by volume"` |
| By heat / social buzz | `"stocks trending today most discussed"` |
| Sector movers | `"sector movers today S&P 500"` |
| After-hours movers | `"after hours stock movers today"` |

### Step 3 — Parse & Rank Results

**⚠️ Critical: "today's" movers from WebSearch are usually YESTERDAY's close data.** StockAnalysis, StockMarketWatch, Investing.com report the previous trading day's movers. By real-time AlphaMeta `quote`, the moves may have partially or fully reversed. Always verify with `quote` before presenting.

Extract symbols, price changes, and volume data from search results. Filter out micro-cap stocks (<$100M market cap) which dominate gainers/losers lists and are often illiquid.

Example parsing from search results:
```
Top Gainers (Previous Close):
1. LHAI +172% — Acquisition + GPU financing (MCap: $44M, micro-cap)
2. SSTK -29% — Getty merger terminated (MCap: $2.1B, mid-cap)
3. MU -8.4% — Semis sector weakness (MCap: $95B, mega-cap)
4. SOC +43.9% — 18x volume surge (MCap: $679M, small-cap)
   → MCap labels help user decide which to investigate further
```

### Step 4 — Enrich Top Candidates with AlphaMeta (Phased Execution)

Select the **top 5-10 movers** (prioritize known mid/large-cap symbols, as `quote` can return $0.00 for illiquid micro-caps) and run enrichment.

#### Phase 1 — Data Freshness Check (run ALL candidates in parallel):

```text
quote <SYMBOL>    # Returns: {close: YESTERDAY close, last: current, bid, ask, volume}
```

From `quote` output, compute the **real-time change%**:
- `change_pct = (last - close) / close` (use `(bid+ask)/2` as fallback if `last = 0`)
- Compare with WebSearch-reported change%. If discrepancy > 10%, the WebSearch data is from a prior day.
- Example: WebSearch says LHAI +172% close; AlphaMeta quote shows close=$2.74, last=$1.74 → chg = **-36.5%** (move fully reversed)

#### Phase 2 — Deeper Analysis (for movers with confirmed current activity):

```text
capital-flow <SYMBOL>   # Net flow direction and MFI
kline <SYMBOL> day 10   # Multi-day trend context
```

**Data freshness confidence table:**

| WebSearch Δ | AlphaMeta `quote` Δ | Interpretation |
|---|---|---|
| +172% | -36.5% | ❌ Data is from prior day, move fully reversed |
| -29% | -1.01% | ❌ Most of the move has reversed, market digested the news |
| -8.4% | -2.36% | ⚠️ Partial reversal, trend may still be active |
| +5.8% | +5.2% | ✅ Data is current, move holding |

Always present AlphaMeta quote as the authoritative source. Add a freshness note: "WebSearch data is from [date]; AlphaMeta quote shows current price."

### Step 5 — Sort Options

Offer to sort/rank the movers by different dimensions per user preference:

| Sort By | Method | Example |
|---|---|---|
| By % Change (默认) | Rank by `(quote.last - quote.close) / quote.close` | NVDA +5.2%, AMD -3.1% |
| By Volume | Rank by `quote.volume` (from AlphaMeta real-time) | TSLA 45M shares, NVDA 32M |
| By Flow Intensity | Rank by `capital-flow` net flow (`summary.net_flow`) | NVDA +$380M, AMD -$95M |

### Step 6 — Output Structured Table

| Symbol | Last | Prev Close | Change% | Vol | Flow | Freshness |
|--------|------|-----------|---------|-----|------|-----------|
| NVDA | $142.50 | $135.50 | +5.2% | 32M | +$380M | ✅ Current |
| LHAI | $1.74 | $2.74 | -36.5% | 14K | -$386K | ❌ WebSearch data was +172% (yesterday) |
| SSTK | $9.80 | $9.90 | -1.01% | 15 | +$6.6M | ❌ WebSearch was -29% (yesterday, recovered) |
| SOC | $4.38 | $4.40 | -0.45% | 162 | — | ❌ WebSearch was +43.9% (yesterday, fully reversed) |

Add a **freshness confidence tag** for each mover:
- ✅ **Current** — AlphaMeta quote confirms the move direction and magnitude
- ⚠️ **Partial reversal** — WebSearch move still partially visible but reduced
- ❌ **Stale / Reversed** — WebSearch data from prior day, current price shows opposite direction

If there is no catalyst data from AlphaMeta (`news` returns empty), add catalyst from WebSearch with attribution: `"WebSearch reports: [reason]"`.

If presenting US pre-market movers specifically, add a header: `### Pre-Market Movers / 盘前异动`.

---

## WebSearch Fallback / WebSearch 兜底

| Situation | Response |
|---|---|
| WebSearch returns no movers | "Could not find top movers data. Try a different session (pre-market vs regular hours) or a specific symbol for single-symbol analysis." |
| WebSearch returns tickers but no prices | Extract tickers and use `quote` to backfill price data |
| WebSearch results seem stale | Add time qualifier: add "today" or the specific date to the query |
| User asks for real-time screen | "AlphaMeta does not support real-time top-mover scanning. WebSearch provides near-real-time data. Consider dedicated platforms (Finviz, TradingView) for live screens." |
| Only 2-3 movers found | Present what's available; note limited results |
| Cross-market requested | Run separate WebSearch queries per market; present in grouped sections |

## Errors / 错误处理

| Situation | Response |
|---|---|
| No market specified | Default to US regular hours; ask "Which market?" |
| `quote` returns last=$0.00 or stale | Use `(bid + ask) / 2` as fallback; if bid/ask also 0, mark as "no quote" |
| AlphaMeta change% differs from WebSearch >10% | Indicates WebSearch data is from prior day. Note: "WebSearch data from [prior session]; real-time quote shows [X]%." |
| `capital-flow` unavailable | Skip flow column; use WebSearch data instead |
| `news` returns no results | Add catalyst from WebSearch with attribution: "WebSearch reports: [reason]" |
| All top movers are micro-cap ($0–$100M) | Note: "Most top gainers are micro-cap stocks with limited liquidity. Quote data may be unreliable." |
| Server not running | "AlphaMeta server is not available. Top movers data limited to WebSearch results only." |
| User wants historical top movers | Run WebSearch with specific date: "top gainers [date]" |
