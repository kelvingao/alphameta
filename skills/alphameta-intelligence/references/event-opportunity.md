# Event Opportunity / 事件机会

Identifies pricing dislocations from corporate events — merger arbitrage, buyback announcements, index inclusion/rebalancing, equity incentive plans, and lockup expirations.

## Current Status

Event opportunity capture is a framework-only capability. AlphaMeta does not provide:

- Merger arbitrage spread monitoring
- Index rebalancing impact analysis
- Lockup expiration calendar
- Buyback announcement tracking

**Approach**: Use WebSearch for event opportunity research. For specific opportunities identified by the user, use AlphaMeta commands (`quote`, `consensus`, `financial-report`) for fundamental analysis.

No automated event opportunity scan is available via the current API.
