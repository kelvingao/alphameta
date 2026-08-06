# Market Pulse / 行情扫描

Market strength assessment and capital flow scanning — evaluates overall market condition and identifies where money is flowing.

## Workflow

1. Market scope is US equities only.
2. Run market strength reporter for broad market assessment.
3. Run capital flow analysis on key indices or user-specified symbols.
4. Synthesize findings into a market pulse summary.

## Commands

### Market strength report

```bash
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "reporter"}'
```

### Market strength score (detailed)

```bash
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "advice"}'

# For specific symbols
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "advice SPY SPX"}'
```

### Capital flow analysis

```bash
# Default: today's intraday flow (30-min buckets)
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "capital-flow <SYMBOL>"}'

# Multi-day trend
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "capital-flow <SYMBOL> 5d"}'

# Longer period
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "capital-flow <SYMBOL> 1mo"}'
```

### Quote check for indices

```bash
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "quote SPY QQQ DIA IWM"}'
```

## Output

Structure the market pulse as follows:

**1. Market strength** (2-3 lines)

- Overall score from `reporter` or `advice`
- Key signals (VWAP distances, EMA crossovers, VIX level)

**2. Capital flow highlights** (2-3 bullets)

- Symbols or sectors with notable inflow/outflow
- Use `capital-flow` results for top movers

**3. Key levels** (1-2 bullets)

- Major index levels (SPY, QQQ levels from quotes)

## Error handling

| Situation | Response |
|---|---|
| Server not running | Tell the user to start AlphaMeta server |
| `reporter` returns no data | Fall back to `advice` for market strength |
| No capital flow data | Skip flow section; rely on quote levels |
| Other errors | Surface verbatim |
