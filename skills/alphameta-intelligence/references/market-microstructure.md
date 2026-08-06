# Market Microstructure / 市场微观结构

Order book depth, bid-ask spread, and order flow pressure — reveals short-term supply/demand imbalance and price inflection zones. Focuses on resting liquidity and imminent order flow, unlike candlestick or fundamental analysis.

## Available Commands

AlphaMeta provides these microstructure-adjacent commands:

| Data Needed | Command | Description |
|---|---|---|
| Order book levels | `depth <SYMBOL> [count]` | Bid/ask ladder with volume per level |
| Capital flow | `capital-flow <SYMBOL>` | Large/medium/small order distribution |
| Current price & spread | `quote <SYMBOL>` | Last price, best bid, best ask |

## CLI Examples

```bash
# Order book (top 10 levels)
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "depth SPY 10"}'

# Capital flow
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "capital-flow AAPL"}'

# Quote for spread reference
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "quote SPY"}'
```

## In-Context Analytics (LLM Computed)

These metrics are NOT provided by AlphaMeta. The AI agent computes them from raw depth and capital-flow responses.

### 1. Weighted Bid-Ask Spread

```
weighted_spread = (best_ask - best_bid) / mid_price
```

Where `mid_price = (best_ask + best_bid) / 2`.

Interpretation:
- < 0.01%: extremely tight (large-cap US during RTH)
- 0.01-0.05%: normal liquid
- 0.05-0.20%: moderate spread (small-cap, off-hours)
- > 0.20%: wide spread (illiquid or stressed)

### 2. Depth Asymmetry

```
bid_volume = sum(volume_i) for all bid levels
ask_volume = sum(volume_i) for all ask levels
depth_asymmetry = (bid_volume - ask_volume) / (bid_volume + ask_volume)
```

Range: [-1, +1]. Positive means bid-heavy (buy-side pressure); negative means ask-heavy (sell-side pressure).

Interpretation:
- > +0.3: strong buy wall (support zone)
- < -0.3: strong sell wall (resistance zone)
- Between -0.3 and +0.3: balanced book

### 3. Large-Order Net Pressure

From `capital-flow` output, extract large-order buy vs sell volume:

```
large_order_net = large_buy_volume - large_sell_volume
```

Positive signals institutional accumulation; negative signals distribution. Cross-check medium/small order direction for divergence (e.g., large selling + small buying = retail catching a falling knife).

### 4. Order-Wall Detection

Identify price levels where resting volume exceeds the average level volume by 3x or more:

```
avg_level_volume = (total_bid_volume + total_ask_volume) / (bid_levels + ask_levels)
threshold = avg_level_volume * 3
wall_levels = [level for level in book if level.volume >= threshold]
```

Order walls act as support (bid walls) or resistance (ask walls). A wall that spans multiple consecutive levels is stronger than a single-level spike.

## Workflow

1. **Resolve symbol** — Determine the symbol from user query. US equities only.
2. **Fetch order book** — Run `depth <SYMBOL> 10` for the top 10 bid/ask levels.
3. **Fetch capital flow** — Run `capital-flow <SYMBOL>` for large/medium/small order pressure.
4. **Fetch quote** — Run `quote <SYMBOL>` for current price and best bid/ask.
5. **Compute in-context metrics** — Calculate weighted spread, depth asymmetry, large-order net pressure, and order-wall levels from raw responses.
6. **Check market hours** — If outside regular trading hours (RTH), note that depth data may be stale and spread will be wider.
7. **Synthesize report** — Structure findings into the output format below.

## Output Format

Structure the microstructure report as follows:

**Market Microstructure: <SYMBOL>**

- **Spread**: <weighted_spread>% (<best_ask> - <best_bid> at mid <mid_price>) — <tight / normal / moderate / wide>
- **Depth Asymmetry**: <value> (<bid-heavy / ask-heavy / balanced>); bid vol: <N>, ask vol: <N>
- **Order Flow Pressure**: Large net <+/-N> (<buy/sell/neutral>), Medium net <+/-N>, Small net <+/-N>
- **Order Walls**: Bid walls at <levels> (support), Ask walls at <levels> (resistance)
- **Assessment**: <1-2 sentence synthesis>

## Off-Hours Caveat

Outside regular trading hours (RTH), AlphaMeta depth data reflects the opening auction book (US) or limited pre-market liquidity. Spreads will be artificially wide and depth asymmetry may be misleading. Always check whether the market is currently in RTH before drawing microstructure conclusions. When in doubt, append a caveat: "Data reflects non-RTH conditions; depth may change substantially at the open."

## Error Handling

| Situation | Response |
|---|---|
| `depth` returns empty | Order book unavailable for this symbol; fall back to `quote` for basic spread |
| `capital-flow` returns no data | Skip flow pressure section; rely on depth alone |
| `quote` returns no bid/ask | Cannot compute spread; report "spread unavailable" |
| Symbol not found on exchange | Inform user the symbol is not traded on the target exchange |
| Depth has only 1-2 levels | Note limited book depth; depth asymmetry is less reliable |
| Server not running | Tell user to start AlphaMeta server |
