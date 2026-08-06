# Asset Allocation

Prompt-only educational reference. Explains major asset-allocation frameworks (MPT efficient frontier, risk parity, all-weather) and, when applied, uses account data for context.

## Frameworks

### MPT (Modern Portfolio Theory)

- Compute expected return (historical mean daily return x 252) and covariance matrix from 252-day returns.
- Find minimum-variance portfolio and tangency portfolio (max Sharpe).
- Caution: MPT is sensitive to input estimation error; treat outputs as directional.

### Risk Parity

- Allocate so each asset contributes equally to total portfolio volatility.
- Simplified: weight ~ 1 / volatility.
- Result: typically overweights low-volatility assets vs equities.

### All-Weather (Bridgewater style)

- 4 economic quadrants: growth up/down x inflation up/down.
- Reference weights: 30% equities, 40% long bonds, 15% intermediate bonds, 7.5% gold, 7.5% commodities.
- Map user's holdings to quadrant exposure; identify gaps.

## CLI

```bash
# Current holdings (if user wants to analyse their actual portfolio)
balance
positions

# 252-day daily price history for each holding (run concurrently)
# Use alphameta-market-data kline command
kline <SYMBOL> --period day --count 252
```

## Output Template

```
Asset Allocation Analysis — Source: Interactive Brokers (via AlphaMeta)
Framework: <MPT / Risk Parity / All-Weather>
Date: <today>

[Current Portfolio]
Asset       Weight   Expected Return   Volatility (ann.)
<symbol>    <N>%     <N>%              <N>%

[Suggested Allocation — <Framework>]
Asset       Target Weight   Rationale
<symbol>    <N>%            <reason>

[Key Metrics]
- Portfolio expected return (ann.): N%
- Portfolio volatility (ann.): N%
- Sharpe ratio (rf=4%): N

[Caveats]
- Historical returns do not guarantee future results.
- Covariance estimates are noisy over short windows.
- <framework-specific caveats>

⚠️ For reference only. Not investment advice.
```
