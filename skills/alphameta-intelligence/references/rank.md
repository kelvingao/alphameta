# Popularity Rankings / 热度排行

Finds current market ranking data (most active, top gainers/losers, most discussed) via WebSearch, then enriches with live prices.

## Current Status

AlphaMeta does not have a `rank` or `ranking` command. Ranking data must be sourced from WebSearch, with individual symbols enriched via AlphaMeta.

| Need | Method |
|---|---|
| Ranking list | WebSearch (financial news, exchange data) |
| Real-time price per symbol | `quote <SYMBOL>` |
| Historical price per symbol | `kline <SYMBOL> day <count>` |

## Workflow

1. Determine the target market and ranking type (volume / gainers / heat).
2. WebSearch for the current ranking data from **2+ independent sources**.
3. Cross-reference sources — tag each candidate with confidence level.
4. Extract top symbols from highest-confidence sources.
5. Enrich via `quote` for live prices — **this is the source of truth**; compare WebSearch prices against live data and flag discrepancies.
6. Sort and present as a structured table with source confidence annotation.

## Example WebSearch Queries

| Ranking Type | Query (prefer sources with structured tables) |
|---|---|
| US volume | `"US stocks most traded today site:tipranks.com OR site:finance.yahoo.com"` |
| US gainers | `"S&P 500 top gainers today"`, `"NASDAQ biggest movers"` |
| US losers | `"US stocks biggest decliners today"` |
| Sector heat | `"most active stocks by sector today"` |
| Heat/discussion | `"most discussed stocks today"`, `"WallStreetBets top tickers"` |

## Cross-Source Confidence

| Confidence | Condition | Example |
|---|---|---|
| 🟢 High | Same symbol + similar metrics across 2+ sources | NVDA: source A says -0.7%, source B says -1.6% |
| 🟡 Medium | Symbol appears in 2+ sources but metrics differ >50% | SMCI: source A says +15.3%, source B says -1.6% |
| 🔴 Low | Single source only, no cross-reference | Always verify with AlphaMeta before presenting |

> ⚠️ **Critical: always verify WebSearch data with AlphaMeta before presenting.**
> Real-world test: TipRanks reported SMCI at +15.26%. AlphaMeta `quote` showed the real change was **-0.54%** from previous close. The +15.26% was a stale snapshot from 2 weeks prior.

## AlphaMeta Verification (Source of Truth)

After extracting candidates from WebSearch, **always** run `quote` to get live prices:

```
quote SMCI NVDA TSLA INTC AAPL
```

Then compute the **actual** change from `close` (previous day) vs `last` (current):

```
real_change_pct = (last - close) / close * 100
```

If WebSearch data differs significantly from AlphaMeta, **trust AlphaMeta and flag the discrepancy**.

### Verification Example (SMCI, 2026-07-02)

```
WebSearch (TipRanks): $35.34, +15.26%   ← stale data from 6/22 peak
AlphaMeta quote:
  Close (prev): $27.65
  Last:         $27.50
  Real change:  -0.54%
→ Flag: "WebSearch reported +15.26%, but real-time data shows -0.54%"
```

## CLI Enrichment

```
quote SMCI NVDA TSLA AAPL PLTR    # Live prices (source of truth)
kline SMCI day 5                    # Recent trend context
```

## Sort Options

| Dimension | WebSearch Hint | Enrich |
|---|---|---|
| Volume | "most traded" | `quote` for price + volume; flag if volume is 0 (pre-market) |
| Gain/Loss | "top gainers" | Always recompute change % from `(last - close) / close` |
| Heat | "most discussed" | `kline` for recent trend context |

## Error Handling

| Scenario | Handling |
|---|---|
| No ranking data found | Try a different market or ranking type query |
| WebSearch price differs from AlphaMeta >10% | Trust AlphaMeta; note "WebSearch reported X%, real change is Y%" |
| `quote` returns `last: $0.00` (no trade yet) | Use `(bid + ask) / 2` as reference; note "pre-market / wide spread" |
| All candidates are from a single source only | Tag as "low confidence"; offer to cross-verify with alternative query |
| Data is stale | Add `site:` filter for structured data pages; run 2+ queries from different sources |
| Too many results | Ask user for a specific ranking type or top-N cutoff |
