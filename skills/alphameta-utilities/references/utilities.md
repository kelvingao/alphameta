# Utilities

Helper commands for calendars, TTS, calculator, paper trading, and system management.

> **Note**: Price alerts (`alert`) and quote group management (`qadd`, `qlist`, `qsave`, etc.) have moved to `alphameta-watchlist`.

## Use Cases

> Check economic calendar (Fed rate, CPI, NFP) for trading decisions
> Check earnings calendar for big tech report dates
> Check IPO calendar for new stock listings
> Calculate option Max Pain for specific expiration
> Get contract details with Greeks
> Export historical K-line data

## Examples

```bash
# Economic calendar (default - next 7 days)
calendar

# Earnings calendar
calendar earnings

# IPO calendar
calendar ipo

# Get contract metadata with Greeks
details AAPL

# Calculate max pain
maxpain NVDA 05-01

# Export historical K-line
daydumper AAPL 2026-01-01 2026-04-01

# Text-to-speech announcement
say "AAPL is up 2%"
```

## Gotchas

> **`advice` hangs**: Use `reporter` instead for market strength scores.
>
> **`meta` CLI bug**: Use HTTP API, not direct CLI.
>
> **IV/RV requires market data**: Without subscription, implied volatility may be unavailable.

## Commands

| Command | Description |
|---------|-------------|
| `calendar` | Financial calendar (econ/earnings/ipo) |
| `math` | Calculator (+-*/ sqrt() sin() cos()) |
| `details` | Market data with Greeks (requires subscription) |
| `maxpain` | Calculate max pain for expiration |
| `say` | Text-to-speech |
| `qualify` | Cache contract eligibility |
| `meta` | Command system metadata |
| `reporter` | Market strength score report |
| `simulate` | Simulate events for testing |
| `paper` | Switch/execute paper trading |
| `reconnect` | Reconnect IBKR Gateway |
| `clear` | Clear terminal display |
| `advice` | Market strength score (⚠️ hangs, use `reporter`) |
| `daydumper` | Export historical K-line data |

Use `search` for command details.
