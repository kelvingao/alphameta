# Sector Rotation / 板块轮动

Tracks capital rotation across sectors — identifies which sectors are gaining or losing momentum.

## Current Status

AlphaMeta does not have a sector-rotation scanner or sector-level capital flow aggregation. Sector rotation analysis requires:

- Multi-stock or multi-ETF quote data across sectors
- Capital flow data at sector level
- Relative strength ranking across sectors

**Fallback**: Use WebSearch for sector rotation reports. The `capital-flow` command works at single-symbol level only and cannot be used for sector-level aggregation.
