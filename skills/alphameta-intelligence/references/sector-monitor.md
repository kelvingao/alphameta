# Sector Monitor / 板块监控

Tracks sector strength and weakness over time — combines price momentum, capital flow, and valuation data to identify leading and lagging sectors.

## Current Status

AlphaMeta does not have sector-level data aggregation or sector monitoring tools. Sector monitoring requires:

- Sector classification for individual stocks
- Aggregated sector-level price and flow data
- Relative strength ranking across sectors

**Fallback**: For individual sector ETF analysis, use `quote` to check price levels and `capital-flow` for flow data on specific sector ETFs (e.g., XLK.US, XLF.US). No automated multi-sector monitoring is available.
