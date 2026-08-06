# SEC Filings

SEC EDGAR filing analysis via AlphaMeta — listing, financial data extraction, and segment breakdown for US-listed companies.

> **Response language**: match the user's input language — Simplified Chinese / Traditional Chinese / English.

## When to Use

| Trigger | Example |
|---------|---------|
| List recent filings | `帮我列出 AAPL 最近的申报`, `TSLA 8-K`, `NVDA 10-K` |
| Financial data extraction | `AAPL 最新利润表`, `MSFT 去年各季度的收入`, `GOOGL 分业务部门` |
| Specific quarter | `AAPL Q1 2025 财务数据`, `MSFT 2024 年全年` |
| Multi-period trends | `NVDA 最近8个季度的收入和净利润`, `AAPL YoY 对比` |

## Data Sources

Priority: **AlphaMeta CLI (primary) → Web Search (supplement)**

Use the AlphaMeta execute API for all SEC data. Commands:

| Data Needed | Command |
|-------------|---------|
| List SEC filings | `filing <symbol> [type]` |
| Filing detail | `filing <symbol> detail <accession_number>` |
| Financial statements (XBRL) | `sec <symbol> [year] [quarter] [periods]` |

## CLI Reference

### `filing` — List SEC filings

Lists recent SEC EDGAR filings. Lightweight — no XBRL download.

```
filing <symbol> [type]
filing <symbol> detail <accession_number>
```

| Arg | Description | Example |
|-----|-------------|---------|
| `symbol` | Stock ticker | `AAPL`, `MSFT`, `TSLA`, `NVDA` |
| `type` | Filing type filter: `10-K`, `10-Q`, `8-K`, or `detail` | `10-K` |
| `accession_number` | Accession number (for detail mode) | `0000320193-25-000079` |

**Examples**:
```
filing AAPL              # List all recent SEC filings
filing AAPL 10-K         # List 10-K (annual reports)
filing AAPL 10-Q         # List 10-Q (quarterly reports)
filing AAPL 8-K          # List 8-K (current reports)
filing AAPL detail ACC   # Filing detail with full metadata
```

**Response fields**: `form`, `filing_date`, `period_of_report`, `accession_number`, `is_xbrl`, `is_inline_xbrl`, `size`, `primary_document`

### `sec` — Extract financial KPIs from XBRL

Fetches income statement data (revenue, operating income, net income, EPS) and segment breakdowns from SEC XBRL filings.

```
sec <symbol> [year] [quarter] [periods]
```

| Arg | Description | Example |
|-----|-------------|---------|
| `symbol` | Stock ticker | `MSFT`, `GOOGL`, `AAPL`, `TSM` |
| `year` | Year in YYYY | `2025` |
| `quarter` | Quarter | `q1`, `q2`, `q3`, `q4` |
| `periods` | Periods: `p1` (single with segments), `p4`, `p8`, `all` (multi-period trend) | `p8` |

**Modes**:
- **Single period** (`p1`, default): Uses XBRL API for detailed segment breakdown. Returns consolidated metrics + segment data. Supports revenue, operating income, net income, EPS.
- **Multi-period** (`p4`, `p8`, `all`): Uses Company Facts API for historical trend data. Returns trend data with YoY/QoQ comparisons. No segment breakdown.

**Examples**:
```
sec MSFT              # MSFT latest quarter with segments
sec MSFT p8           # MSFT last 8 quarters (trend)
sec MSFT 2025 q1     # MSFT Q1 2025
sec GOOGL             # Google latest quarter with segments
sec TSM               # TSM (foreign, 20-F filings)
```

**Response fields**: `symbol`, `periods`, `consolidated` (with metrics + YoY/QoQ), `segments` (for single period)

## Filing Type Guide

| Filing | Frequency | Key Content | Investment Signal |
|--------|-----------|-------------|-------------------|
| 10-K | Annual | Full financials, Risk Factors, MD&A, auditor opinion | Baseline quality, hidden risks |
| 10-Q | Quarterly | Interim financials, MD&A updates, legal proceedings | Trend vs prior quarters |
| 8-K | Ad hoc | Material events: earnings, M&A, exec changes, defaults | Immediate catalyst |
| 20-F | Annual | Foreign issuer annual report (e.g., TSM, ASML) | Cross-border baseline |

## Workflow

1. **Identify what user needs**: filing list or financial data extraction.
2. **If filing list**: run `filing <symbol> [type]` or `filing <symbol> detail <acc>`.
3. **If financial data**: run `sec <symbol> [year] [quarter] [periods]`:
   - Use `p1` when user wants the latest quarter with segment breakdown
   - Use `p4`/`p8`/`all` when user wants historical trends or YoY/QoQ comparisons
4. **Supplement with Web Search** for: consensus estimates, earnings call transcripts, management guidance context (not in SEC data).

Output the results in the user's language. For financial data, present a structured table with periods as columns, metrics as rows, including YoY/QoQ changes and segment breakdown where available.

## Output — Filing List Mode

```
{Symbol} SEC Filings — Source: SEC EDGAR

Form   | Filing Date   | Period End    | Accession Number
10-K   | 2025-10-31    | 2025-09-27    | 0000320193-25-000079
10-Q   | 2025-08-01    | 2025-06-28    | 0000320193-25-000073
8-K    | 2025-07-31    | 2025-07-31    | 0001140361-25-030955
...
[N results, showing last {N} filings]
```

## Output — Filing Detail Mode

```
{Symbol} Filing Detail — Source: SEC EDGAR

Form:           10-K
Company:        Apple Inc.
CIK:            320193
Filing Date:    2025-10-31
Period End:     2025-09-27
Accession:      0000320193-25-000079
XBRL:           Yes
Exhibits:       10-K, EX-4.1, EX-21.1, EX-23, EX-31.1, EX-32.1, EX-97
URL:            https://www.sec.gov/...-index.html
```

## Output — Financial Data Mode

```
{Symbol} Financial Summary — Source: SEC EDGAR
Period: {periods}

Metric               {period1}    {period2}    {period3}    YoY
Revenue              $XX.XB       $XX.XB       $XX.XB       +X.X%
Operating Income     $XX.XB       $XX.XB       $XX.XB       +X.X%
Net Income           $XX.XB       $XX.XB       $XX.XB       +X.X%
EPS                  $X.XX        $X.XX        $X.XX        +X.X%
Operating Margin     XX.X%        XX.X%        XX.X%        ±X.Xpp

Segment Revenue:
{segment1}           $X.XB        $X.XB        $X.XB        +X.X%
{segment2}           $X.XB        $X.XB        $X.XB        +X.X%
...

⚠️ 数据来源 SEC EDGAR，仅供参考，不构成投资建议。
```

## Error Handling

| Situation | Response |
|-----------|----------|
| `filing` returns empty | No SEC filings found for this symbol. For non-US stocks, SEC filings are not applicable. |
| `sec` returns error | Symbol may not have XBRL data, or may be a non-US issuer without 20-F. Try a different symbol or check if the company files with SEC. |
| Symbol not found | Verify the ticker symbol is correct (e.g., AAPL, MSFT, NVDA). For foreign issuers, use the US-listed ADR ticker (e.g., TSM, ASML). |
