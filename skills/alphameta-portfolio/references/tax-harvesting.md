# Tax-Loss Harvesting

Prompt-only analysis skill. Scans account positions for unrealised losses, calculates potential tax saving, flags wash-sale risk, and suggests economically-similar substitute securities. Applies to US-listed securities only (US tax rules). Read-only — does not place orders.

## Important Notes

- **US tax rules only**: wash-sale rule (IRS Section 1091) applies to US investors trading US-listed securities.
- **Cost basis required**: positions must include average cost data from IBKR.
- **Not tax advice**: always consult a qualified tax professional before executing.

## Workflow

1. Fetch all positions including cost basis.
2. Fetch current prices for all positions via `quote`.
3. Compute unrealised gain/loss per position.
4. Filter to positions with unrealised losses.
5. For each loss position, compute potential tax saving (loss x estimated marginal tax rate).
6. Flag wash-sale risk (any purchase of the same or substantially-identical security within 30 days before or after the sale).
7. Suggest substitute securities that maintain similar market exposure.
8. Rank opportunities by tax saving magnitude.

## CLI

```bash
# Positions with cost basis
positions

# Current prices (run concurrently for each symbol)
quote <SYMBOL>
```

## Calculations

| Quantity            | Method                                                                                    |
| ------------------- | ----------------------------------------------------------------------------------------- |
| Unrealised loss     | (Current price - Average cost) x Quantity                                                 |
| Tax saving estimate | Unrealised loss x assumed marginal tax rate (default 37% short-term / 20% long-term)      |
| Holding period      | Today - position open date (if available); classify short-term (<1yr) or long-term (>=1yr) |
| Wash-sale window    | 30 days before + 30 days after the sale date                                              |

## Substitute Securities

When suggesting substitutes to avoid wash-sale, recommend securities that are economically similar but not "substantially identical":

| Original          | Example substitute (same sector, different issuer) |
| ----------------- | -------------------------------------------------- |
| AAPL              | MSFT, GOOGL, or QQQ ETF                            |
| SPY (S&P 500 ETF) | IVV or VOO (different fund family)                 |
| XOM               | CVX, SLB, or XLE ETF                               |
| Individual stock  | Sector ETF covering the same industry              |

Always note that substitute suitability depends on investor-specific factors; these are illustrative only.

## Output Template

```
Tax-Loss Harvesting Analysis — Source: Interactive Brokers (via AlphaMeta)
Date: <today>  Account: US Securities

[Positions with Unrealised Losses]
Symbol   Cost Basis  Current Price  Unreal. Loss  Hold Period  Tax Saving Est.
TSLA     $280.00     $210.00        -$7,000       8 months     ~$2,590 (37%)
XOM      $120.00     $108.00        -$1,200       14 months    ~$240 (20%)

[Harvesting Opportunities (ranked by tax saving)]
1. TSLA  Loss -$7,000 -> est. tax saving ~$2,590
   Substitute: RIVN / LCID / DRIV ETF (do not repurchase TSLA within 30 days)
   ⚠️ Wash-sale risk if TSLA was purchased in last 30 days

2. XOM  Loss -$1,200 -> est. tax saving ~$240
   Substitute: CVX or XLE ETF

[Wash-Sale Warnings]
- Check recent purchase dates; do not repurchase within 30 days of sale.
- Purchasing a call option on the sold stock may also trigger wash-sale.

⚠️ For reference only. Not tax or investment advice. Consult a qualified tax professional.
```

## Error Handling

| Situation | Reply |
|---|---|
| No US positions | No US positions found; tax-loss harvesting applies to US stocks only. |
| All positions profitable | All positions are in profit; no harvesting opportunities. |
| Cost basis unavailable | Cannot retrieve cost basis; check account permissions. |
