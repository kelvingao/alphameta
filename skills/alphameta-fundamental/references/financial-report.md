# Financial Report — Three-Statement Analysis

Full three-statement financials (IS / BS / CF) with complete line-item hierarchy, cross-statement reconciliation, DuPont decomposition, and earnings-quality analysis. Data sourced from SEC EDGAR XBRL filings via AlphaMeta (IBKR).

> **Response language**: match the user's input language — Simplified Chinese / Traditional Chinese / English.

## When to Use

| Trigger | Example |
|---------|---------|
| Three statements | *"AAPL 三张表"*, *"TSLA three financial statements"*, *"700.HK 三張表"* |
| Single statement | *"NVDA 利润表"*, *"AAPL balance sheet"*, *"TSLA 現金流量表"* |
| Cross-statement reconciliation | *"NVDA 三表勾稽"*, *"AAPL cross-statement reconciliation"* |
| DuPont decomposition | *"茅台 杜邦分析"*, *"MSFT DuPont decomposition"* |
| Earnings quality | *"TSLA 盈利质量"*, *"AAPL earnings quality"* |

**Do not trigger if:** user wants a quick KPI snapshot (use SKILL.md `financial-report`), valuation percentile (→ `alphameta-technical`), or analyst consensus (→ references/consensus.md).

## CLI Reference

> Before running any command, use `query=<command>` to check the exact argument format and available options — the CLI is updated frequently and flags may change. Do not assume argument names or positions.

```
curl http://localhost:18080/api/v1/search?query=financial-report
curl http://localhost:18080/api/v1/search?query=financial-statement
curl http://localhost:18080/api/v1/search?query=sec
```

### `financial-report` — KPI Summary

Extracts key financial metrics from income statement, balance sheet, and cash flow statement. Returns only high-level KPIs.

```
financial-report <symbol> [kind] [periods]
```

| Arg | Description | Example |
|-----|-------------|---------|
| `symbol` | Stock ticker | `AAPL`, `MSFT`, `TSLA` |
| `kind` | Statement kind: `IS`, `BS`, `CF`, or omit for all | `IS` |
| `periods` | `p1` (single), `p4`, `p8`, `all` (optional) | `p4` |

**IS KPIs**: Revenue, Gross Profit, Operating Income, Net Income, EPS
**BS KPIs**: Total Assets, Total Liabilities, Cash & Equivalents, Long-term Debt, Goodwill
**CF KPIs**: Operating Cash Flow, Capital Expenditure, Investing/Financing Cash Flow, Share Buybacks

### `financial-statement` — Full Hierarchical Statement

Returns all line items from a financial statement with complete hierarchy (indentation via `level` field). This is the **primary data source** for three-statement analysis.

```
financial-statement <symbol> [kind] [periods]
```

| Arg | Description | Example |
|-----|-------------|---------|
| `symbol` | Stock ticker | `AAPL`, `MSFT`, `TSLA` |
| `kind` | `IS`, `BS`, `CF`, or `ALL` (default: IS) | `BS`, `ALL` |
| `periods` | `p1` (single), `p4`, `p8`, `all` (optional, default: p8) | `p1` |

**Response fields** for each kind: `statement` (name), `periods` / `period`, `line_count`, `lines[]` (each: `level` for hierarchy, `label`, `values`)

### `sec` — Multi-period Financial Trends + Segments

Fetches income statement data with YoY/QoQ comparisons and optional segment breakdown.

```
sec <symbol> [year] [quarter] [periods]
```

## Workflow

1. **Resolve symbol** to ticker (e.g., `AAPL`, `MSFT`, `TSLA`, `NVDA`).

2. **Determine scope** from user intent:
   - Single statement requested → fetch that kind only.
   - Reconciliation / DuPont / earnings quality → fetch all three statements.

3. **Fetch data** (run commands concurrently where possible):

   ```bash
   # KPI-level summary (fast, always fetch first)
   financial-report <SYMBOL>

   # Full hierarchical statements (required for reconciliation/DuPont/quality)
   financial-statement <SYMBOL> ALL p8
   ```

4. **In-LLM analysis** per requested depth:

   | Analysis | Method |
   |----------|--------|
   | **三表勾稽 / Cross-statement reconciliation** | Verify: net income (IS) ≈ change in retained earnings (BS); net income + non-cash items ≈ operating cash flow (CF); ΔCash (CF) ≈ ΔCash (BS) |
   | **杜邦分解 / DuPont decomposition** | ROE = Net Margin × Asset Turnover × Equity Multiplier |
   | **盈利质量 / Earnings quality** | Accrual ratio = (Net Income − Operating CF) / Avg Total Assets; high positive ratio → earnings less cash-backed |

5. **Output structured report** using the template below. Cite **AlphaMeta / SEC EDGAR**; end with disclaimer.

## Output Template

```
{Symbol} ({ticker}) Financial Statements — Source: SEC EDGAR via AlphaMeta
Period: {report_period} | Report date: {rpt_date}

[Income Statement (IS)]
- Revenue: {value}  YoY ±{pct}%
- Gross profit / margin: {value} / {pct}%
- Operating income: {value}
- Net income: {value}  YoY ±{pct}%
- EPS (basic / diluted): {value} / {value}

[Balance Sheet (BS)]
- Total assets: {value}
- Total liabilities: {value}  |  D/E ratio: {pct}%
- Cash & equivalents: {value}
- Shareholders' equity: {value}  |  Book value per share: {value}

[Cash Flow (CF)]
- Operating CF: {value}
- Investing CF: {value}
- Financing CF: {value}
- Free cash flow (OCF − capex): {value}

[Cross-statement reconciliation]
- IS→BS: Net income vs ΔRetained earnings: {match / gap of X}
- IS→CF: Net income vs OCF bridge: {match / key non-cash items}
- CF→BS: ΔCash: {match / gap}

[DuPont decomposition]
ROE {pct%} = Net margin {pct%} × Asset turnover {X×} × Equity multiplier {X×}

[Earnings quality]
- Accrual ratio: {pct%} — {low / medium / high} accrual,
  earnings are {cash-backed / partly accrual-driven / accrual-heavy}

⚠️ 以上数据仅供参考，不构成投资建议。/ 以上數據僅供參考，不構成投資建議。/ For reference only. Not investment advice.
```

(Omit sections not requested by the user; state "data unavailable" rather than fabricating.)

## Data Limitations

| Capability | AlphaMeta | Notes |
|-----------|-----------|-------|
| Financial KPIs (IS/BS/CF) | `financial-report` ✅ | Equivalent |
| Full hierarchical statements | `financial-statement` ✅ | AlphaMeta advantage — includes all line items |
| Multi-period trends | `sec` + `financial-statement p8` ✅ | AlphaMeta advantage |
| Segment breakdown | `sec <symbol>` ✅ | AlphaMeta advantage |
| Cross-statement reconciliation | LLM in-context ✅ | Same approach |
| DuPont decomposition | LLM in-context ✅ | Same approach |
| Earnings quality analysis | LLM in-context ✅ | Same approach |
| Analyst consensus | `consensus` (via references/consensus.md) ✅ | Available as reference |

## Error Handling

| Situation | Response |
|-----------|----------|
| `financial-report` returns error | Symbol may not have SEC XBRL data or may be non-US. Try an ADR ticker for non-US companies. |
| `financial-statement` returns error | Full statement data unavailable for this symbol. Fall back to `financial-report` KPI data. |
| `sec` returns no data | Multi-period trends unavailable. Show single-period data instead. |
| Only one or two statements returned | Show available statements only; note missing ones; skip reconciliation. |
| No data for a reconciliation step | State explicitly which reconciliation was skipped — do not fabricate. |
| Symbol not found | Verify ticker symbol (e.g., AAPL, MSFT, NVDA). For non-US, try ADR ticker. |
