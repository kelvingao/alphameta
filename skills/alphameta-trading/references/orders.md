# Order Management

Place, modify, and cancel orders. Supports stocks, options, and multi-leg combo contracts.

## Use Cases

> Place a limit order to buy 100 shares of AAPL at $150
> Sell 2 option contracts (negative quantity = sell)
> Place a butterfly spread with combo syntax
> Roll a short put to the next expiration (multi-leg)

## Examples

```bash
# Buy 100 shares at market
buy AAPL 100 AF

# Sell 2 option contracts
buy NVDA260501C00175000 -2 MKT

# Butterfly spread
buy "bto 1 AAPL260716C00155000 sto 2 AAPL260716C00160000 bto 1 AAPL260716C00165000" 100 AF @ 5.00

# Roll short put (multi-leg): Buy to Close May $440 Put, Sell to Open Jun $440 Put
# Internal ratio 1:1, external qty 8 → actual 8:8
buy "btc 1 GLD260501P00044000 sto 1 GLD260618P00044000" 8 AF @ 5.35
```

## Gotchas

> **⚠️ Get confirmation before executing any orders!!!**
>
> **No `sell` command**: Use negative quantity. `buy AAPL -100` = sell 100 shares.
>
> **OCC strike must be 8 digits**: `00175000` not `175000`
>
> **`preview` to test first**: Verify margin impact before actual execution

## Commands

| Command | Description |
|---------|-------------|
| `buy` | Market/limit buy or sell (negative = sell) |
| `limit` | Limit order |
| `fast` | Fast market order (momentum scalping) |
| `evict` | Force close position at midprice |
| `expand` | Batch concurrent orders with brace expansion |
| `cancel` | Cancel order by ID or symbol |
| `modify` | Modify order price/quantity |
| `scale` | Scale-in order (multiple batches) |
| `straddle` | Straddle/strangle option quotes |

Use `search` for command details.

## Multi-Leg Orders (Roll, Spread, Combo)

For **rolling options**, **vertical spreads**, **straddles**, **iron condors**, and other multi-leg strategies, see [multi-leg.md](multi-leg.md) for full documentation including syntax, examples, and common patterns.
