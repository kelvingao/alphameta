# AlphaMeta CLI Overview

All commands run via `POST /api/v1/execute`. Use the server's command registry at runtime — it's always up-to-date.

## Discovering Commands

Always use the search endpoint — it reflects the currently running server version:

```bash
# List all commands grouped by category
curl http://localhost:18080/api/v1/search

# Search for a specific command
curl "http://localhost:18080/api/v1/search?query=quote"

# List commands in a specific category
curl "http://localhost:18080/api/v1/search?category=Market+Data"
```

Do not rely on hardcoded command names or flags — use the search endpoint instead.

## Command Execution

```bash
curl -X POST http://localhost:18080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"cmd": "<command> [args]"}'
```

**Response format:**
```json
{
  "success": true,
  "result": { ... },
  "request_id": "...",
  "execution_time_ms": 123
}
```

On error, the response includes `error.code` and `error.message`.

## CLI Categories

Use these category names to filter the search endpoint:

| Category | Typical Commands | Related Skill |
|---|---|---|
| `Market Data` | Real-time quotes, option chains, market depth, subscription | `alphameta-market-data` |
| `Trading` | Place, modify, cancel, preview, fast/scale/evict orders | `alphameta-trading` |
| `Portfolio` | Positions, P&L, balance, asset distribution | `alphameta-portfolio` |
| `Automation` | Conditional triggers, scheduled tasks | `alphameta-predicate` |
| `Watchlist` | Watchlist groups, snapshots | `alphameta-watchlist` |
| `Technical` | Greeks, IV, max pain, gamma exposure | `alphameta-technical` |
| `Fundamental` | Financial statements, SEC filings, KPIs | `alphameta-fundamental` |
| `Utilities` | Calendar, TTS, calculator, paper trading, reporter | `alphameta-utilities` |
| `Connection` | Health, reconnect, server info | `alphameta` |
| `Task Management` | Async task lifecycle | — |

## Execution Tips

- **Quote groups**: commands like `qadd`, `qlist`, `qsave` persist subscriptions across sessions
- **Option chains**: run `chain <SYMBOL> <MM-DD>` first to discover valid OCC symbols before using `info` or `order`
- **Orders**: always preview first (`order preview <spec>`) before executing — see `alphameta-trading`
- **Search is your friend**: if unsure what command to use, `curl "http://localhost:18080/api/v1/search?query=<keyword>"` will show all matching commands with descriptions
