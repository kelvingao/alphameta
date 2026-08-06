# ETF Analysis / ETF分析

Multi-dimension evaluation of US-listed ETFs — covering product profile, tracking accuracy, liquidity, premium/discount dynamics, and allocation fit.

## AlphaMeta Coverage

AlphaMeta does not have a dedicated ETF analysis command. Use these commands to construct an ETF profile:

| Analysis Need | AlphaMeta Command |
|---|---|
| Real-time price & volume | `quote <symbol>` |
| Historical price series | `kline <symbol> day <count>` |
| Valuation / composite metrics | `calc-index <symbol>` |
| Capital flow intensity | `capital-flow <symbol>` |

For missing data (AUM, expense ratio, NAV, underlying index details, holdings overlap), use WebSearch to supplement.

## Five-Dimension Framework

### 1. Product Profile

- **Underlying index** — extract from WebSearch (e.g., SPY tracks S&P 500, QQQ tracks Nasdaq-100)
- **AUM proxy** — approximate from recent volume x price; for precise AUM use WebSearch
- **Expense ratio** — WebSearch only (AlphaMeta has no fee data)
- **Inception date** — WebSearch only

```bash
# Price baseline for sizing
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "quote SPY"}'

# Valuation context
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "calc-index SPY"}'
```

### 2. Tracking Error

Annualised tracking error = std(ETF daily return - benchmark daily return) x sqrt(252).

```bash
# Fetch last 60 daily bars for ETF
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kline SPY day 60"}'

# Fetch same period for benchmark proxy (e.g., SPX index ETF)
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kline SPY day 60"}'
```

Compute in Python / spreadsheet outside AlphaMeta:
- daily_return_etf = (close_t - close_t-1) / close_t-1
- daily_return_bench = (close_t - close_t-1) / close_t-1
- diff = daily_return_etf - daily_return_bench
- TE = std(diff) x sqrt(252)
- TE under 0.50% indicates tight tracking; above 1.00% suggests tracking drift.

### 3. Liquidity Assessment

```bash
# Volume and bid-ask spread proxy from quote
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "quote XLF"}'

# Capital flow confirms institutional participation
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "capital-flow XLF"}'
```

Assess from quote: daily volume, bid size, ask size. Narrow spread (below 0.05%) with volume > 1M shares indicates institutional-grade liquidity.

### 4. Premium / Discount

NAV is not available via AlphaMeta. Use the gap between market price and indicative value:

- `quote` shows last trade price vs bid/ask midpoint
- Persistent premium (price > indicative value for 5+ days) may signal high demand or creation/redemption friction
- Persistent discount may signal structure issues or low demand
- Flag any deviation > 0.50% for further WebSearch investigation

### 5. Allocation Fit

| ETF Type | Examples | Role in Portfolio |
|---|---|---|
| Broad market | SPY, VTI, IVV | Core U.S. equity beta |
| Sector | XLK, XLE, XLV | Thematic tilt |
| Factor / smart beta | MTUM, QUAL, USMV | Risk-factor exposure |
| International | EFA, EEM, VWO | Geographic diversification |

```bash
# Quick price check across categories
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "quote SPY XLK MTUM EFA"}'
```

Cross-reference with `calc-index` for valuation context and `capital-flow` for recent money flows.

## Workflow

1. Confirm the ETF symbol and the user's analysis goal (sizing, tracking check, liquidity, or allocation fit).
2. Run `quote <symbol>` for current price, volume, and spread context.
3. Run `kline <symbol> day 60` for tracking error calculation.
4. Run `calc-index <symbol>` and `capital-flow <symbol>` for valuation and flow context.
5. Use WebSearch for AUM, expense ratio, NAV, and underlying index details.
6. Synthesize findings across the five dimensions into the output template.

## Output Template

**SPY ETF Profile**
- **Product**: S&P 500 Index, ~$500B+ AUM, 0.09% ER, 1993 inception
- **Tracking**: ~0.03% annualised (tight); daily tracking difference within 0.01%
- **Liquidity**: 40M+ avg volume, penny-wide spreads (0.01%)
- **Premium/Discount**: Trades within 0.10% of NAV historically; current near par
- **Fit**: Core U.S. large-cap beta; suitable as primary equity holding

## Error Handling

| Situation | Response |
|---|---|
| Server not running | 请启动 AlphaMeta 服务器 / Start the AlphaMeta server |
| `quote` returns no data | 无法获取实时价格，请检查代码 / Cannot fetch real-time price, check symbol |
| `kline` data insufficient for TE | 60根日K线是计算跟踪误差的最低要求 / 60 daily bars is the minimum for tracking error |
| WebSearch unreachable | 基础数据来自行情，产品细节无法补充 / Product details unavailable without web search |
| Symbol not found | 未找到该代码，请确认ETF代码是否正确 / Symbol not found, verify the ETF ticker |
| Other errors | 直接返回错误信息 / Surface the error verbatim |
