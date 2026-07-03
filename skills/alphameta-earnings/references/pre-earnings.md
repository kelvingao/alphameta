# Pre-Earnings Preview

The **pre-earnings** mode of `alphameta-earnings`: help an investor prepare for an
**upcoming** earnings release by surfacing prior guidance, recent events, the last call's
Q&A, and the key things to watch. Read this file only when the company has **not yet
reported** the latest quarter and the user needs a forward-looking preview.

> **Output (three-tier)**: inline summary by default. Upgrade on explicit request:
> - **Level 1** (default): Inline summary in chat — see "Output: Inline Preview Summary".
> - **Level 2** ("完整前瞻 / full preview"): Single Markdown file — see "Output: Optional Markdown File".
> - **Level 3** ("生成报告 / generate docx"): DOCX with embedded charts — see "Output: DOCX Upgrade Path".

> **Response language**: match the user's input language — Simplified Chinese / English.
> **RULE: Response language priority**: English is the default when language is ambiguous.
> If the user input is only a slash command, command name, ticker / symbol, or contains
> no natural-language language signal, you MUST respond in English. Do not infer Chinese
> from trigger keywords, skill metadata, or examples.

## Data Sources

Priority: **collect.py (primary) -> Web Search (supplement)**.

### Primary: collect.py (parallel data collector)

The main data source is the `collect.py` script located at
`scripts/collect.py` within the alphameta-earnings skill directory. It fetches
all relevant data in one parallel round:

```bash
python3 scripts/collect.py <SYMBOL>
python3 scripts/collect.py <SYMBOL> --full   # adds balance sheet & cash flow
```

The collect.py digest provides these sections in compact JSON (3-4K tokens):

| Digest Section     | AlphaMeta Command                 | Used For                          |
|--------------------|-----------------------------------|-----------------------------------|
| Filings            | `filing <symbol>`                 | Prior guidance, management outlook |
| Income Statement   | `financial-report <symbol> IS p8` | Revenue/EPS trends, margin history |
| Consensus          | `consensus <symbol>`              | Beat/miss history, EPS estimates   |
| Valuation Percentile | `calc-index <symbol>`           | PE/PB percentile context           |
| Operating KPIs     | `operating <symbol> p8`           | Multi-quarter metric trends        |
| Kline / Price      | `kline <symbol> day 250`          | Price context, support/resistance  |
| Quote              | `quote <symbol>`                  | Current market price               |
| News               | `news <symbol>`                   | Recent events                      |
| Segment Data       | `sec <symbol>`                    | Revenue breakdown by segment       |

Run `python3 scripts/collect.py --help` for full options.

See the [alphameta](../alphameta) skill for server setup and command execution syntax.
The collect.py script is a convenience wrapper around the AlphaMeta execution API
(`POST http://localhost:18080/api/v1/execute` with `{"cmd": "..."}`). If collect.py
is unavailable, individual commands can be run directly via `curl` or the alphameta CLI.
Use `GET http://localhost:18080/api/v1/search?query=xxx` for command discovery.

### Supplement: Web Search

| Data Needed                    | Search Query Pattern                           |
|--------------------------------|-------------------------------------------------|
| Earnings call transcript       | `"[Company] Q[X] [Year] earnings call transcript"` |
| Options-implied move           | `"[Symbol] earnings implied move"`              |
| Whisper numbers / whisper EPS  | `"[Symbol] whisper number this quarter"`        |
| Industry events not indexed    | `"[Industry] [Month] key developments"`         |
| Peer earnings calendar          | `"[Peer Symbol] earnings date Q[X]"`            |
| Analyst preview notes           | `"[Symbol] earnings preview analyst"`           |

## Analysis Modules

### Module A: Prior Quarter Guidance vs. Actual

Extract from the most recent filing and the call before it.

- **Guidance fulfillment**: the key metric is always **management's own prior guidance vs.
  the actual result** — not YoY, not consensus vs. actual. What did management guide for
  Q[N-1] at the end of Q[N-2], and how did the Q[N-1] actual compare?
- **Management outlook**: macro/sector views, strategic priorities, capital allocation
  stated in the prior report.
- **Performance summary**: for each guided metric, the beat/miss amount and direction.

Use `consensus <symbol>` from collect.py for beat/miss data. Cross-reference with
`filings <symbol>` for prior guidance details (look for management's own quantitative
outlook in the MD&A or earnings release text within the filing).

Key comparison:

| Metric | Mgmt Prior Guidance | Actual | Deviation | Assessment |
|--------|---------------------|--------|-----------|------------|
| Revenue | $X,XXX - $X,XXX    | $X,XXX | +X%       | Beat / Inline / Miss |
| EPS     | $X.XX - $X.XX      | $X.XX  | +X%       | Beat / Inline / Miss |

- Col 2 = management's own guidance range/midpoint, NOT market consensus
- Col 3 = actual reported value from the filing
- Col 4 = (actual - guidance midpoint) / guidance midpoint, with sign
- Col 5 = 超预期 / 基本符合 / 不及预期 (or English equivalent)

If management gave no quantitative guidance (e.g. pre-revenue stage companies), use
operational milestone commitment vs. actual progress instead. Use `filings <symbol>` to
locate prior filings; for transcripts not in the CLI, web-search
`"[Company] Q[X] earnings call transcript"`.

### Module B: Recent Events Tracking

Surface events since the prior release relevant to this quarter, categorized by:

- **Macro/policy**: rate decisions, regulatory changes, trade policy, tax changes
- **Industry**: competitor moves, supply chain developments, technology shifts
- **Company**: product launches, management changes, partnerships, legal/regulatory actions
- **Market sentiment**: analyst upgrades/downgrades, short interest changes, fund flows

Use `news <symbol>` from the collect.py digest. Supplement with web search for events
not indexed. Each event entry should include: date, source, description, and relevance
to the upcoming earnings.

### Module C: Prior Earnings Call Q&A Summary

From the prior call transcript, extract:

- **High-frequency analyst questions**: topics that came up repeatedly (margins, segment
  growth, capex, competition, capital returns, guidance methodology)
- **Management's response**: key judgments and commitments made, not verbatim quotes
- **Verification significance**: which Q&A topics this quarter's results will answer

Source: web search for the transcript. Not available via collect.py.

Format:

```
Q: [Topic / question paraphrased]
  -> Mgmt: [Key judgment or commitment]
  -> Watch for: [What this quarter's numbers will reveal]
```

### Module D: Key Focus Framework for This Quarter

Synthesize Modules A-C into an actionable preview:

- **Guidance fulfillment checklist**: each prior quantitative guidance item mapped to the
  specific data point to check in the upcoming release.
- **Beat / miss risk factors**: what could surprise in either direction — demand trends,
  pricing power, cost pressures, FX headwinds, one-time items.
- **3-5 key questions to watch**: plain-language questions combining institutional focus
  with the user's holding thesis.
- **Risk flags**: tail risks from prior management warnings plus recent external events.

Use `operating <symbol> p8` from the collect.py digest for historical metric trends.

### Module E: Historical Guidance Fulfillment Tracking

Pull 4-8 quarters to establish management's track record:

- **Guidance-vs-actual table**: by quarter, showing each guided metric vs. actual
- **Bias pattern**: consistently conservative (sandbagging), consistently optimistic
  (guided high), or alternating
- **Metric reliability**: tight vs. wide historical deviation by metric type
- **Credibility assessment**: for the current guidance — how much confidence should an
  investor place in it?

Use `consensus <symbol>` from collect.py: the `beat_miss_history` field contains
8 quarters of prior data.

```
Quarter   Revenue Guide  Revenue Actual  Deviation   EPS Guide   EPS Actual  Deviation
Q1 FY26   $X,XXX-$X,XXX  $X,XXX         +X%         $X.XX-$X.XX $X.XX       +X%
...
```

Credibility labels: 高 (high) / 中 (medium) / 低 (low).

### Module F: Market Consensus vs. Management Guidance

Identify expectation gaps:

- **Current consensus**: EPS and revenue estimates for the upcoming quarter
- **Comparison with management guidance**: above / below / within range
- **Consensus range**: high-low spread as a measure of analyst disagreement
- **Historical consensus accuracy**: how close is the Street usually?
- **Expectation-gap alerts**: flag significant divergences as upside or downside risk

Use `consensus <symbol>` from collect.py: the `eps_estimates` field provides current
estimates. Compare with management's explicit guidance (from Module A).

```
  Metric      Consensus    Mgmt Guide    Gap       Signal
  Revenue     $X,XXX       $X,XXX        +X%       Upside / Inline / Downside
  EPS         $X.XX        $X.XX         +X%       Upside / Inline / Downside
```

Expectation-gap alerts: flag when consensus is materially above or below the implied
guidance midpoint (>3% for revenue, >5% for EPS).

## Output: Inline Preview Summary

Use exactly this structure. Skip any section with no data with a one-line note
(e.g. "No call transcript available — skip"). Do not rename, reorder, or add sections.

```
[Company (Symbol)] Earnings Preview
Report date: {date} | Analysis: {today}

[One] Prior Guidance Review
- [Metric]: Mgmt guided {range} -> Actual {value} ({beat/miss +X%})
  Note: management's OWN guidance vs. actual, not consensus vs. actual
- ...

[Two] Management Outlook Highlights
- ...

[Three] Prior Call | Analyst Q&A
Q: {question}
  -> Mgmt: {response}
  -> Watch for: {what to check}
- ...

[Four] Recent Events
- {date} {source}: {event} -> Relevance: {impact on earnings}
- ...

[Five] Historical Guidance Track Record
- Revenue: Last N quarters avg deviation {direction} {magnitude}
- EPS: Fulfillment rate {X%}, average deviation {value}
- Credibility: {assessment}

[Six] Consensus vs Mgmt Guidance
  Metric      Consensus    Mgmt Guide    Gap
  Revenue     ...          ...           ...
  EPS         ...          ...           ...
- Expectation gap alert: {message}

[Seven] Key Things to Watch This Quarter
1. {question}
2. {question}
3. {question}

[Eight] Risk Flags
- {risk}
- {risk}

---
Data: AlphaMeta CLI + Web Search | For reference only, not investment advice
```

If the output language is Chinese, use the Chinese section headers:

```
【一】上期业绩指引回顾
【二】管理层展望要点
【三】上期电话会 | 分析师核心 Q&A
【四】近期重要事件
【五】历史指引兑现规律
【六】市场一致预期 vs 管理层指引
【七】本次财报核心关注点
【八】风险提示
```

## Output: Optional Markdown File

Only when the user explicitly asks for a written preview: produce a single file
`[SYMBOL]_Q[N]_[YEAR]_Earnings_Preview.md` covering the same eight sections, using
Markdown tables and Unicode bar characters (`|█`) for any data visualization.
**No DOCX, no Python scripts, no image files.**

## Output: DOCX Upgrade Path

Only when the user explicitly asks for a generated file ("生成报告 / generate docx"): produce a
professional DOCX with embedded matplotlib charts (requires `python-docx`, `matplotlib`, `numpy` — the LLM will install on demand).

Uses the same eight sections as the inline summary (see above). Read data from the `collect.py`
RAW_DIR JSON files directly, build charts with ChartBuilder, then assemble with DocxBuilder.

**Chart mapping:**

| Section | Chart | Function | Data Source |
|---------|-------|----------|-------------|
| 【一】Prior Guidance Review | Revenue/EPS quarterly bars (estimate bar highlighted) | `cb.quarterly_bar(title, quarters, values, estimate_idx=-1, ylabel="$B")` | `income_stmt.json` → IS.metrics.Revenue |
| 【五】Historical Track Record | Guidance beat rate trend over 8 quarters | `cb.growth_lines(title, quarters, series, ylabel="Beat Rate %")` | `consensus.json` → beat_miss_history |
| 【六】Consensus vs Mgmt | Analyst price target range | `cb.analyst_pt_hbar(title, current, current_label, target_mean, target_high, target_low, num_analysts)` | `consensus.json` → price_target |
| 【七】Key Watch Items | 60-day price action with reference lines | `cb.price_action(title, dates, prices, current, current_label)` | `kline.json` → last_20 |
| 【六】or standalone | Scenario comparison (bear/base/bull) | `cb.scenario_hbar(title, ["Bear","Base","Bull"], values, current, current_label)` | quote.json + calculated |
| Any section | Segment revenue breakdown (optional) | `cb.grouped_bar(title, categories, series, ylabel="$B")` | `segment.json` → segments |

**Formatting requirements** (fonts, hyperlinks, year notation, writing style):
→ Follow [`report-structure.md`](report-structure.md) §§Formatting Requirements.

**Code pattern:**

```python
import sys, json; sys.path.insert(0, "scripts")
from generate_report import DocxBuilder, ChartBuilder

RAW = "<RAW_DIR from collect.py output>"
income = json.load(open(f"{RAW}/income_stmt.json"))
consensus = json.load(open(f"{RAW}/consensus.json"))
kline = json.load(open(f"{RAW}/kline.json"))
quote = json.load(open(f"{RAW}/quote.json"))
px = quote["quotes"][0]["last"] or quote["quotes"][0]["close"]

cb = ChartBuilder()
b = DocxBuilder(symbol="SYMBOL", company="...",
    report_date="...", analysis_date="...",
    price=f"${px:.2f}", market_cap="~$XB",
    valuation="P/E XXx", rating="...",
    subtitle="Earnings Preview",
    output_path="SYMBOL_QN_FY202X_Earnings_Preview.docx")

b.cover()
b.toc([("【一】","Prior Guidance Review"),("【二】","Management Outlook"),
       ("【三】","Earnings Call Q&A"),("【四】","Recent Events"),
       ("【五】","Historical Track Record"),("【六】","Consensus vs Mgmt Guidance"),
       ("【七】","Key Watch Items"),("【八】","Risk Factors")])
b.section("【一】Prior Guidance Review")
b.body("Management guided revenue $X.XB-X.XB, actual $X.XB (+X%)...")
b.table(["Metric","Guide","Actual","Δ"],[["Rev","$X","$X","+X%"],["EPS","$X","$X","+X%"]])
b.image(cb.quarterly_bar("Revenue Trend", quarters, values, ylabel="$B"))
# ... build remaining sections with text, tables, charts ...
b.section("【八】Risk Factors")
b.bullet("Risk 1...")
b.disclaimer()
b.save()
```

File name: `[SYMBOL]_Q[N]_[YEAR]_Earnings_Preview.docx`

## Error Handling

| Situation                                  | Response                                                                                 |
|--------------------------------------------|------------------------------------------------------------------------------------------|
| Shell `command not found: alphameta`       | Fall back to direct `curl` calls to the AlphaMeta API if the server is reachable. Otherwise tell the user to install alphameta (`pip install alphameta`) and start the server (`alphameta --ibkr`). Deliver a web-search-only preview with a clear label. |
| collect.py not found                       | Run individual commands via `curl -X POST http://localhost:18080/api/v1/execute -H "Content-Type: application/json" -d '{"cmd": "..."}'`. Use `GET http://localhost:18080/api/v1/search?query=xxx` to discover available commands. |
| `income_stmt.json` / `balance_sheet.json` / `cash_flow.json` empty | Non-US company (foreign issuer, 20-F filer). `financial-report` only covers US SEC filers. Use `operating` + `earnings` data from the digest as primary sources. For deeper financial details, run `financial {symbol} statements` via CLI as a supplemental data source. |
| Company has **already reported**            | Switch to the post-earnings path of the alphameta-earnings skill (conversation summary card or full DOCX report). |
| No CLI data + no web results               | State which modules have gaps; still deliver the available modules. Never produce a blank preview. |
| No transcript found for prior call         | Skip Module C with a one-line note. Deliver the other 7 modules.                        |
| Company does not provide quantitative guidance | Use operational milestones vs. actual progress (Module A). Flag in the credibility assessment (Module E). |
| Other error or unexpected output           | Surface verbatim — never silently retry.                                                 |
