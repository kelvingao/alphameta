# Portfolio Diagnosis

Comprehensive portfolio health check — merges structural risk (concentration, sector mix, currency, factor tilt, pairwise correlation) with quantitative risk metrics (VaR, CVaR, drawdown, Sharpe, Calmar, historical scenario stress tests). One data fetch, one integrated report.

> **Response language**: match the user's input language (Simplified Chinese / Traditional Chinese / English).

## When to Use

- *"帮我诊断一下我的组合"* / *"組合診斷"* / *"diagnose my portfolio"*
- *"计算 VaR 和最大回撤"* / *"calculate VaR and max drawdown"*
- *"压力测试我的组合"* / *"run a stress test on my portfolio"*
- *"我的持仓集中度怎么样"* / *"check concentration risk in my positions"*
- *"行业分布和货币敞口"* / *"sector distribution and currency exposure"*
- *"相关性风险和因子暴露"* / *"correlation risk and factor exposure"*
- *"完整风险分析"* / *"full risk assessment"*

## Workflow

1. **Fetch account data**: `balance` and `positions` — get net liquidation, holdings with dollar values, currencies.
2. **Fetch 1-year price history**: `kline <SYMBOL> day 252` for each holding (run concurrently for all symbols).
3. **Fetch fundamental context**: `financial <SYMBOL> snapshot` for sector/industry, `financial <SYMBOL> ratios` for beta/market cap (run concurrently; skip if market closed).
4. **Compute structural metrics** in the LLM:
   - Top-5 concentration, sector/industry distribution, currency exposure
   - Factor tilt (large-cap >$10B vs small-cap; PE<15 or div yield>3% = value)
   - Pairwise Pearson correlation (60-day returns, flag r>0.8 as high)
5. **Compute quantitative metrics** in the LLM:
   - Historical VaR (95%/99%) from 252-day portfolio return distribution
   - CVaR (expected shortfall at 95%)
   - Max drawdown with peak/trough dates
   - Sharpe ratio (annual return − 4% risk-free ÷ annual volatility)
   - Calmar ratio (annual return ÷ |max drawdown|)
   - Annualised volatility (daily return std × √252)
6. **Run scenario stress tests**: apply historical index drawdowns (2008 GFC −57%, 2020 COVID −34%, 2022 rate-hike −25%) with beta adjustment.
7. **Present integrated report** using the output template.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll fetch 60d kline for correlation and 252d for VaR separately" | One 252d fetch covers both — correlation uses the last 60d, VaR uses all 252. Fewer API calls. |
| "Sector data requires a separate fundamental data subscription" | Use `financial <SYMBOL> snapshot` which returns sector/industry when available. Label as "unknown" if unavailable — don't skip the section. |
| "Ratios data is only available during market hours, skip entirely" | Still try it. If null, fall back to proxy indicators (price-based factor classification). |
| "Stress tests are too imprecise, I'll omit them" | Stress tests are illustrative but valuable. Always include with the disclaimer: *"Based on historical index drawdowns with beta adjustment. Past performance does not guarantee future results."* |
| "Single-asset portfolio doesn't need correlation or diversification analysis" | Show what you can (VaR, drawdown, stress) and note: *"Single-asset — cannot compute diversification benefit or correlation risk."* |

## Red Flags

- **Using `marketValue` instead of `dollarValue`** for weight calculations — `dollarValue` is notional, correct for concentration analysis
- **Forgetting to exclude cash-equivalent positions** (SGOV, BIL, SHV, TFLO, USFR, TBIL, CLIP, BOXX) from risk metrics — they inflate VaR/drawdown numbers
- **Treating VaR as a loss forecast** — always note: *"VaR is a historical estimate, not a prediction of future losses"*
- **Ignoring holdings with < 60 trading days of history** — they can't contribute to VaR or correlation. List separately as "insufficient history"
- **Single position > 30% of notional risk** — flag as over-concentrated
- **Portfolio with only 1-2 holdings** — correlation/diversification metrics are meaningless, skip those sections

## CLI

```bash
# Step 1: account summary + positions
balance
positions

# Step 2: 1-year daily price history for each holding (run concurrently per symbol)
kline <SYMBOL> day 252

# Step 3: fundamental context (optional — try even if market closed)
financial <SYMBOL> snapshot   # sector/industry
financial <SYMBOL> ratios     # beta, market cap (market hours only)
```

## Output

```
Portfolio Risk Diagnosis — AlphaMeta / Interactive Brokers
Analysis window: 252 trading days                    Date: <today>

[Risk Metrics]
• Daily VaR (95%, historical):  <N>%   (1-day loss not exceeded 95% of the time)
• Daily VaR (99%, historical):  <N>%   (1-day loss not exceeded 99% of the time)
• CVaR / Expected Shortfall (95%):  <N>%
• Max Drawdown (1yr):  <N>%   (peak: <date> → trough: <date>)
• Annualised Volatility:  <N>%
• Sharpe Ratio (rf=4%):  <N>
• Calmar Ratio:  <N>

[Concentration Risk]
• Top-5 holdings: <symbols> = <N>% of portfolio
• Risk level: {Low (<40%) / Medium (40-60%) / High (>60%)}

[Sector/Industry Distribution]
• <Sector>:  <N>%
• ...

[Currency Exposure]
• USD: <N>%   HKD: <N>%   CNY: <N>%   Other: <N>%

[Factor Tilt]
• Large-cap: <N>%   Small-cap: <N>%
• Value tilt: <N>%   Growth tilt: <N>%
• Portfolio beta (60-day vs SPX): <N>

[Correlation Risk]
• High-correlation pairs (r > 0.8): <list>
• Average pairwise correlation: <N>
• Diversification note: <observation>

[Scenario Stress Tests]
Scenario                  Estimated Loss     Notes
2008 GFC                  −<N>%  (~$<X>)    Based on SPX −57% draw; beta-adj.
2020 COVID crash          −<N>%  (~$<X>)    Based on SPX −34% draw; beta-adj.
2022 rate-hike cycle      −<N>%  (~$<X>)    Based on SPX −25% draw; beta-adj.
2015 A-share crash        −<N>%  (~$<X>)    Applies if holding A-shares

[Summary]
• Tail risk level: {Low / Medium / High}
• Largest risk contributor: <symbol> (<N>% of portfolio risk)
• Key concerns: <observation>
• Suggested actions: <suggestions>

⚠️ Risk metrics are based on historical data and do not predict future losses.
⚠️ 仅供参考，不构成投资建议。
```

## Key Concepts

### Cash-Equivalent Exclusion

Exclude SGOV, BIL, SHV, TFLO, USFR, TBIL, CLIP, BOXX, and money market funds from all risk calculations. Show them in a separate `(cash eq.)` group.

### Factor Tilt Classification

Classify each holding using the following rules (best-effort, using available data):
- **Large-cap**: market cap > $10B; **Small-cap**: ≤ $10B (use `financial <SYMBOL> ratios` for MKTCAP)
- **Value tilt**: P/E < 15 or dividend yield > 3%
- **Growth tilt**: P/E > 25 and revenue growth > 10%
- If ratios unavailable, classify by price (stock > $100 = large-cap heuristic) and mark as approximate

### Portfolio Return Series

For VaR and correlation, compute a daily portfolio return series:
1. For each holding, get 252-day daily close prices (from `kline`)
2. Compute daily log returns per holding
3. Weight by current dollarValue (notional) to get portfolio-level daily returns
4. Use the last 60 days for correlation, all 252 for VaR/drawdown

### VaR Methodology

- **Historical VaR**: direct percentile of the portfolio return distribution — non-parametric, no distribution assumption
- **Parametric VaR (bonus)**: μ − z·σ where z = 1.645 (95%) or 2.326 (99%) — assumes normal distribution; note this limitation
- For single-asset or 1-2 holdings, state: *"Limited diversification — VaR may understate tail risk"*

### Stress Test Beta Adjustment

```
Estimated Loss = Index Drawdown × Portfolio Beta × Holding Weight
```

Where Portfolio Beta = weighted average of individual stock betas (from `financial <SYMBOL> ratios`). If beta unavailable, use 1.0 (market average) and note the assumption.

## Error Handling

| Situation | Reply |
|---|---|
| Service not running (health fails) | Start the service: `alphameta start` |
| Empty positions | No holdings found — cannot run diagnosis |
| `kline` returns error for a symbol | Skip that symbol from VaR/correlation; note data gap |
| `financial` returns null (market closed) | Fall back to price-based factor classification; mark as approximate |
| Single-asset portfolio | Show individual metrics; skip correlation/diversification sections |
| All VaR/correlation inputs unavailable | Cannot compute risk metrics — insufficient price history |
