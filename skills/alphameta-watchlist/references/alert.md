# Price Alerts

Set price-triggered alerts for symbols. Alerts are evaluated server-side and fire when the market price crosses the threshold.

> **Note**: Alerts are priced-based notifications only. For conditional triggers (RSI, EMA crossover, scheduled tasks), use `alphameta-predicate`.

## Usage

```bash
# Alert when price goes above a threshold
alert AAPL > 200

# Alert when price drops below a threshold
alert NVDA < 100

# Alert with expiration
alert TSLA > 350 --expire 2026-12-31
```

## Alert Conditions

| Symbol | Operator | Price | Behavior |
|--------|----------|-------|----------|
| `AAPL` | `>` | `200` | Fire when price rises above 200 |
| `NVDA` | `<` | `100` | Fire when price drops below 100 |
| `TSLA` | `>` | `350` | Fire above 350, expire by date |

## Gotchas

- **One alert per condition**: Create separate alerts for `>` and `<` on the same symbol.
- **No recurring alerts**: Alerts fire once then expire. Re-create after trigger.
- **Market-dependent**: Only evaluates during active trading hours for the symbol's primary exchange.
- **IBKR connection required**: Alerts are processed server-side via IBKR's alert system.

## Command Reference

| Command | Description |
|---------|-------------|
| `alert <sym> > <price>` | Alert when price rises above threshold |
| `alert <sym> < <price>` | Alert when price drops below threshold |
| `alert <sym> > <price> --expire <date>` | Alert with expiration date |
