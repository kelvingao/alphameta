# ETF Fund Flow / ETF资金流

Tracks capital flows into and out of sector ETFs to detect sector rotation signals. Net inflows suggest accumulation; net outflows suggest distribution. When combined with price action and volume, ETF fund flows provide early rotation cues before sector-level relative strength shifts.

## Key US Sector ETFs

| Sector | Ticker | Description |
|---|---|---|
| Technology | XLK | Software, hardware, semiconductors |
| Financials | XLF | Banks, insurance, diversified financials |
| Energy | XLE | Oil & gas, equipment, services |
| Health Care | XLV | Pharma, biotech, managed care |
| Consumer Discretionary | XLY | Retail, auto, leisure, media |
| Consumer Staples | XLP | Food, beverage, household goods |
| Industrials | XLI | Aerospace, defense, transport, machinery |
| Materials | XLB | Chemicals, metals, mining, paper |
| Real Estate | XLRE | REITs, property management |
| Utilities | XLU | Electric, gas, water utilities |
| Communication Services | XLC | Telecom, social media, entertainment |

## Workflow

### a. Identify target ETFs

Default: all 11 SPDR sector ETFs above. Optionally filter to specific sectors or add international ETFs (e.g. EEM, VWO, EFA).

### b. Fetch real-time quote for each ETF

Quote provides last price, change %, and volume. Use this to gauge immediate sector momentum.

### c. Fetch capital-flow for each ETF (5-day)

Capital flow reveals net buying/selling pressure. The `capital-flow` command returns inflow/outflow data over the specified period.

### d. Fetch kline for volume trend analysis (20-day)

Compare current volume against the 20-day average. Rising volume + positive flow = strong accumulation signal. Rising volume + negative flow = distribution.

### e. Rank ETFs by capital flow signal

Sort by net inflow (outflow) magnitude, expressed as a percentage of average daily volume. Weight by volume confidence.

### f. Identify top-3 inflow and top-3 outflow sectors

The strongest inflow sectors signal rotation target; the strongest outflow sectors signal rotation source.

### g. Synthesise sector rotation narrative

Combine flow direction, price trend, and volume confirmation to describe the current rotation landscape:

- Capital rotating INTO: Technology (XLK), Financials (XLF)
- Capital rotating OUT OF: Utilities (XLU), Consumer Staples (XLP)
- Implication: Cyclical risk-on rotation underway; defensive sectors being shed.

## CLI Examples

All commands use POST to `http://localhost:18080/api/v1/execute` with JSON payload `{"cmd": "<command>"}`.

```bash
# Single ETF quote
curl -s -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "quote XLK"}'

# 5-day capital flow
curl -s -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "capital-flow XLF 5d"}'

# 20-day kline for volume trend
curl -s -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kline XLE day 20"}'

# Batch all 11 sector tickers
for t in XLK XLF XLE XLV XLY XLP XLI XLB XLRE XLU XLC; do
  curl -s -X POST http://localhost:18080/api/v1/execute \
    -H "Content-Type: application/json" \
    -d "{\"cmd\": \"capital-flow $t 5d\"}"
done
```

Fall back to WebSearch when capital-flow data is unavailable:

> Search: `SPDR sector ETF weekly fund flows [current month] [current year]`

## Output Template

### Sector ETF Fund Flow Ranking

```
Rank | Ticker | Sector          | Price  | Chg % | Net Flow (5d) | Vol vs 20d Avg
-----|--------|-----------------|--------|-------|---------------|----------------
1    | XLK    | Technology      | 218.50 | +1.2% | +$1.8B        | 1.35x
2    | XLF    | Financials      | 42.15  | +0.8% | +$1.1B        | 1.20x
3    | XLY    | Consumer Disc.  | 195.30 | +0.5% | +$0.7B        | 1.10x
...  | ...    | ...             | ...    | ...   | ...           | ...
9    | XLU    | Utilities       | 72.40  | -0.3% | -$0.5B        | 1.40x
10   | XLP    | Consumer Staples| 84.20  | -0.1% | -$0.4B        | 1.15x
11   | XLRE   | Real Estate     | 39.80  | -0.4% | -$0.3B        | 0.90x
```

### Rotation Narrative

**Rotation Signal: Cyclical Risk-On**

Capital flowing into Technology (XLK, +$1.8B) and Financials (XLF, +$1.1B) with above-average volume, indicating institutional accumulation. Simultaneous outflows from Utilities (XLU, -$0.5B) and Consumer Staples (XLP, -$0.4B) suggest defensive rotation unwinding. Consumer Discretionary (XLY, +$0.7B) supports a growth-biased outlook.

## Error Handling

| Symptom | Likely Cause | Action |
|---|---|---|
| Empty capital-flow response | Command not supported for ETFs | Fall back to volume trend from kline + price action |
| 404 on command | `capital-flow` not installed | Use `quote` + `kline` only; add WebSearch for flow data |
| Stale quote data | Market closed | Use last available close; note market hours |
| ETF not found | Wrong ticker | Verify against sector table above |
| All flows show zero | Period too short for low-volume ETF | Extend to 10d or 20d period |
