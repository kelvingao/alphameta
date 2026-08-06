# Vectorized Backtesting Framework

Vectorized backtesting computes strategy signals and portfolio returns using **array/vector operations** (pandas/NumPy) rather than iterating bar-by-bar. The entire framework is **returns-centric**: prices are only used to compute returns, and everything downstream (signals, performance, visualization) operates on returns.

```
prices → returns → strategy_returns  →  performance metrics (text)
                                   ↘  →  quantstats (PNG tear sheet)
```

It is fast, concise, and ideal for strategy research and factor testing.

> **Limitations**: Vectorized backtesting assumes perfect execution — no slippage, no latency, no fill uncertainty. It cannot model path-dependent logic (trailing stops, pyramid scaling, position-level risk limits). For production-grade simulation, use event-driven backtesting.

## When to Use This Reference

- User asks to "backtest" or "回测" a strategy
- User wants performance metrics (Sharpe, drawdown, CAGR, etc.)
- User wants to compare multiple strategies or parameter variants

## Data Preparation

### Input

Daily OHLCV data from `kline`:

| Column | Description |
|---|---|
| `date` | Trading date (UTC) |
| `close` | Adjusted close price |
| `volume` | Volume (optional) |

### Pandas Setup

```python
import pandas as pd
import numpy as np

# Load kline output into DataFrame
df = pd.DataFrame(bars)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').set_index('date')

# Daily returns — vectorized
df['return'] = df['close'].pct_change()

# Log returns (alternative, better for compounding)
df['log_return'] = np.log(df['close'] / df['close'].shift(1))
```

### Alignment

If multiple symbols are involved, align on common dates (same as pairs-trading):

```python
common_dates = sorted(set(df.index) & set(df2.index))
df = df.loc[common_dates]
```

## Core Vectorized Backtest Pattern

The entire pipeline is centered on **returns**. Prices enter once and are immediately converted; from that point on, every operation is returns × returns.

```
                     ┌──────────────┐
                     │   prices     │
                     └──────┬───────┘
                            │ pct_change()
                            ↓
                     ╔══════════════╗
                     ║   returns    ║ ◄── starting point of ALL vectorized backtests
                     ╚═════╤════════╝
                           │
                 ┌─────────┴─────────┐
                 │   signal logic    │ ← vectorized: rolling, rank, quantile...
                 └─────────┬─────────┘
                           │ shift(1) — avoid look-ahead bias
                           ↓
                 ┌──────────────┐
                 │   positions  │ ← -1 / 0 / +1 or fractional
                 └──────┬───────┘
                        │ × returns (key insight: signal × return)
                        ↓
                 ╔══════════════════╗
                 ║ strategy_returns ║ ◄── the single output that feeds everything
                 ╚═════╤════╤═══════╝
                       │    │
              ┌────────┘    └──────────┐
              ↓                        ↓
     ┌────────────────┐     ┌──────────────────┐
     │  hand-calc     │     │  quantstats      │
     │  metrics       │     │  PNG tear sheet  │
     │  (text table)  │     │  (rich viz)      │
     └────────────────┘     └──────────────────┘
```

**Critical rule — avoid look-ahead bias:**

```python
# ❌ WRONG — uses today's signal on today's return
strategy_returns = signal * returns

# ✅ CORRECT — shift signal forward: enter next bar
strategy_returns = signal.shift(1) * returns
```

### Three Signal Types

```python
# 1. Binary (-1, 0, +1) — traditional long/short/flat
positions = pd.Series(0, index=df.index)
positions[signal > threshold] = 1   # long
positions[signal < -threshold] = -1 # short

# 2. Proportional (fraction of capital per asset)
weights = signal.rank(pct=True) * 2 - 1  # −1 to +1

# 3. Rebalanced periodically (e.g. monthly)
# Not truly vectorized — requires groupby loop
for period, group in df.groupby(pd.Grouper(freq='ME')):
    weights = compute_weights(group.iloc[-1])
```

## Performance Metrics

All metrics derive from two series:
- `strategy_returns` — daily P&L of the strategy (%)
- `benchmark_returns` — daily returns of buy-and-hold (optional)

```python
# Common setup
eq_curve  = (1 + strategy_returns).cumprod()
dd        = eq_curve / eq_curve.cummax() - 1
trading_days = len(strategy_returns)
years     = trading_days / 252
```

### CAGR — Compound Annual Growth Rate

Annualized geometric return.

```python
total_return = (1 + strategy_returns).prod() - 1
cagr = (1 + total_return) ** (1 / years) - 1
```

```
CAGR = (final_equity / initial_equity)^(252 / N_days) − 1
```

### Annualized Volatility

Standard deviation of daily returns, annualized.

```python
vol = strategy_returns.std() * np.sqrt(252)
```

### Sharpe Ratio

Risk-adjusted return per unit of total risk.

```python
sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
```

| Range | Interpretation |
|---|---|
| < 0.5 | Poor |
| 0.5 – 1.0 | Acceptable |
| 1.0 – 1.5 | Good |
| 1.5 – 2.0 | Excellent |
| > 2.0 | Outstanding (suspect overfitting) |

### Sortino Ratio

Risk-adjusted return per unit of **downside** risk only.

```python
downside_returns = strategy_returns[strategy_returns < 0]
downside_vol = downside_returns.std() * np.sqrt(252)
sortino = (strategy_returns.mean() * 252) / downside_vol
```

### Max Drawdown

Largest peak-to-trough decline.

```python
max_dd = dd.min()  # negative number

# As percentage
max_dd_pct = abs(max_dd) * 100
```

### Calmar Ratio

CAGR divided by absolute max drawdown.

```python
calmar = cagr / abs(max_dd)
```

| Range | Interpretation |
|---|---|
| > 1.0 | Strong risk-adjusted return |
| 0.5 – 1.0 | Moderate |
| < 0.5 | Weak |

### Win Rate & Profit Factor

```python
trades = strategy_returns[strategy_returns != 0]
winning_trades = trades[trades > 0]
losing_trades  = trades[trades < 0]

win_rate = len(winning_trades) / len(trades) if len(trades) > 0 else 0
profit_factor = winning_trades.sum() / abs(losing_trades.sum()) if len(losing_trades) > 0 else float('inf')
avg_trade = trades.mean()
```

### Total Trades & Exposure

```python
total_trades = len(trades)        # all non-zero return days
avg_trades_per_year = total_trades / years
exposure_pct = len(trades) / trading_days * 100
```

## Quantstats Visualization

[Quantstats](https://github.com/ranaroussi/quantstats) is the standard library for strategy performance tear sheets. It takes a single **returns series** and generates a comprehensive HTML report or individual PNG charts.

```bash
pip install quantstats
```

### Full Report (HTML)

```python
import quantstats as qs

# strategy_returns is a pandas Series with DatetimeIndex
qs.reports.html(strategy_returns, benchmark_returns, output='report.html')
```

### Individual PNG Charts

> **Version note**: quantstats API changes across versions. The functions below are verified on quantstats 0.0.81+ (2026). `qs.plots.equity_curve()` does **not** exist — use `qs.plots.returns()` for the equity curve.

```python
import quantstats as qs

# Equity curve (cumulative returns)
qs.plots.returns(strategy_returns, savefig='equity.png')

# Daily returns bar chart
qs.plots.daily_returns(strategy_returns, savefig='daily_returns.png')

# Drawdown plot
qs.plots.drawdown(strategy_returns, savefig='drawdown.png')

# Drawdown periods (top N drawdowns)
qs.plots.drawdowns_periods(strategy_returns, savefig='drawdown_periods.png')

# Monthly returns heatmap
qs.plots.monthly_heatmap(strategy_returns, savefig='monthly_heatmap.png')

# Monthly returns bar
qs.plots.monthly_returns(strategy_returns, savefig='monthly_returns.png')

# Distribution of returns (histogram)
qs.plots.distribution(strategy_returns, savefig='distribution.png')

# Rolling Sharpe
qs.plots.rolling_sharpe(strategy_returns, savefig='rolling_sharpe.png')

# Rolling Sortino
qs.plots.rolling_sortino(strategy_returns, savefig='rolling_sortino.png')

# Rolling volatility
qs.plots.rolling_volatility(strategy_returns, savefig='rolling_vol.png')

# Rolling beta (vs benchmark)
qs.plots.rolling_beta(strategy_returns, benchmark, savefig='rolling_beta.png')

# Yearly returns
qs.plots.yearly_returns(strategy_returns, savefig='yearly_returns.png')

# Monte Carlo simulation
qs.plots.montecarlo(strategy_returns, savefig='montecarlo.png')
```

All `savefig` params accept either a file path string or `dict(path='...')`.

### Key Metrics (Text, if quantstats not available)

Quantstats also exposes individual metrics for text-only output:

```python
qs.stats.sharpe(strategy_returns)
qs.stats.max_drawdown(strategy_returns)
qs.stats.cagr(strategy_returns)
qs.stats.win_rate(strategy_returns)
qs.stats.profit_factor(strategy_returns)
```

### Output Strategy

| Context | Output Format |
|---|---|
| Agent generates code for user to run locally | Full Python script with `qs.reports.html()` → PNG/HTML |
| Agent replies in chat (user can't run Python) | Quantstats-style text table (see template below) |

## Quantstats-Style Output Template

Present backtest results in this structured format. This is the **in-chat text fallback** when the user cannot run Python locally. For rich visualization, see the Quantstats section above.

```
BACKTEST REPORT — Source: AlphaMeta / Interactive Brokers

Strategy: Momentum (lookback=63d)
Symbol:   SPY
Period:   2020-01-01 → 2025-12-31  (1258 trading days)

PERFORMANCE
CAGR:                  +12.4%
Cumulative Return:     +79.2%
Annualized Volatility:  18.7%

RISK-ADJUSTED
Sharpe Ratio:           1.21
Sortino Ratio:          1.68
Calmar Ratio:           0.89

DRAWDOWN
Max Drawdown:          −14.0%
Peak → Trough:         2022-01-04 → 2022-06-16
Current Drawdown:       −2.1%

TRADE STATISTICS
Total Trades:            187
Avg Trades/Year:         37.4
Win Rate:               54.3%
Profit Factor:           1.82
Avg Trade:              +0.32%
Exposure:               74.5%

BENCHMARK COMPARISON (Buy & Hold)
Benchmark CAGR:         +11.8%
Benchmark Max DD:       −19.5%
Excess Return:           +0.6%
Information Ratio:       0.15

⚠️ 以上分析仅供参考，不构成投资建议。/ For reference only. Not investment advice.
```

## Error Handling

| Situation | Response |
|---|---|
| `kline` returns < 60 bars | Insufficient history for meaningful backtest. Ask for a longer period. |
| All signals flat (zero positions) | Strategy never triggered — suggest adjusting parameters. |
| CAGR / Sharpe is NaN | Check for constant returns or all-zero signals. |
| Total return = +inf or -inf | Data contains zero prices or extreme outliers. Filter or warn. |
| Max DD = 0 | No trading occurred (all positions flat). |
| Service not running | Start the service: `alphameta --ibkr` |

## Example (Momentum — Vectorized)

```python
import pandas as pd
import numpy as np

# === Step 1: Fetch data ===
# kline SPY day 756
bars = [...]  # from AlphaMeta API

# === Step 2: Prepare ===
df = pd.DataFrame(bars)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').set_index('date')
df['return'] = df['close'].pct_change()
df.dropna(inplace=True)

# === Step 3: Signal (63-day momentum) ===
lookback = 63
df['momentum'] = df['close'] / df['close'].shift(lookback) - 1
df['signal'] = np.where(df['momentum'] > 0, 1, -1)

# === Step 4: Strategy returns (shift to avoid look-ahead) ===
df['strategy_return'] = df['signal'].shift(1) * df['return']

# === Step 5: Equity curve ===
df['equity'] = (1 + df['strategy_return']).cumprod()

# === Step 6: Performance (manual) ===
total_ret = df['equity'].iloc[-1] - 1
years = len(df) / 252
cagr = (1 + total_ret) ** (1 / years) - 1
vol = df['strategy_return'].std() * np.sqrt(252)
sharpe = (df['strategy_return'].mean() / df['strategy_return'].std()) * np.sqrt(252)
dd = df['equity'] / df['equity'].cummax() - 1
max_dd = dd.min()

# === Step 7: Quantstats visualization (optional) ===
import quantstats as qs
qs.reports.html(df['strategy_return'], output='spy_momentum_report.html')
# Or individual charts:
# qs.plots.returns(df['strategy_return'], savefig='spy_equity.png')
# qs.plots.monthly_heatmap(df['strategy_return'], savefig='spy_monthly.png')
```

## Related References

- Strategy-specific signals → see `pairs-trading.md` and other strategy references
- OHLCV data source → [`alphameta-market-data`](../../alphameta-market-data/SKILL.md)
- Risk analysis (VaR, stress test) → [`alphameta-portfolio`](../../alphameta-portfolio/SKILL.md)
