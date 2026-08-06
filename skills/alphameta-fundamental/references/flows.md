# Institutional Flows (13F & Insider)

Institutional ownership and insider flow signals — 13F fund manager portfolios and SEC Form 4 insider transactions.

> **Response language**: match the user's input language — Simplified Chinese / Traditional Chinese / English.

## When to Use

| Trigger | Example |
|---------|---------|
| Fund manager 13F portfolio | `巴菲特最新持仓`, `Berkshire holdings`, `BlackRock 13F` |
| QoQ holding changes | `伯克希尔QoQ变化`, `Berkshire QoQ changes`, `巴菲特增持了什么` |
| Insider transactions | `AAPL 内部人交易`, `TSLA insider trades`, `苹果高管买卖` |

For general financial data (P&L, revenue, EPS), use this skill's `financial-report`. For SEC filings listing, use references/sec-filings.md.

## Data Sources

Priority: **AlphaMeta CLI (primary) → Web Search (supplement)**

All data sourced from SEC EDGAR — 13F-HR filings and Form 4 filings.

| Data Needed | Command |
|-------------|---------|
| Fund manager 13F portfolio | `investors <CIK_or_ticker>` |
| Top N holdings | `investors <CIK_or_ticker> top <N>` |
| QoQ holding changes | `investors <CIK_or_ticker> changes` |
| Insider trades | `insider-trades <symbol> [count]` |

## CLI Reference

### `investors` — SEC 13F Fund Manager Portfolio

Retrieves the latest 13F-HR filing for an institutional investment manager, showing their equity holdings, position values, and quarter-over-quarter changes.

```
investors <cik_or_ticker>
investors <cik_or_ticker> top <N>
investors <cik_or_ticker> changes
```

| Arg | Description | Example |
|-----|-------------|---------|
| `cik_or_ticker` | SEC CIK number or stock ticker | `0001067983`, `BRK-B`, `1364742` |
| `N` | Number of positions to show (for `top`) | `20`, `50` |

**Examples**:
```
investors BRK-B              # Berkshire's 13F portfolio snapshot
investors 0001067983         # Same, by CIK
investors BRK-B top 20       # Top 20 holdings
investors BRK-B changes      # QoQ holdings comparison
investors 1364742            # BlackRock 13F
```

**Response fields** (portfolio mode): `manager`, `cik`, `report_period`, `total_holdings`, `total_value`, `holdings[]` (each: `issuer`, `ticker`, `cusip`, `value`, `shares`, `pct_portfolio`, `put_call`)

**Response fields** (changes mode): `manager`, `cik`, `report_period`, `increased`/`reduced`/`unchanged` (each: `count`, `items[]` with `issuer`, `ticker`, `value`, `shares`, `prev_value`, `prev_shares`, `share_change`, `value_change`, `value_change_pct`)

### `insider-trades` — SEC Form 4 Insider Transactions

Retrieves recent insider buy/sell transactions from SEC Form 4 filings.

```
insider-trades <symbol> [count]
```

| Arg | Description | Example |
|-----|-------------|---------|
| `symbol` | Stock ticker | `AAPL`, `TSLA`, `NVDA` |
| `count` | Number of trades to return (optional, default 20) | `50` |

**Examples**:
```
insider-trades AAPL          # Last 20 insider trades
insider-trades AAPL 50       # Last 50 trades
insider-trades TSLA          # Tesla insider activity
```

**Response fields**: `symbol`, `count`, `trades[]` (each: `transaction_type`, `code`, `shares`, `price`, `value`, `date`, `insider`, `position`, `remaining_shares`)

Transaction types include: `Sale`, `Purchase`, `Gift`, `Exercise`, `Tax`, `Derivative_Sale`, etc.

## Workflow

### Fund Manager 13F

1. **Resolve the manager**: If the user provides a manager name (Berkshire, BlackRock, etc.), use these known CIKs:

   | Manager | CIK |
   |---------|-----|
   | Berkshire Hathaway (Buffett) | `1067983` |
   | BlackRock | `1364742` |

   If the user provides a ticker like `BRK-B`, the command automatically resolves CIK.

2. **Run `investors <CIK_or_ticker>`** for portfolio snapshot.
3. **Run `investors <CIK_or_ticker> top <N>`** if user wants top holdings only.
4. **Run `investors <CIK_or_ticker> changes`** if user wants QoQ comparison.

### Insider Transactions

1. **Run `insider-trades <symbol> [count]`** for the user's symbol.
2. **Analyze the results**: classify by transaction type (Sale vs Purchase vs Grant), net direction (total sold vs total bought), highlight large or unusual transactions.
3. **Flag patterns**: cluster selling near highs, first purchase after long gap, large option exercises.

## Output — 13F Portfolio Mode

```
{Manager Name} 13F Portfolio — Source: SEC EDGAR
Period: {report_period}
Total Holdings: {N}  |  Total Value: ${value}

Issuer                       Ticker     Value (USD)      % Portfolio
─────────────────────────────────────────────────────────────────────
APPLE INC                    AAPL       $57,843,260,493   21.99%
AMERICAN EXPRESS CO          AXP        $45,859,204,536   17.43%
COCA COLA CO                 KO         $30,420,000,000   11.56%
...
```

## Output — 13F Changes Mode

```
{Manager Name} QoQ Changes — Source: SEC EDGAR
Period: {report_period}

📈 INCREASED ({N} positions):
  {Issuer} ({Ticker})  shares: +{N} (+{X}%)  value: +${V}

📉 REDUCED ({N} positions):
  {Issuer} ({Ticker})  shares: {N} ({X}%)  value: ${V}

➡️ UNCHANGED ({N} positions)
```

## Output — Insider Trades Mode

```
{Symbol} Insider Trades — Source: SEC EDGAR (Form 4)

Date       | Type       | Insider           | Position       | Shares   | Price   | Value
───────────|────────────|───────────────────|────────────────|──────────|─────────|──────────
2026-05-08 | Sale       | Ben Borders       | PAO            |    1,274 | $290.00 | $369,460
2026-05-06 | Sale       | Arthur D Levinson | Director       |  149,527 | $284.57 | $42,550,898
...

Net: {N} Sales (${V}), {N} Purchases (${V}), {N} Gifts/Other
```

## Error Handling

| Situation | Response |
|-----------|----------|
| CIK not found | Could not resolve CIK. Check the ticker or use numeric CIK format (e.g., 1067983 for Berkshire). |
| No 13F filings | This entity does not file 13F-HR (only institutional investment managers with >$100M AUM file 13F). |
| No insider trades | No recent Form 4 filings. The company may be non-US or insiders may not have traded recently. |
| No QoQ data | Previous quarter holdings unavailable for comparison (may be the first filing). |
| Symbol not found | Verify the ticker symbol is correct. |
