---
name: alphameta-intelligence
description: |-
  Market intelligence: strategy screener, popularity rankings, top movers with news correlation, quote anomalies, index/ETF constituent stocks, morning briefings, ETF fund flow, market microstructure, and catalyst monitoring.
  Triggers: "筛选", "策略筛选", "排行", "热度", "异动", "成分股", "晨报", "早报", "ETF资金流", "screener", "rank", "anomaly", "constituent", "top movers", "morning brief", "ETF flow", "market intelligence", "市场强度", "资金流向", "事件日历", "今天财报", "市场微观结构"
---

# AlphaMeta Insights

Market intelligence hub — screening, scanning, briefing, and thematic research via AlphaMeta.

> **Response language**: match the user's input language — Simplified Chinese / English.

See the [alphameta](../alphameta) skill for server setup and command execution syntax.

## When to use

Trigger when user asks about: strategy screening, popularity rankings, top movers / market scanning, quote anomalies / unusual movements, index/ETF constituent stocks, morning market briefing, catalyst monitoring, ETF fund flow analysis, or market microstructure.

For raw data (quotes, kline, calendar) refer to the respective dedicated skills.

## Sub-topic Routing

| User intent | Load references file |
|---|---|
| Strategy screener | references/screener.md |
| Popularity rankings / 热度榜 | references/rank.md |
| Top movers / market scanning | references/top-movers.md |
| Quote anomalies / unusual moves | references/anomaly.md |
| Index / ETF constituent stocks / 成分股 | references/constituent.md |
| Morning briefing / 晨报 | references/morning-brief.md |
| Market pulse / 行情扫描 | references/market-pulse.md |
| Catalyst radar / watchlist scan | references/catalyst-radar.md |
| Event radar / 事件日历 | references/event-radar.md |
| ETF analysis framework | references/etf-analysis.md |
| ETF fund flow / ETF资金流 | references/etf-flow.md |
| Market microstructure / 市场微观结构 | references/market-microstructure.md |

## CLI Commands

All commands run via AlphaMeta's `POST /api/v1/execute`. Discover available commands:

```bash
curl http://localhost:18080/api/v1/search
```

Check the relevant reference file for specific commands per insight type.

## Frameworks

### Morning Brief
Pre-market summary: overnight moves, watchlist highlights, today's catalysts, and trading agenda.

**Primary path**: Run the parallel data collector, then synthesize from the digest:

```bash
python3 scripts/collect.py                              # Watchlist from qlist
python3 scripts/collect.py --symbols AAPL,MSFT,NVDA     # Explicit symbols
python3 scripts/collect.py --news --capital-flow         # Include news & capital flow
```

See [references/morning-brief.md](references/morning-brief.md) for the full workflow, data collection, and File Layout. Output format follows [references/brief-structure.md](references/brief-structure.md).

### Market Pulse
Market strength assessment and capital flow scanning using `reporter`, `advice`, and `capital-flow`. See [references/market-pulse.md](references/market-pulse.md).

### Event Radar
Earnings calendar, economic calendar, IPO calendar, and pre-earnings previews. See [references/event-radar.md](references/event-radar.md).

### Catalyst Radar
Multi-dimension catalyst scanning across watchlist: news, insider trades, earnings, analyst revisions. See [references/catalyst-radar.md](references/catalyst-radar.md).

### Screener
Stock screening by valuation, consensus, and financial metrics — with WebSearch fallback for bulk multi-criteria screening. See [references/screener.md](references/screener.md).

### Popularity Rankings
Stock popularity heat rankings by trading activity, media coverage, and community discussion — via WebSearch with AlphaMeta price enrichment. See [references/rank.md](references/rank.md).

### Constituent Stocks
Index and ETF constituent stock lists for market structure analysis — via WebSearch with AlphaMeta quote enrichment. See [references/constituent.md](references/constituent.md).

### ETF Analysis
Five-dimension ETF evaluation: product profile, tracking error, liquidity, premium/discount, allocation fit. See [references/etf-analysis.md](references/etf-analysis.md).

### ETF Fund Flow
US ETF sector rotation signals from capital flow and volume trend analysis across 11 SPDR sector ETFs. See [references/etf-flow.md](references/etf-flow.md).

### Market Microstructure
Order book depth, bid-ask spread analysis, depth asymmetry, order-flow pressure, and order-wall detection. See [references/market-microstructure.md](references/market-microstructure.md).

## Auth requirements

All CLI commands: Public — no login required.

## Error handling

| Situation | Response |
|---|---|
| Server not running / connection refused | Tell the user to start AlphaMeta server: `alphameta --ibkr` |
| Command not found | Run `curl http://localhost:18080/api/v1/search` to list available commands |
| Empty data returned | "No data available for the requested symbol or time range" |
| Other errors | Surface verbatim |

## MCP fallback

If AlphaMeta server is unavailable, use WebSearch to supplement market intelligence data.

## Related skills

| User wants | Use |
|---|---|
| Real-time quotes, K-line, depth | `alphameta-market-data` |
| Candlestick / OHLCV data | `alphameta-market-data` |
| Analyst consensus / ratings | `alphameta-fundamental` |
| Insider trades / 13F holdings | `alphameta-fundamental` |
| SEC filings | `alphameta-fundamental` |
| Financial statements (three-statement analysis) | `alphameta-fundamental` |
| Calendar / utilities | `alphameta-utilities` |
| Technical indicators / Greeks | `alphameta-technical` |

## File layout

```
alphameta-intelligence/
├── SKILL.md
├── scripts/
│   └── collect.py              # Parallel data collector (pure stdlib)
└── references/
    ├── morning-brief.md · brief-structure.md   # Morning brief workflow + output template
    ├── market-pulse.md · event-radar.md        # Market scanning + event calendars
    ├── catalyst-radar.md · screener.md · anomaly.md  # Screening + anomaly detection
    ├── top-movers.md                           # Top movers discovery
    ├── rank.md · constituent.md                # Rankings + constituent lists
    ├── etf-analysis.md · etf-flow.md           # ETF evaluation + sector rotation flow
    └── market-microstructure.md                # Order book depth analysis
```
