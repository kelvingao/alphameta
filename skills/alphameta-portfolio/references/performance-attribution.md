# Performance Attribution

Prompt-only analysis skill. Decomposes a portfolio's return into attributable components using Brinson-Hood-Beebower sector attribution. Answers: "did I add value through sector allocation or position selection?"

## Workflow

1. Fetch portfolio positions and P&L: `balance`, `positions`.
2. Fetch benchmark daily candles (default: SPY for US equities).
3. Fetch each position's daily candles (up to 10 positions; skip if > 10).
4. **Brinson Attribution** (use current weights from positions; group by sector):
   - Allocation effect = (w_p,i - w_b,i) x (r_b,i - r_b)
   - Selection effect = w_b,i x (r_p,i - r_b,i)
   - Interaction = (w_p,i - w_b,i) x (r_p,i - r_b,i)
   - Total active return = sum of all three
5. Present Brinson table by sector.

## CLI

```bash
# Positions and portfolio value
balance
positions

# Benchmark daily candles
# Use alphameta-market-data kline command
kline SPY --period day --count 252

# Each position's daily candles (run concurrently, max 10)
kline <SYMBOL> --period day --count 252
```

## Output

| Component          | Description                          |
| ------------------ | ------------------------------------ |
| Allocation effect  | Value from sector weighting decisions |
| Selection effect   | Value from stock selection within sectors |
| Interaction effect | Combined allocation + selection impact |
| Total active return | Sum of all three effects             |

Brinson table by sector -> interpretive summary.

```
Performance Attribution — Source: Interactive Brokers (via AlphaMeta)
Benchmark: SPY  Date: <today>

[Brinson Attribution by Sector]
Sector        Portfolio%  Benchmark%  Allocation  Selection   Interaction
Technology    45%         30%          +1.2%       +0.8%       +0.1%
Financials    10%         15%          -0.5%       +0.3%       -0.1%
...           ...         ...          ...         ...         ...

[Summary]
- Total active return: +2.1%
- Allocation effect: +0.7% (sector weighting added value)
- Selection effect: +1.5% (position selection was the main driver)
- Interaction: -0.1%

⚠️ For reference only. Not investment advice.
```

## Error Handling

| Situation | Reply |
|---|---|
| Empty positions | No positions found; nothing to attribute. |
| > 10 positions | Attribution limited to top-10 positions. |
| Kline data unavailable for a symbol | Skip that symbol; note data gap. |
