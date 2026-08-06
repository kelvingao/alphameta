# Portfolio Rebalance

Prompt-only analysis skill. Compares current portfolio weights against user-provided target weights, computes drift, and produces a prioritised rebalance trade list with estimated transaction costs. Read-only — does not place orders.

## Workflow

1. Fetch current positions and total portfolio value: `balance`, `positions`.
2. Ask user for target weights if not provided (symbol -> target % pairs).
3. Fetch current prices for all symbols via `quote`.
4. Compute current weights and drift vs target.
5. Generate trade list: symbols to buy (underweight) and sell (overweight).
6. Estimate transaction cost (IBKR commission ~$0.65 per option contract, ~$0.0035 per share for stocks).
7. Present trade list sorted by drift magnitude (largest first).

## CLI

```bash
# Current holdings and portfolio value
balance
positions

# Current prices for each symbol in portfolio or target list (run concurrently)
quote <SYMBOL>
```

## Calculations

| Quantity        | Method                                                        |
| --------------- | ------------------------------------------------------------- |
| Current weight  | Position MV / Total portfolio MV                              |
| Target MV       | Total portfolio MV x target weight %                          |
| Required trade  | Target MV - Current MV (positive = buy, negative = sell)      |
| Trade quantity  | Required trade amount / current price (round to lot size)     |
| Drift threshold | Flag if |current weight - target weight| > 5 percentage points |
| Est. cost       | Trade amount x estimated commission rate (approximate)        |

## Output Template

```
Portfolio Rebalance Plan — Source: Interactive Brokers (via AlphaMeta)
Total Portfolio Value: <MV> <currency>
Date: <today>

[Current vs Target Weights]
Symbol    Current%  Target%   Drift     Action      Amt        Est.Cost
NVDA      35.2%     30.0%     +5.2%     SELL        $1,840     ~$0.65
TSLA      12.1%     20.0%     -7.9%     BUY         $2,100     ~$0.65
CASH      52.7%     50.0%     +2.7%     —           —          —

[Trade Summary]
- Total buys:  $X,XXX
- Total sells: $X,XXX
- Net cash change: +/-$XXX

[Notes]
- Positions within +/-5% of target are within tolerance and need no action.
- Sell orders on positions with unrealised gains may trigger tax events.
- Review option lot sizes before placing orders.

⚠️ For reference only. Not investment advice. Place orders via alphameta-trading.
```

## Error Handling

| Situation | Reply |
|---|---|
| No target weights provided | Please provide target weights (e.g. NVDA 30%, TSLA 20%, cash 50%). |
| Quote unavailable for a symbol | Skip that symbol; note data gap. |
| Empty positions | No open positions to rebalance. |
