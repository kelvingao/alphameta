# AlphaMeta Skills

![Skills](https://img.shields.io/badge/Skills-12-green?style=flat-square)
[![WeChat](https://img.shields.io/badge/WeChat-Group-C5EAB4?style=flat&logo=wechat&logoColor=white)](https://github.com/intelliscale/.github/blob/main/profile/QR.png)

AlphaMeta makes your AI assistant:
- Fluent in your broker — ask about stock prices, your portfolio, positions, orders, and valuations in plain English or 中文, backed by real Interactive Brokers data
- Fluent in quant trading — ask about trend analysis, trading signals, backtesting, and algo trading strategies in plain English or 中文, powered by real-time market data and quantitative models

12 skills covering market data, fundamentals, technical analysis, trading, portfolio, automation, quant, watchlist, utilities, market intelligence, earnings, and base infrastructure across stocks / options / futures / crypto.

## Install

```bash
# Install everything globally (~/.claude/skills/)
npx skills add intelliscale/alphameta-skills -g

# Or just one skill, globally
npx skills add intelliscale/alphameta-skills -g --skill alphameta-trading
```

---

## Update

```bash
# Update all skills
npx skills update -g

# Update a single skill
npx skills update alphameta-trading -g
```

---

## What you can ask

Ask your AI assistant naturally (supports 中文 / English):

- *"我的 NVDA 持仓现在盈亏如何？"* / *"How is my NVDA position doing?"*
- *"帮我买入 10 手 SPY 260530 500 看跌期权"* / *"Buy 10 SPY May 30 500 puts"*
- *"计算 GLD260501P440 的 delta 和 gamma"* / *"What's the delta on GLD260501P440?"*
- *"当 TSLA 跌破 150 美元时平仓"* / *"Close my TSLA position if it drops below $150"*
- *"显示 GLD 期权链，IV 排序"* / *"Show me GLD option chain sorted by IV"*
- *"给我今天的晨报"* / *"Generate my morning market briefing"*

---

## What's inside

| Group | Skills |
|---|---|
| **Foundation** | [`alphameta`](skills/alphameta/SKILL.md) — Server setup, command execution, and command search reference; used by all other skills |
| **Market Data** | [`alphameta-market-data`](skills/alphameta-market-data/SKILL.md) — Quotes, k-line, option chains, market depth, intraday, pattern recognition |
| **Fundamentals** | [`alphameta-fundamental`](skills/alphameta-fundamental/SKILL.md) — Financial statements, analyst consensus, SEC filings, institutional flows, insider trades |
| **Technical Analysis** | [`alphameta-technical`](skills/alphameta-technical/SKILL.md) — Greeks, IV/HV, max pain, GEX, k-line patterns |
| **Trading** | [`alphameta-trading`](skills/alphameta-trading/SKILL.md) — Options strategies, place/modify/cancel orders, multi-leg combos |
| **Portfolio** | [`alphameta-portfolio`](skills/alphameta-portfolio/SKILL.md) — Positions, P&L, balance, margin, risk analysis, hedging, portfolio diagnosis |
| **Automation** | [`alphameta-predicate`](skills/alphameta-predicate/SKILL.md) — Conditional triggers (price/RSI/EMA), scheduled tasks |
| **Quant** | [`alphameta-quant`](skills/alphameta-quant/SKILL.md) — Pairs trading, cointegration, vectorized backtesting |
| **Watchlist** | [`alphameta-watchlist`](skills/alphameta-watchlist/SKILL.md) — Named symbol groups, add/remove symbols, local persistence |
| **Utilities** | [`alphameta-utilities`](skills/alphameta-utilities/SKILL.md) — Calculator, calendar, TTS, paper trading, market strength reporter |
| **Market Intelligence** | [`alphameta-intelligence`](skills/alphameta-intelligence/SKILL.md) — Screener, top movers, morning brief, sector rotation, anomalies |
| **Earnings** | [`alphameta-earnings`](skills/alphameta-earnings/SKILL.md) — Pre & post-earnings analysis: Lite in-chat summary card (default) or full Markdown research report with valuation. DOCX report optional |

---

## Prerequisites

You need the AlphaMeta server running (for live quotes, your positions, orders):

```bash
# Install
pip install alphameta

# Start Server
alphameta --ibkr

# Check status
curl "http://127.0.0.1:18080/api/v1/health"
# → {"status": "ok", "ib_connected": true, "account_id": "U12345678"}
```

---

## Architecture

```
User Query → AI Assistant → AlphaMeta Skills → REST API → IBKR Gateway
                                   ↓
                            AlphaMeta Server (port 18080)
```

AlphaMeta runs as a local service connecting to IBKR, exposing a clean REST API that your AI assistant can call using natural language.