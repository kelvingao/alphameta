# Morning Brief Structure and Templates

> **When to use**: Every time the user requests a morning brief (晨报 / morning briefing). This reference provides the section-by-section structure for generating a 6-section daily briefing in Markdown. The output is delivered as a `.md` file saved to the user's Obsidian vault.

This document provides complete section-by-section templates, conditional branches, and formatting requirements for the daily morning brief.

> **Data source**: All data comes from the `collect.py` RAW_DIR JSON files (`idx_spx.json`, `idx_comp.json`, `idx_indu.json`, `idx_vix.json`, `kline_{SYMBOL}.json`, `quotes.json`, `trading_cal.json`, `cal_earnings.json`, `cal_econ.json`, `cal_ipo.json`, `cap_{SYMBOL}.json`, `news_{SYMBOL}.json`). Read them directly with `json.load(open(f'{RAW_DIR}/{file}'))`. Do not re-call CLI commands for data already collected. See `morning-brief.md` for the complete File Layout table.

## Contents

- [Header](#header) — date line, market status, next trading day
- [Section 1: Overnight RTH Recap](#section-1-overnight-rth-recap) — index close + change + trend commentary
- [Section 2: Pre-market Signals](#section-2-pre-market-signals) — futures direction, watchlist pre-market movers
  - [Normal Trading Day](#normal-trading-day) · [Holiday / Non-trading Day](#holiday--non-trading-day) · [Stale Data](#stale-data)
- [Section 3: Watchlist Highlights](#section-3-watchlist-highlights) — single table, sorted by RTH change
- [Section 4: Today's Catalysts](#section-4-todays-catalysts) — holidays, economic events, earnings, macro themes
- [Section 5: Capital Flow Signals](#section-5-capital-flow-signals) — inflow/outflow table
- [Section 6: Trading Agenda](#section-6-trading-agenda) — 2-4 actionable items
- [Footer](#footer) — source attribution
- [Conditional Section Map](#conditional-section-map) — when to skip/modify each section
- [Formatting Requirements](#formatting-requirements) — number format, price format, source annotations, word limit

---

## Header

**Top Section - Date & Status Line:**

```
# YYYY-MM-DD 晨会纪要

> 生成时间：YYYY-MM-DD HH:MM CST | 市场状态：[正常交易 / 假期休市 / 盘前] | 上一 RTH：YYYY-MM-DD | 下一交易日：YYYY-MM-DD HH:MM CST
```

**Market status** is determined from `trading_cal.json`:
- `is_trading_day=false` + `is_holiday=true` → "假期休市"
- `is_trading_day=true` and current time < `market_open_user` → "盘前"
- Otherwise → "正常交易"

**Next trading day**: the first entry after today where `is_trading_day=true`.   ← from `trading_cal.json`

---

## Section 1: Overnight RTH Recap

**Content — 4-6 bullets covering major indices:**

```
## 1. Overnight RTH Recap（[YYYY-MM-DD] 收盘）

- **SPX** [CLOSE]（[±CHANGE%]）— [one-sentence trend description]
- **COMP** [CLOSE]（[±CHANGE%]）— [one-sentence trend description]
- **INDU** [CLOSE]（[±CHANGE%]）— [one-sentence trend description]; add 🔺 for new all-time highs
- **VIX** [CLOSE]（[±CHANGE%]）— [direction + sentiment assessment]
```

- RTH Change = `(kline[-1].close / kline[-2].close - 1) * 100`   ← from `idx_spx.json`, `idx_comp.json`, `idx_indu.json`, `idx_vix.json`
- **Optional bullets**: commodities, forex, bond yields (if notable moves)
- Flag 250d highs/lows when breached   ← from `idx_*.json` → `250d_high` / `250d_low`

---

## Section 2: Pre-market Signals

### Normal Trading Day

**Content — Futures direction + pre-market movers table:**

```
## 2. Pre-market Signals

- **Index Futures**: [ES/NQ/YM direction from quote data; skip if unavailable]
- **Watchlist Pre-market Movers**: symbols where |quote.last - quote.close| > 1%

| Symbol | Last | RTH Close | Pre-market Change | Signal |
|--------|------|-----------|--------------------|--------|
| [SYM]  | [L]  | [C]       | [±X.XX%]          | [gap up / gap down] |
```

- Pre-market Change = `(quote.last - quote.close) / quote.close * 100`   ← from `quotes.json`
- **Data freshness gate**: cross-check `quote.close` vs `kline[-1].close`. If difference >1%, skip that symbol's pre-market data. See `morning-brief.md` §Data Freshness for full decision table.

### Holiday / Non-trading Day

```
## 2. Pre-market Signals

⚠️ 今日（[M/D]）为 [holiday name]，美股休市。无盘前交易数据。下一交易日：**[M/D]（[周X]）[HH:MM] CST** 开盘。
```

### Stale Data

```
## 2. Pre-market Signals

† 盘前数据未更新（quote.last 与 quote.close 差异 <0.5%，或 quote 数据整体过期）。跳过盘前信号。
```

---

## Section 3: Watchlist Highlights

**Content — Single table, all symbols sorted by RTH Change (largest decline → largest gain).** Extract key drivers from `news_{SYMBOL}.json`.

```
## 3. Watchlist Highlights（[YYYY-MM-DD] RTH）

| Symbol | RTH Close | RTH Change | 关键驱动 |
|--------|-----------|------------|----------|
| **[SYM]** | $[CLOSE] | **-[XX.XX]%** | [one-sentence reason from news] |
| **[SYM]** | $[CLOSE] | **+[XX.XX]%** | [one-sentence reason from news] |
| ... | ... | ... | ... |
```

- **RTH Close** = `kline[-1].close`; **RTH Change** = `(kline[-1].close / kline[-2].close - 1) * 100`   ← from `kline_{SYMBOL}.json`
- **Key driver column**: extract from the most relevant headline/summary in `news_{SYMBOL}.json`. 1 sentence max. Do not quote full articles.
- Default: show all focus group symbols. For large watchlists (30+), show the 15-20 most significant movers and note "（共 [N] 只标的，仅列显著变动）".
- For holidays with no new RTH data: show the last available RTH session, clearly dated in the section header.

---

## Section 4: Today's Catalysts

**Content — 4 bullet categories (conditional):**

```
## 4. Today's Catalysts

- 🔴 **今日休市**（[holiday name]）   ← if today is a holiday
- 📊 **[M/D]（[周X]）[HH:MM] CST**：[event name]（impact=[high/medium/low]）— [brief impact note]
- 📋 近期财报：[focus group symbols with upcoming earnings; otherwise "无主要标的财报"]
- ⚡ 宏观主题：[2-4 key narratives extracted from news files]
```

- **Economic events**: from `cal_econ.json` → `.economicCalendar[]`. Include time (converted to CST) and impact level.   ← from `cal_econ.json`
- **Earnings**: from `cal_earnings.json` → `.earningsCalendar[]`. List only focus group symbols; if none, pick 2-3 largest market-cap names or write "无主要标的财报".   ← from `cal_earnings.json`
- **Macro themes**: identify common narratives across multiple `news_*.json` files (e.g. "AI storage glut fears spreading", "payrolls miss eases rate concerns"). Do not list individual news items — synthesize.

---

## Section 5: Capital Flow Signals

**Content — Inflow/Outflow table (top 3-5 each direction):**

```
## 5. Capital Flow Signals

| 方向 | 标的 | 净流量 | MFI | 信号 |
|------|------|--------|-----|------|
| 🔴 流出 | **[SYM]** | **-[NET]** | [MFI] | [one-sentence explanation] |
| 🟢 流入 | **[SYM]** | **+[NET]** | [MFI] | [one-sentence explanation] |
```

- **方向**: 🔴 流出 for net_outflow, 🟢 流入 for net_inflow   ← from `cap_{SYMBOL}.json` → `.flow_direction`
- **净流量**: from `cap_{SYMBOL}.json` → `.summary.net_flow`. Units: ≥1B → suffix `B`, otherwise → `M`. Round to 2 decimal places.
- **MFI**: from `cap_{SYMBOL}.json` → `.summary.money_flow_index`
- **信号**: 1-sentence interpretation of the flow direction + magnitude + context
- Add one summary line after the table for overall MFI range (e.g. "MFI 整体区间 [MIN]-[MAX]，[assessment]")

### No Capital Flow Data

```
## 5. Capital Flow Signals

无资金流数据（`--capital-flow` 未启用或数据不可用）。
```

---

## Section 6: Trading Agenda

**Content — 2-4 numbered action items:**

```
## 6. Trading Agenda

1. **[theme/symbol]**：[observation and action plan. Include trigger condition, target level, and risk note.]
2. **[theme/symbol]**：[...]
3. **[theme/symbol]**：[...]
4. **[theme/symbol]**：[...]
```

- 2-4 items maximum. Each item: symbol/theme + specific observation + trigger condition or key level + brief rationale.
- Prioritize the day's biggest movers and the most immediate upcoming catalysts (next 1-3 trading days).
- Be specific about levels — use actual price/percentage thresholds, not vague "watch for weakness."

---

## Footer

```
*Data sourced from AlphaMeta / 数据来源：AlphaMeta*
```

---

## Conditional Section Map

| Condition | Handling |
|-----------|----------|
| Holiday / market closed | §2: replace with holiday notice · §4: mark "今日休市" |
| Pre-market data stale | §2: replace with `† 盘前数据未更新` notice |
| `cal_econ.json` empty | §4: "本周无重大经济事件" |
| `cal_earnings.json` has no focus symbols | §4: "无主要标的财报" |
| kline data missing latest RTH | All RTH figures marked `†`; apply Fallback rules from `morning-brief.md` §Data Freshness |
| No capital flow data | §5: replace with "无资金流数据" notice |
| Individual symbol quote stale | Skip that symbol from §2 pre-market table; do NOT mark `†` |

---

## Formatting Requirements

### 1. Number Format
- **Percentages**: 2 decimal places. Positive prefixed with `+`, negative with `-`. Example: `+4.84%`, `-14.13%`.
- **Prices**: thousands comma separator, 2 decimal places. Prefixed with `$`. Example: `$1,745.00`, `$308.63`.
- **Net flow**: ≥1B → suffix `B` (e.g. `-$12.14B`); <1B → suffix `M` (e.g. `+$557.18M`). Round to 2 decimal places.

### 2. Table Requirements
- Source line not required (all data from RAW_DIR; attribution is in the footer).
- Clear column headers. Bold the symbol name and change value in each row.

### 3. Source Annotations
- **Normal data**: no annotation. All numbers sourced from RAW_DIR by default.
- **Web search fallback**: `[source: web]` appended to the sentence. Example: "SPX closed at 7483.23 (-0.22%) [source: web]".
- **Stale data**: `†` prefixed to the sentence. Example: "† SNDK close unavailable for 2026-07-02; using prior session data."
- Annotations are used sparingly — only when the data path deviates from RAW_DIR.

### 4. Writing Style
- **Lead with numbers**: "SNDK fell 14.13% to $1,745" — never "SNDK dropped sharply."
- **Use "vs." not "versus"**.
- **Be concise**: one sentence per bullet. No descriptive padding.
- **Focus on what's NEW**: the overnight move, not the company background.
- **Chinese output**: the brief is delivered in Chinese. All section headers and content are in Chinese except for symbols, prices, and percentages (which use Western numerals).
- **Word limit**: <600 English words equivalent (Chinese: approx. 500-600 characters).

### 5. Delivery
- Output is written to the Obsidian vault path specified by the user (e.g. `~/Documents/Obsidian/.../YYYY-MM-DD 晨报.md`).
- In chat, alongside the file path: a compact summary — the Quality Checklist result and 2-3 key takeaways.
