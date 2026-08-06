# Analyst Consensus

Analyst consensus estimates and ratings via AlphaMeta — price targets, EPS/revenue forecasts, analyst rating distribution, beat/miss history, and estimate revision trend. Data sourced from yfinance + Finnhub.

> **Response language**: match the user's input language — Simplified Chinese / Traditional Chinese / English.

## When to Use

| Trigger | Example |
|---------|---------|
| Consensus snapshot | *"AAPL 分析师预期"*, *"TSLA consensus"*, *"NVDA analyst estimates"* |
| EPS/营收预测 | *"MSFT 下季度 EPS 预期多少"*, *"AAPL next quarter EPS forecast"* |
| 目标价 | *"NVDA 目标价多少"*, *"TSLA price target"* |
| 评级分布 | *"AAPL 多少分析师买入"*, *"how many analysts buy MSFT"* |
| Beat/miss 历史 | *"TSLA 上季超预期了吗"*, *"did AAPL beat last quarter"* |
| 预期修正 | *"MSFT 预期有在调吗"*, *"NVDA estimate revision trend"* |

**Do not trigger if:** user wants fundamentals (→ use this skill's `financial-report`), valuation percentile (→ `alphameta-technical`).

## CLI Reference

### `consensus` — Full Consensus Snapshot

```
consensus <symbol>
```

| Arg | Description | Example |
|-----|-------------|---------|
| `symbol` | Stock ticker | `AAPL`, `MSFT`, `TSLA`, `NVDA` |

**Examples**: `consensus AAPL`, `consensus MSFT`, `consensus NVDA`

### Response Fields

The command returns a structured JSON with the following sections:

**`analyst_ratings`** — Coverage and rating distribution:
```
total_analysts  total number of analysts covering
strong_buy      strong buy count
buy             buy count
hold            hold count
sell            sell count
strong_sell     strong sell count
```

**`price_target`** — Analyst price targets:
```
mean    mean target price
high    highest target price
low     lowest target price
```

**`eps_estimates`** / **`revenue_estimates`** — Period-level estimates with low/avg/high range:
```
# Period keys: 0q (current quarter), +1q (next quarter),
#              0y (current fiscal year), +1y (next fiscal year)
0q:
  avg              mean estimate
  low              lowest estimate
  high             highest estimate
  numberofanalysts # of analysts providing estimate
  growth           YoY growth rate
  yearagoeps       actual EPS from prior year same quarter (for reference)
```

**`revision_trend`** — EPS estimate changes over time (per period):
```
0q:
  current       current EPS estimate
  7daysago      estimate 7 days ago
  30daysago     estimate 30 days ago
  60daysago     estimate 60 days ago
  90daysago     estimate 90 days ago
```

**`revision_direction`** — Inferred revision direction:
```
overall             "rising" / "falling" / "flat" / "mixed"
rating              "upgrading" / "downgrading" / "stable"
eps                 "upward" / "downward" / "stable"
eps_30d_change_pct  EPS estimate change over 30 days (%)
eps_90d_change_pct  EPS estimate change over 90 days (%)
```

**`beat_miss_history`** — Historical earnings vs estimates:
```
date           earnings date
estimate_eps   pre-earnings EPS estimate
reported_eps   actual reported EPS
surprise_pct   surprise percentage
```

**`valuation`** — Key valuation metrics:
```
forward_pe          forward P/E
trailing_pe         trailing P/E
market_cap          market capitalization
eps_ttm             trailing twelve months EPS
dividend_yield_pct  dividend yield (%)
beta                beta
```

## Workflow

1. **Resolve symbol** to ticker (e.g., AAPL, MSFT, TSLA).
2. **Run command**: `consensus <symbol>`
3. **Synthesize** into the output template below.

### Optional: Cross-reference with actual financials

For beat/miss analysis, you may also want to call `financial-report` (this skill) for the actual reported financial data alongside consensus.

## Output Template

```
{symbol} Consensus — Source: yfinance + Finnhub
As of: {date}

[Coverage & Ratings]
- Analysts covering: {total} | Strong Buy: {sb} / Buy: {b} / Hold: {h} / Sell: {s} / Strong Sell: {ss}
- Median target: ${pt} | Range: [${low} – ${high}]

[EPS Consensus]
- Current quarter: avg {avg}, range [{low} – {high}]
- Next quarter:    avg {avg}, range [{low} – {high}]
- Current FY:      avg {avg}, range [{low} – {high}]
- Next FY:         avg {avg}, range [{low} – {high}]

[Revenue Consensus]
- Current quarter: avg {avg}, range [{low} – {high}]
- Current FY:      avg {avg}, range [{low} – {high}]

[Estimate Revision Trend]
- Direction (30/90 days): {overall direction}
- EPS 30d change: {+X%} | EPS 90d change: {+X%}
- Rating trend: {upgrading / stable / downgrading}

[Beat/Miss History (last 4 quarters)]
| Date       | Estimate | Actual | Surprise |
|------------|----------|--------|----------|
| {date}     | {est}    | {act}  | {±X.X%}  |

[Valuation]
- Forward P/E: {X.X} | Trailing P/E: {X.X}
- Market Cap: ${X}B | Beta: {X.X}

⚠️ 以上数据仅供参考，不构成投资建议。/ 以上數據僅供參考，不構成投資建議。/ For reference only. Not investment advice.
```

## Data Limitations

| Capability | AlphaMeta | Notes |
|-----------|-----------|-------|
| Rating distribution | `consensus` ✅ | Equivalent |
| Price target | `consensus` ✅ | Equivalent (mean/high/low) |
| EPS estimates (period) | `consensus` ✅ | 4 periods: 0q/+1q/0y/+1y |
| Revenue estimates (period) | `consensus` ✅ | 4 periods |
| Estimate revision trend | `consensus` ✅ | Direction inferred from eps_trend + rating change |
| Beat/miss history | `consensus` ✅ | Last 4+ years |
| Analyst upgrade/downgrade detail | ⚠️ Direction only | No per-firm event detail |
| PEAD signal | ⚠️ LLM inferred | Same approach — LLM reasons from beat_miss + revision_direction |

## Error Handling

| Situation | Response |
|-----------|----------|
| `consensus` returns error | Symbol may be non-US or delisted. Verify ticker. |
| Some fields missing | EPS/revenue estimates may be less common for non-US symbols. Price targets require analyst coverage. |
| No beat/miss history | Newly public companies may have short history. |
| Rate limited | yfinance has rate limits; wait and retry. |
| Symbol not found | Verify ticker symbol (e.g., AAPL, MSFT, NVDA). |
