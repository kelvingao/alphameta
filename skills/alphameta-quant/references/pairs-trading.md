# Pairs Trading / Cointegration Analysis

Statistical-arbitrage framework for a pair of correlated securities. Tests for cointegration via the Engle-Granger two-step method, estimates hedge ratio via OLS, computes spread Z-score and half-life of mean reversion, and outputs actionable long/short signals with position sizing guidance.

## Workflow

```
Step 1: Fetch OHLCV data (252 daily bars for both symbols)
Step 2: Align dates, compute log prices
Step 3: OLS regression → hedge ratio β and intercept α
Step 4: Compute spread = ln(P_A) − β × ln(P_B) − α
Step 5: ADF test on spread residuals → cointegration verdict
Step 6: Spread statistics (mean, std, Z-score)
Step 7: Half-life of mean reversion
Step 8: Generate trading signal
Step 9: Position sizing guidance
```

## CLI — Fetch Data

```bash
# Fetch 252 daily bars for both symbols
curl -X POST "http://localhost:18080/api/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kline <SYMBOL_A> day 252"}'

curl -X POST "http://localhost:18080/api/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kline <SYMBOL_B> day 252"}'
```

Run `curl "http://localhost:18080/api/v1/search?query=kline"` to confirm current command syntax.

The API returns `result.bars[]` where each bar has: `date`, `open`, `high`, `low`, `close`, `volume`.

## Step-by-Step Computation

### Step 1 — Align Dates

Extract closing prices for both symbols, then keep only dates that exist in **both** sets:

```
common_dates = sorted(set(dates_A) & set(dates_B))

if len(common_dates) < 30:
    → insufficient overlap — pairs trade not feasible
```

Use daily closing prices for both symbols on the common dates.

### Step 2 — Log Prices

```
lp_t = ln(price_t)
```

Transform both price series to log-returns space.

### Step 3 — Hedge Ratio (OLS Regression)

Regress log-price of Symbol A on log-price of Symbol B:

```
ln(P_A) = α + β × ln(P_B) + ε
```

**Least-squares solution:**

```
β = Σ((x_i − x̄)(y_i − ȳ)) / Σ((x_i − x̄)²)
α = ȳ − β × x̄

where:
  x = ln(P_B),  y = ln(P_A)
  x̄ = mean(x),  ȳ = mean(y)
```

**Interpretation:**
- β ≈ 1.15 means Symbol A moves 1.15% for every 1% move in Symbol B
- β close to 0 means prices are unrelated — not suitable for pairs trading

### Step 4 — Spread

```
spread_t = ln(P_A_t) − β × ln(P_B_t) − α
```

The spread represents the pricing error between the two securities. A cointegrated pair will have a spread that oscillates around zero (stationary).

### Step 5 — Cointegration Test (ADF)

Use the **Augmented Dickey-Fuller (ADF)** test on the spread series to check for stationarity.

**Regression:**

```
Δspread_t = α + γ × spread_{t-1} + δ × Δspread_{t-1} + ε_t
```

The null hypothesis H₀: γ = 0 (spread has a unit root — not stationary / not cointegrated).

The test statistic is the t-statistic of γ: `ADF = γ / SE(γ)`

**Critical values (MacKinnon 2010, n≈500, trend='c'):**

| Significance | Critical value |
|---|---|
| 1% | −3.44 |
| 5% | −2.87 |
| 10% | −2.57 |

**Verdict:**
- ADF < −3.44 → cointegrated at 1% (strong)
- ADF < −2.87 → cointegrated at 5% (standard threshold)
- ADF < −2.57 → cointegrated at 10% (weak, use with caution)
- ADF > −2.57 → not cointegrated — pairs trade not recommended

### Step 6 — Spread Statistics

```
μ_spread = mean(spread)
σ_spread = std(spread, ddof=1)

Z-score = (spread_current − μ_spread) / σ_spread
```

The Z-score tells you how many standard deviations the current spread is from its historical mean.

### Step 7 — Half-Life of Mean Reversion

Model the spread as a mean-reverting AR(1) process:

```
Δspread_t = ϕ × spread_{t-1} + ε_t
```

**Computation:**
1. Create `spread_lag = spread[:-1]` (spread at t-1)
2. Create `spread_diff = spread[1:] - spread[:-1]` (Δspread at t)
3. Regress `spread_diff` on `spread_lag` → slope = ϕ
4. Half-life = −ln(2) / ϕ (if ϕ < 0; otherwise not mean-reverting)

**Interpretation:**
- ϕ < 0 → mean-reverting. Smaller |ϕ| = slower reversion.
- Half-life ≈ 15 days → spread takes ~15 trading days to revert halfway to its mean
- Half-life > 252 or ϕ ≥ 0 → not mean-reverting, pairs trade is high-risk

### Step 8 — Trading Signal

| Z-score range | Signal | Action |
|---|---|---|
| Z > 2.0 | **SHORT the spread** | Short Symbol A, long Symbol B |
| Z < −2.0 | **LONG the spread** | Long Symbol A, short Symbol B |
| 0.5 ≤ |Z| < 2.0 | **WATCH** | Monitor — approaching threshold |
| |Z| < 0.5 | **NEUTRAL** | Spread near mean — no trade |

**Rationale for SHORT (Z > 2.0):**
The spread is 2+ standard deviations above its mean — historically elevated. Under the cointegration assumption, it should revert toward the mean. Short the overvalued asset (A) and long the undervalued asset (B).

### Step 9 — Position Sizing

```
# Equal-dollar weighting
Notional_per_leg = Capital / 2
Shares_A = Notional_per_leg / Price_A
Shares_B = Notional_per_leg / Price_B

# Volatility-scaled (adjusts for different volatilities)
Shares_A = Capital / (Price_A × (1 + |β|))
Shares_B = Capital × β / (Price_B × (1 + |β|))
```

**Important:** Both legs must be executed simultaneously to minimize execution risk.

## Output Template

Present results in this structured format:

```
PAIRS TRADING ANALYSIS — Source: AlphaMeta / Interactive Brokers

Pair: {Symbol_A} vs {Symbol_B}
Period: {start_date} → {end_date}  ({N} trading days)

COINTEGRATION
Log-price correlation:     {0.92}
ADF statistic:             {−3.15}
ADF critical values:       1%=−3.44, 5%=−2.87, 10%=−2.57
Verdict:                   Cointegrated at 5% ✓

HEDGE RATIO
β (slope):                 {1.15}
α (intercept):             {0.42}
Interpretation:            {Symbol_A} → 1.15 × {Symbol_B} + 0.42

SPREAD STATISTICS
Mean:                      {0.000012}
Standard deviation:        {0.0423}
Current Z-score:           {2.11}
Half-life of mean rev.:    {18} trading days

SIGNAL: SHORT the spread
Short {Symbol_A}, long {Symbol_B}

Rationale: Spread is 2.1σ above mean — historically elevated.
Mean reversion expected within ~18 trading days.

RISK NOTES
- Cointegration may break during regime changes.
- Position sizing: equal-dollar or volatility-scaled. Execute legs simultaneously.
- Stop-loss: consider exiting if Z-score exceeds ±3.0.
- Slippage and transaction costs reduce expected returns.
- Past cointegration does not guarantee future cointegration.

⚠️ 以上分析仅供参考，不构成投资建议。/ For reference only. Not investment advice.
```

## Example (Manual Walk-Through)

Given 252 daily closing prices for NVDA and AMD:

**1. Log prices:**
```
ln(NVDA_close)  →  [5.21, 5.22, 5.19, ...]
ln(AMD_close)   →  [4.78, 4.80, 4.76, ...]
```

**2. OLS hedge ratio:**
```
x = ln(AMD), y = ln(NVDA)
x̄ = 4.85, ȳ = 5.30

β = Σ((x_i − 4.85)(y_i − 5.30)) / Σ((x_i − 4.85)²) = 1.15
α = 5.30 − 1.15 × 4.85 = −0.28
```

**3. Spread and Z-score:**
```
spread_t = ln(NVDA_t) − 1.15 × ln(AMD_t) + 0.28
μ = 0.000, σ = 0.042
Z = (0.089 − 0.000) / 0.042 = 2.11
```

**4. ADF test:** Compute ADF = −3.15. Since −3.15 < −2.87 (5% critical value), reject unit root → cointegrated.

**5. Signal:** Z = 2.11 > 2.0 → **SHORT the spread**.

## Error Handling

| Situation | Response |
|---|---|
| `kline` returns < 60 bars | Insufficient history for reliable cointegration test. Ask user for a symbol with more history. |
| < 30 overlapping trading days | Symbols have too few overlapping dates — different exchanges or trading calendars. |
| Log-price correlation < 0.7 | Prices are weakly related — unlikely to find a cointegrating relationship. |
| β < 0.1 or β > 10 | Hedge ratio is extreme — prices are not structurally related. |
| ADF > −2.57 | Not cointegrated — pairs trade not recommended. Chart the spread to visualize. |
| ϕ ≥ 0 or half-life > 252 | Spread is not mean-reverting — pairs trade is high-risk. |
| Service not running | Start the service: `alphameta --ibkr` |
| Command not found | Search at runtime: `curl "http://localhost:18080/api/v1/search?query=kline"` |

## Interpretation Guide

| Metric | What it tells you |
|---|---|
| **Correlation > 0.8** | Prices move together — necessary but not sufficient for cointegration |
| **Cointegrated at 5%** | Spread is stationary — will revert to its mean over time ✓ |
| **Half-life ≈ 10–30 days** | Mean reversion within a reasonable trading horizon |
| **Z-score = 2.1** | Spread is 2.1σ above mean — statistically stretched |
| **Not cointegrated** | No statistical basis for pairs trading — relationship may drift permanently |

## Related Skills

- OHLCV data and charting → [`alphameta-market-data`](../../alphameta-market-data/SKILL.md)
- Portfolio risk analysis → [`alphameta-portfolio`](../../alphameta-portfolio/SKILL.md)
- Options strategies around volatility regimes → [`alphameta-trading`](../../alphameta-trading/SKILL.md)
- Hedge strategy design → [`alphameta-portfolio`](../../alphameta-portfolio/SKILL.md)
