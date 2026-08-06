# Event-Driven Strategy / 事件驱动策略

Identifies trading opportunities from corporate events — M&A, buybacks, spinoffs, index changes, management transitions — using NLP sentiment analysis on news and filings.

## Current Status

Event-driven strategy is a framework-only capability. AlphaMeta does not provide:

- NLP sentiment scoring on news or announcements
- Automated M&A / buyback / spinoff detection
- Corporate event classification and signal generation

**Approach**: Use WebSearch for event detection and sentiment analysis. Use AlphaMeta commands (`news`, `filings`, `calendar`, `quote`) for data once an event is identified.

No automated event-driven strategy pipeline is available via the current API.
