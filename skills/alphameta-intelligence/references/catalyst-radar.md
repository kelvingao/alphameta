# Catalyst Radar / 催化剂扫描

Scans for catalysts that could move a stock — earnings surprises, insider transactions, analyst revisions, regulatory events, and large capital flows.

## Partial AlphaMeta Coverage

AlphaMeta does not have a dedicated 7-dimension catalyst scan. Use individual commands to check specific catalyst types:

| Catalyst | AlphaMeta Command |
|---|---|
| Earnings / preview | `calendar earnings`, `preview <symbol>` |
| Insider trades | `insider-trades <symbol>` |
| News / announcements | `news <symbol>` |
| Capital flow | `capital-flow <symbol>` |

## Workflow

1. Identify the symbol(s) to scan (from user query or watchlist).
2. Run available commands in parallel.
3. Present findings grouped by catalyst type.

**Note**: Dedicated multi-dimension catalyst scanning (policy changes, regulatory events, index inclusion) is not available via current AlphaMeta API. Consider using WebSearch to supplement.
