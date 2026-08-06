# Event Radar / 事件雷达

Scans upcoming earnings, economic data, and IPO events — provides a forward-looking calendar with pre-earnings previews for key names.

## Workflow

1. Determine the time horizon (today / this week / next week) from user query; default to next 7 days.
2. Fetch earnings calendar, economic calendar, and IPO calendar in parallel.
3. For key earnings names, fetch `preview` for deeper context.
4. Synthesize into an event radar summary.

## Commands

### Earnings calendar

```bash
# All earnings next 7 days
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "calendar earnings"}'

# Specific symbol earnings
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "calendar earnings AAPL"}'

# Custom date range
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "calendar earnings 2026-06-20 2026-07-04"}'
```

### Economic calendar

```bash
# All economic events next 7 days
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "calendar econ"}'

# High-impact events only
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "calendar econ high"}'

# Medium or low impact
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "calendar econ medium"}'
```

### IPO calendar

```bash
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "calendar ipo"}'
```

### Pre-earnings preview (for key names)

```bash
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "preview <SYMBOL>"}'
```

## Output

Structure the event radar as follows:

**1. Earnings this week** (table)

| Date | Symbol | Company | Est. EPS | Est. Revenue |
|------|--------|---------|----------|-------------|

**2. Key earnings previews** (2-4 names with highlights)

- For major names: consensus EPS, revenue estimates, recent revisions
- Use `preview` output for each

**3. Economic data** (table or bullets)

| Date | Event | Prior | Consensus | Impact |
|------|-------|-------|-----------|--------|

**4. IPOs** (bulleted, if any)

- Upcoming IPOs with dates

## Error handling

| Situation | Response |
|---|---|
| Server not running | Tell the user to start AlphaMeta server |
| No earnings scheduled | "No major earnings reports in the selected period" |
| No economic events | "No high-impact economic data in the selected period" |
| Preview not available for a symbol | Skip that symbol's preview; note briefly |
| Other errors | Surface verbatim |
