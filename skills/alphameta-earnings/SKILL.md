---
name: alphameta-earnings
description: 'Post-earnings analysis skill for institutional-grade earnings updates. Covers beat/miss, segment breakdown, margin trends, guidance assessment, estimate revisions, and valuation. Dual-mode: Lite (in-chat summary card, default) + Full (Markdown report, optional DOCX). Supports US markets. Triggers: "earnings update", "quarterly results", "Q1/Q2/Q3/Q4 results", "earnings report", "post-earnings analysis", "beat/miss", "guidance update", "财报分析", "业绩更新", "季度业绩", "季报", "年报", "盈利分析", "财报点评", "财报前瞻", "业绩前瞻", "财报预览".'
---

# AlphaMeta Earnings

> **Response language**: match the user's input language — Simplified Chinese / English.
> **RULE: Response language priority**: English is the default when language is ambiguous. If the user input is only a slash command, command name, ticker / symbol, or contains no natural-language language signal, you MUST respond in English. Do not infer Chinese from trigger keywords, skill metadata, or examples.

## Routing: Pre-earnings vs Post-earnings

Determine whether the company has reported the latest quarter:

| Signal | Action |
|--------|--------|
| Earnings not yet released (upcoming) | Route to [`references/pre-earnings.md`](references/pre-earnings.md). Follow the pre-earnings preview workflow. |
| Already reported | Proceed with **post-earnings** analysis below. Default to **Lite Mode**. |

To check: use `python3 scripts/collect.py <SYMBOL>` and inspect the digest for period-end date and report status.

---

## Post-Earnings: Dual-Mode Architecture

### Lite Mode (default, ~2-3 min)

The default path. Produces an in-chat summary card with 8 modules.

**Step 1 — Collect data**
Run the parallel data collector (pure Python stdlib, no pip needed):

```bash
python3 scripts/collect.py <SYMBOL>
```

This fetches 10 data sources concurrently and prints a compact digest (~3-4K tokens). The script:
- Normalizes symbol format automatically
- Exits with an error if the AlphaMeta server is unreachable
- Saves raw JSON responses to a temp directory (printed in digest)

**Step 2 — Output summary card directly** (no DOCX, no file, no DCF). Card modules — skip any whose data is N/A:

1. **Header** — `[Company] ([Ticker]) — Q[X] [Year] Earnings` + consensus rating, avg target, current price, upside
2. **Core KPI table** — 4-5 metrics (Revenue, NI, Gross Margin, EPS): Reported / YoY / vs Estimate (Beat +X% or Miss -X%)
3. **Revenue by segment** — table with Unicode `█` share bars + YoY (from Segment digest)
4. **Quarterly trend** — last 6-8 quarters of revenue + net margin (from Income Statement digest)
5. **Thesis status** — 2-4 bullets, each tagged 🟢 Strengthened / 🟡 Maintained / 🟠 Weakened, grounded in the quarter's numbers
6. **Street view** — rating distribution + target price range (from Consensus digest, do not compute your own)
7. **Next-quarter consensus** — what the Street expects next quarter (from Earnings digest)
8. **Risks** — one line of inline-backtick tags: `` `Risk1` · `Risk2` · `Risk3` ``

Refer to `earnings` quarterly data for beat/miss flags and `consensus` analyst_ratings for ratings. Use the user's language for card content; keep numbers/formats consistent with Markdown tables.

**Step 3 — Close with upgrade hint**

```
💡 如需完整研报（含 DCF 估值、目标价推导、逐段分析），回复"生成完整报告"。
```

If the user's language is English, localize the hint accordingly: "Reply 'generate full report' for a complete report with DCF valuation, price target derivation, and segment-level analysis."

---

### Full Report Mode (on explicit request)

Triggered when the user asks for a full report, detailed analysis, or "完整报告".

**Step 1 — Collect full data**
If a RAW_DIR was printed in the Lite run (same session), reuse it. Otherwise run:

```bash
python3 scripts/collect.py <SYMBOL> --full
```

This adds balance sheet and cash flow statements (12 data sources total).

**Step 2 — Fetch earnings call transcript**
Run one web search for the earnings call transcript to supplement with management commentary.

**Step 3 — Analyze**
Read [`references/full-report.md`](references/full-report.md) and follow the analysis framework:
- Beat/miss analysis (revenue, EPS, operating income vs consensus)
- Segment breakdown (revenue and margin by segment)
- Margin analysis (gross, operating, net — YoY and QoQ)
- Guidance assessment (next-quarter and full-year)
- Estimate revision model (forward 1-2 year EPS updates)

**Step 4 — Valuation**
Read [`references/valuation-methodologies.md`](references/valuation-methodologies.md) and apply the three-method approach:
- DCF valuation
- Trading comparables
- Precedent transactions

**Step 5 — Deliverable**
By default, write a Markdown file: `[SYMBOL]_Q[N]_[YEAR]_Earnings_Update.md`

For institutional use, optionally generate a DOCX report with embedded matplotlib charts (requires `python-docx`, `matplotlib`, `numpy` — the LLM will install on demand).

**DOCX workflow**: Read data from the RAW_DIR JSON files, write an inline Python script using `DocxBuilder` and `ChartBuilder` from `scripts/generate_report.py`. Pipe JSON data into charts and tables, then call `python3` to generate the DOCX.

See [`references/pre-earnings.md`](references/pre-earnings.md) §§Output: DOCX Upgrade Path for the complete code pattern (preview), and [`references/report-structure.md`](references/report-structure.md) for the page-by-page DOCX template (full report).

The DOCX path is an upgrade, not the default. Always deliver the Markdown report as the primary full-mode output first.

---

## Data Sources

**Primary path**: `python3 scripts/collect.py <SYMBOL>`
- Pure Python stdlib — no pip dependencies
- Fetches all data in one parallel call (10 sources lite, 12 full)
- Prints a structured digest with all key metrics

**Fallback (no Python / collect.py fails)**: Issue individual CLI calls in parallel. Use runtime discovery to find available commands:

```
GET /api/v1/search?query=<data needed>
```

This returns matching CLI commands dynamically — do not assume hardcoded command names.

**Server setup**: See the [alphameta](../alphameta) skill for `alphameta --ibkr` startup and command execution syntax via `POST /api/v1/execute`.

---

## Error Handling

| Situation | LLM Response |
|-----------|--------------|
| Server not reachable (health check fails) | Ask the user to start the AlphaMeta server with `alphameta --ibkr`. |
| collect.py fails / Python unavailable | Fall back to individual CLI calls in parallel. Use runtime discovery: `GET /api/v1/search?query=<data needed>`. |
| Partial N/A data sections | Work with available data. Flag gaps in the summary card (e.g. "Segment data unavailable — skipping segment breakdown"). |
| All data sources N/A | Use web search with clear source labeling. Label every data point as "[source: web search]". |

---

## Related Skills

For lighter or differently-framed asks, defer to a sibling:

| User asks for...                                                | Use                                                           |
| --------------------------------------------------------------- | ------------------------------------------------------------- |
| Live quote / valuation indices / PE-PB percentiles              | [`alphameta-market-data`](../alphameta-market-data)           |
| Financial statements / fundamentals / consensus                 | [`alphameta-fundamental`](../alphameta-fundamental)           |
| Price chart / k-line / technicals                               | [`alphameta-market-data`](../alphameta-market-data)           |
| Market intelligence: screener, calendar, top movers, briefings  | [`alphameta-intelligence`](../alphameta-intelligence)         |
| Accounting / portfolio / risk analysis                          | [`alphameta-portfolio`](../alphameta-portfolio)               |
| Server setup or CLI discovery                                   | [`alphameta`](../alphameta)                                   |

If the user wants the full earnings report *plus* one of the above (e.g. "earnings update on TSLA and how it compares to MSFT"), do this skill first, then chain to the other.

---

## Reference Files

| File | Contents | When to Read |
|------|----------|--------------|
| [pre-earnings.md](references/pre-earnings.md) | Pre-earnings preview: 6 analysis modules + three-tier output (inline / Markdown / DOCX) | Pre-earnings (upcoming release) |
| [full-report.md](references/full-report.md) | Full-report workflow: analysis framework, Markdown report structure, quality checklist | Full report mode only |
| [report-structure.md](references/report-structure.md) | Page-by-page DOCX template (12 pages) with tables, charts, formatting | DOCX upgrade path only |
| [valuation-methodologies.md](references/valuation-methodologies.md) | DCF, trading comps, precedent transactions — full methodology | Full report valuation step |
| [scripts/collect.py](scripts/collect.py) | Parallel data collector (lite + --full), pure stdlib | Never — just run it |
| [scripts/generate_report.py](scripts/generate_report.py) | DocxBuilder + ChartBuilder — DOCX generation library (optional, needs pip) | DOCX upgrade path only |

---

## File Layout

```
alphameta-earnings/
├── SKILL.md
├── commands/
│   └── earnings.md             # /earnings <SYMBOL> slash command
├── references/
│   ├── pre-earnings.md         # Pre-earnings preview workflow
│   ├── full-report.md          # Full report analysis framework
│   ├── report-structure.md     # DOCX 12-page template (upgrade path)
│   └── valuation-methodologies.md  # DCF + comps + precedent
├── scripts/
│   ├── collect.py              # Parallel data collector (pure stdlib)
│   └── generate_report.py      # DOCX generator (python-docx + matplotlib + numpy)
```
