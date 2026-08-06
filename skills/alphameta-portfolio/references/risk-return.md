# Risk-Return Optimisation

Risk-return optimisation — evaluate your current portfolio against the efficient frontier and get a target allocation tuned to your risk preference and investment horizon.

**Unlike Portfolio Diagnosis (which diagnoses current risk), this framework requires user input and produces a forward-looking optimisation target with rebalancing actions.**

> **Response language**: match the user's input language (Simplified Chinese / Traditional Chinese / English).

## When to Use

- *"帮我优化投资组合"* / *"优化投資組合"* / *"optimise my portfolio"*
- *"有效前沿分析"* / *"有效前沿"* / *"efficient frontier analysis"*
- *"稳健型配置应该怎么配"* / *"aggressive allocation recommendation"* / *"risk preference allocation"*
- *"提高夏普比率"* / *"improve Sharpe ratio"* / *"risk-adjusted return improvement"*
- *"我的组合该调仓了"* / *"rebalance my portfolio"* / *"suggest rebalancing"*

## Workflow

1. **Fetch account data**: `balance` and `positions` — net liquidation, holdings with dollar values, currencies.
2. **Fetch 1-year price history**: `kline <SYMBOL> day 252` for each holding concurrently.
3. **Ask the user**:
   - Risk preference: **Conservative** (低风险, max drawdown <10%) / **Balanced** (稳健, max drawdown 10-20%) / **Aggressive** (进取, max drawdown >20%)
   - Investment horizon: **Short** (1-2y) / **Medium** (3-5y) / **Long** (5y+)
   - Constraints (optional): max single-stock weight, excluded asset classes, target yield
4. **Compute current portfolio metrics**:
   - Expected return (mean of 252-day daily returns, annualised)
   - Volatility (std of daily returns, annualised)
   - Sharpe ratio (annual return − 4% risk-free ÷ annual volatility)
   - Max drawdown over the window
   - Correlation matrix of holdings
   - Concentration (top-5 weight)
5. **Build efficient frontier**: use a simplified mean-variance framework to generate frontier points from the covariance matrix and expected returns.
6. **Map user's risk profile** to the optimal point on the frontier.
7. **Compute Efficiency Gap**: distance from current portfolio to the nearest frontier point.
8. **Output target weights and rebalancing actions** — specific buy/sell amounts.
9. Convert multi-currency positions using `positions` data (already includes currency).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll skip asking the user and assume balanced/medium" | Risk preference is a required input — the entire optimisation depends on it. Always ask. |
| "Expected return = mean of past 252 daily returns" | Correct for this simplified model. State clearly: *"Past returns do not guarantee future performance."* |
| "I can compute the full efficient frontier analytically" | Use a simplified approach — discretely sample weight combinations (e.g. 0-100% equities in 10% steps with bonds/cash as counterweights) and pick the tangency/optimal portfolio per risk profile. |
| "I'll output target weights without current weights for comparison" | Always show both current AND target in the allocation table — the user needs the delta to act. |
| "Constraints are optional, skip if user doesn't answer" | Correct — but always offer: *"Any constraints? (e.g. max 30% single stock, exclude crypto)"* |
| "Cash-equivalent positions (SGOV, BIL) count as bonds" | Correct — they are cash/fixed-income equivalents for allocation purposes, not risk positions. |

## Red Flags

- **Forgetting to ask for risk preference** — optimisation without a risk target is meaningless. **Always ask before computing.**
- **Using equal weights instead of dollarValue weights** for computing current portfolio return/volatility — wrong results
- **Extending the efficient frontier beyond realistic asset classes** — limit to equities / bonds+cash / alternatives / commodities
- **Ignoring position indivisibility** — rebalancing suggestions should be realistic (round lots where practical)
- **Assuming normal distribution** — the simplified model assumes normal returns. Note this limitation.
- **Horizon mismatch** — don't recommend aggressive allocation for a 1-year horizon
- **Output too theoretical** — the user needs actionable numbers (buy $X of Y, sell $Z of W), not academic frontier coordinates

## CLI

```bash
# Current holdings with dollar values and currencies
positions

# Account equity, net liquidation
balance

# 1-year daily price history per holding (run concurrently)
kline <SYMBOL> day 252
```

## Output

```
RISK-RETURN OPTIMISATION — AlphaMeta / Interactive Brokers
Date: <today>

RISK PROFILE: {Conservative / Balanced / Aggressive}
Horizon: {1-2y / 3-5y / 5y+}

CURRENT PORTFOLIO
• Expected Return:     x.x% p.a.
• Volatility:          x.x% p.a.
• Sharpe Ratio:        x.xx
• Max Drawdown (1yr): −x.x%
• Efficiency Score:   xx/100   (distance from efficient frontier)

EFFICIENT FRONTIER (for your profile)
                      Conservative    Balanced    Aggressive
Expected Return       x.x%            x.x%        x.x%
Volatility            x.x%            x.x%        x.x%
Sharpe Ratio          x.xx            x.xx        x.xx
Max Drawdown (est.)   −<10%           −10-20%     −>20%

RECOMMENDED ALLOCATION
Asset Class           Current      Target       Delta
Equities              xx%          xx%          ±xx%
Bonds / Fixed Income  xx%          xx%          ±xx%
Cash / Cash Eq.       xx%          xx%          ±xx%
Alternatives / Comm.  xx%          xx%          ±xx%

CONCENTRATION RISK
Top holdings by weight:
1. <SYMBOL>  xx%  → Target: ≤ xx%
2. ...

REBALANCING ACTIONS
• Buy  <SYMBOL>  +$X,XXX   (to reach xx% target)
• Sell <SYMBOL>  −$X,XXX   (reduce from xx% to xx%)
• Hold <SYMBOL>            (already at target)

⚠️ This is a simplified mean-variance model. Past returns ≠ future performance.
⚠️ 仅供参考，不构成投资建议。
```

## Key Concepts

### Simplified Efficient Frontier

This framework uses a **discrete sampling approach** rather than full Markowitz optimisation:

1. Compute covariance matrix from 252-day daily returns
2. Sample asset-class weight combinations (equities 0-100% in 10% steps, bonds+cash as complement)
3. For each combination: compute expected return, volatility, Sharpe
4. Identify the frontier: the set of portfolios with maximum return for each risk level
5. Map the user's risk profile to the nearest frontier portfolio
6. Compute target weights by scaling current positions toward the frontier portfolio

### Cash-Equivalent Classification

Same convention as Portfolio Diagnosis — SGOV, BIL, SHV, TFLO, USFR, TBIL, CLIP, BOXX, and money market funds count as **Cash / Fixed Income** for allocation purposes. They are risk-free anchors in the optimisation.

### Risk Profile Mapping

| Profile | Target volatility | Max drawdown | Equity range |
|---|---|---|---|
| Conservative | < 8% | < 10% | 20-40% |
| Balanced | 8-15% | 10-20% | 40-65% |
| Aggressive | > 15% | > 20% | 65-90% |

These are guidelines — the actual frontier portfolio closest to the target volatility is selected.

### Efficiency Gap

```
Efficiency Score = (1 − distance from current to frontier) × 100
```

Where `distance` = Euclidean distance in (return, volatility) space normalised by the frontier range. Score < 50 means significant room for improvement.

### Rebalancing Actions

Compute delta per holding:
```
Delta($) = (Target_Weight − Current_Weight) × NetLiquidation
```

Positive delta = buy, negative delta = sell. Round to practical lots (whole shares for stocks). If delta < 1% of portfolio → label as "Hold (within tolerance)".

## Error Handling

| Situation | Reply |
|---|---|
| Service not running (health fails) | Start the service: `alphameta start` |
| Empty positions | No holdings found — cannot run optimisation |
| Fewer than 2 holdings | Efficient frontier requires at least 2 assets for diversification |
| Insufficient price history for a holding | Skip that holding from optimisation; note data gap |
| User declines to provide risk preference | Default to Balanced / 3-5y, note the assumption |
| Single-concentration portfolio (e.g. 100% one stock) | Show current metrics, build theoretical frontier using market proxies (SPY, AGG, SHV as reference assets), note the limitation |
