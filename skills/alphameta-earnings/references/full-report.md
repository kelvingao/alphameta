# Full Report Workflow (Markdown Research Report)

> **Response language**: match the user's input language — Simplified Chinese / English.
> **RULE: Response language priority**: English is the default when language is ambiguous.

Read this only when the user explicitly asks for a full report (完整报告 / 深度分析 / 研报 / "full report" / "research report"), or upgrades after a Lite summary card.

**Deliverable**: `[SYMBOL]_Q[N]_[YEAR]_Earnings_Update.md` — 12-15 sections, Markdown tables, Unicode `█` bars for trends. **No DOCX by default** (the existing `scripts/generate_report.py` is an optional upgrade path for users who want an institutional DOCX with matplotlib charts).

---

## Phase 1 — Data Collection

1. **Reuse Lite digest if present.** If a Lite run already printed a `RAW_DIR`, use it. Otherwise:
   ```bash
   python3 scripts/collect.py <SYMBOL> --full
   ```
   `--full` adds balance sheet + cash flow. Raw JSON lives in the printed `RAW_DIR` — read those files directly instead of re-calling the CLI.

2. **Identify the reporting period** from the latest `earnings` data (quarterly actual EPS with period end dates) or the most recent filing date. Map period-end to fiscal quarter using the company's fiscal calendar (most are calendar year; Apple FY ends Sep, Nike May, Walmart Jan). State the detected quarter in the header — do not pause to ask unless the data is contradictory.

3. **One web search for the earnings call transcript**: `[Company] Q[X] [Year] earnings call transcript`. Verify the transcript date matches the reporting period. Extract: management tone, guidance, key Q&A themes, notable quotes with speaker attribution.

4. **Pre-earnings consensus baseline**: the digest CONSENSUS section has estimate-vs-actual with `beat_est`/`miss_est` flags. Only web-search for consensus history if the user disputes the baseline.

5. **Filing detail for deeper MD&A**: the `filings detail` command provides management discussion and supplementary segment context the structured statements may lack.

**Verify before analysis**: all materials refer to the same quarter; release within ~3 months; reported figures come from CLI data, not memory.

---

## Phase 2 — Analysis (in order; each becomes a report section)

1. **Beat/miss** — for each KPI (revenue, EBIT, net income, EPS): quantify the variance ($ and %), explain WHY (driver, one-time vs sustainable), connect to thesis. CONSENSUS digest has estimate/actual for multiple periods.

2. **Segments** — from `Segment / Revenue Breakdown` digest: what out/under-performed, mix shift, trend vs prior quarters.

3. **Margins** — gross/operating/net trajectory from INCOME_STATEMENT digest (8 quarters). Drivers: pricing, mix, costs, operating leverage.

4. **Guidance** — new vs prior vs Street; credibility (track record); key assumptions. If none provided, say so explicitly and give your own outlook.

5. **Estimate revisions** — update current FY + next FY: revenue, EBITDA/EBIT, EPS. Show old -> new -> % change -> reason per line.

6. **Valuation** — read [valuation-methodologies.md](valuation-methodologies.md). Three methods, dynamic weighting, full math shown:
   - **DCF (40-60%)** — WACC from CAPM (10Y Treasury, beta, ERP), FCF projections, terminal value (perpetuity growth 2-3%). Bear/Base/Bull scenarios.
   - **Trading Comps (25-40%)** — P/E + EV/EBITDA; 25th pct (Bear) / median (Base) / 75th pct (Bull).
   - **Precedent Transactions (0-25%)** — only when relevant M&A exists; otherwise redistribute to DCF + Comps.
   - State chosen weights and justify. Sanity checks: DCF within +/-30% of market price, methods directionally agree, terminal value 50-70% of EV.

7. **Rating decision** — upgrade/downgrade/maintain with rationale. If estimates moved >5%, the target usually moves too; if unchanged, explicitly maintain.

---

## Phase 3 — Report Structure (Markdown)

```markdown
# [Company] ([Ticker]) — Q[X] FY[Year] Earnings Update
> [Event-driven headline, e.g. "DTC Strength Offsets Wholesale Weakness"]

Rating: **[BUY/HOLD/SELL]** | PT: **$XXX** | Price: $XXX | Upside: +XX%

## 1. Earnings Summary            ← verdict (BEAT/INLINE/MISS) + KPI scorecard + 3-4 bullets
## 2. Revenue Analysis            ← beat/miss + quarterly progression table (8Q)
## 3. Segment Breakdown           ← segment table with █ share bars + YoY
## 4. Profitability               ← margin trend table + drivers (+/- list)
## 5. Key Operating Metrics       ← company-specific KPIs vs expectations
## 6. Guidance & Outlook          ← new vs old vs Street + credibility
## 7. Earnings Call Highlights    ← tone, themes, 2-3 quotes with speaker
## 8. Updated Estimates           ← old -> new -> change -> reason (current FY + next FY)
## 9. Valuation                   ← three methods + weights + math
## 10. Bear / Base / Bull         ← range table + sensitivity
## 11. Investment Thesis Update   ← per pillar: STRENGTHENED/UNCHANGED/WEAKENED
## 12. Risks                      ← new/changed risks
## 13. Appendix (optional)        ← quarterly model detail, peer table
## Sources & References           ← all materials as Markdown links with dates
```

**Trend "charts" with Unicode bars**:

```markdown
| Quarter | Revenue (B) | YoY | Trend |
|---------|------------:|----:|-------|
| Q2'25A  | 185.9       | +17% | ███████████████▌ |
| Q3'25A  | 194.1       | +14% | ████████████████▏ |
```

**Style rules**: lead with numbers ("Revenue grew 15% to $1.2B", never "strong growth"). Year notation: `A` actual, `E` estimate. "vs." not "versus". Focus on what's new — no company-101 padding. Every table gets a `Source:` line. All citations are Markdown links with meaningful display text — never raw URLs. Sources section at the **end of the file only** — never in chat.

---

## Phase 4 — Delivery

In chat, alongside the file path: a compact recap — verdict, 3 takeaways, estimate changes, rating + PT. Reuse the Lite summary-card format if the user has not already seen one this conversation.

**DOCX optional upgrade**: the existing `scripts/generate_report.py` can produce a professional DOCX with embedded matplotlib charts (matplotlib + python-docx, bilingual CJK/Latin fonts). If the user wants an institutional report file instead of Markdown, run that script instead. The default full report is Markdown.

---

## Quality Checklist (final pass)

1. Beat/miss leads the report; every variance quantified ($ and %) with WHY.
2. All data from the latest quarter; consensus baseline is pre-earnings.
3. Old vs new estimates shown for current FY + next FY, with reasons.
4. Valuation: weights stated and justified; sanity checks pass or divergence explained.
5. PT and rating explicit — changed with rationale, or explicitly maintained.
6. Guidance analyzed (or its absence noted).
7. Thesis pillars each tagged STRENGTHENED / UNCHANGED / WEAKENED with evidence.
8. Every table has a Source line; all links are Markdown links that resolve.
9. Numbers match the company's reported figures exactly; math checks out.
10. Headline is event-driven; ticker and quarter correct throughout.

---

## Quick Reference: Digest Sections from collect.py

| Section (in output order) | Contains | Used For |
|---|---|---|
| Filings | Latest 5 SEC filings with dates | Quarter identification, filing links |
| Income Statement | 8Q revenue, gross profit, OI, NI | Margin analysis, trend tables |
| Consensus | Analyst ratings, price target, EPS estimates, beat/miss history | Beat/miss analysis, rating context |
| Earnings Calendar & Beat Rate | Next earnings date, forward EPS/revenue estimates, quarterly EPS actual vs estimate, beat rate | Forward estimates, beat rate assessment |
| Valuation Percentile | 5yr PE/PB percentile, current/forward PE | Valuation comps |
| Operating KPIs | 8Q revenue, net income, gross profit | Multi-period trend analysis |
| Daily OHLCV | Last 20 closes + 250d high/low | Price action context |
| Current Quote | Live bid/ask/last, volume, IV/HV | Current price, upside calc |
| News | Latest 10 headlines with summaries | Context, call themes |
| Segment / Revenue Breakdown | Multi-period segment data | Segment analysis |
| *(Full mode only)* Balance Sheet | 8Q BS KPIs | DCF net debt calc |
| *(Full mode only)* Cash Flow | 8Q CF KPIs | FCF calculation |
