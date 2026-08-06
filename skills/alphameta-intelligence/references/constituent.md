# Constituent Stocks / 成分股

Resolves index or ETF constituent lists and enriches individual components with live market data.

## Current Status

AlphaMeta does not have a `constituent` command. Constituent data must be sourced externally, then individual symbols enriched via AlphaMeta.

| Need | Method |
|---|---|
| Constituent list | WebSearch (see queries below) |
| Top holdings weight | WebSearch (ETF issuer site, Morningstar) |
| Real-time price per symbol | `quote <SYMBOL>` |
| Historical price per symbol | `kline <SYMBOL> day <count>` |

## Workflow

1. Determine the target index or ETF (e.g., SPX, SPY, QQQ).
2. WebSearch for the constituent list using targeted queries.
3. Extract symbols from search results.
4. Enrich selected symbols via `quote` and `kline`.
5. Present as a structured table with symbol, price, change %, and weight.

## Example WebSearch Queries

| Market | Query |
|---|---|---|
| US Index | "S&P 500 constituents list 2026", "SPY top 10 holdings" |
| US Sector ETF | "XLF holdings", "QQQ top holdings" |

## CLI Enrichment

```
quote AAPL MSFT GOOGL NVDA AMZN
kline AAPL day 20
```

## Common Index References

| Ticker | Name | Region |
|---|---|---|
| ^GSPC / SPX | S&P 500 | US |
| ^DJI | Dow Jones Industrial Avg | US |
| ^IXIC | NASDAQ Composite | US |

## Error Handling

| Scenario | Handling |
|---|---|
| Constituent list not found | Try alternative query (e.g., "holdings" instead of "constituents") |
| Symbol not recognized by AlphaMeta | Map to IBKR format or verify symbol spelling |
| Too many constituents (e.g., S&P 500) | Ask user for subset or top-N; do not spam 500 quotes |
