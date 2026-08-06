# Screener / 策略筛选

Stock screening — filtering and ranking stocks by valuation, consensus, and financial metrics.

## Partial AlphaMeta Coverage

AlphaMeta does not have a bulk stock screener command. Use these commands for single-symbol screening checks:

| Screening Need | AlphaMeta Command | Alias / Fallback |
|---|---|---|
| Valuation percentile (PE/PB) | `calc-index <symbol>` | — |
| Consensus / ratings | `consensus <symbol>` | — |
| Financial KPIs | `financial-report <symbol>` | `financial-statement <symbol>` (same data) |
| Operating trends | `operating <symbol>` | — |
| Quote & price | `quote <symbol>` | — |
| Capital flow | `capital-flow <symbol>` | — |

> ⚠️ **If a command is not found**, run `curl http://localhost:18080/api/v1/search` to list all available commands. Some commands may have been renamed or aliased in newer versions.

## Single-Symbol Workflow

1. Ask the user for specific screening criteria (valuation, sector, market cap, etc.).
2. If a specific symbol is given, run the relevant single-symbol checks:
   - `calc-index <symbol>` — PE/PB percentile, valuation band
   - `consensus <symbol>` — analyst ratings, target price
   - `financial-report <symbol>` — revenue, EPS, margins
   - `operating <symbol>` — operating metrics, trends
3. Synthesize findings into a concise screening card.
4. For multi-stock screening, proceed to the Bulk Screening Workflow below.

---

## Bulk Screening Workflow / 批量筛选工作流

When the user asks to **find stocks meeting certain criteria** (e.g., "low PE high growth tech stocks", "stocks with PE under 15 and revenue growth over 20%"), AlphaMeta cannot perform this directly. Use **WebSearch** as the discovery layer, then enrich candidates with AlphaMeta.

### Step 1 — Determine Screening Criteria

Clarify the user's screening dimensions. Reference this criteria table:

| Dimension | Metric | Example Criteria |
|---|---|---|
| 估值 Valuation | PE, PB, PS, EV/EBITDA | PE < 15, PB < 2 |
| 成长 Growth | Revenue YoY%, EPS YoY% | Revenue growth > 20% |
| 盈利质量 Quality | ROE, ROIC, Gross Margin | ROE > 15%, Gross Margin > 40% |
| 动量 Momentum | 3M/6M return, RSI | 6M return > 10%, RSI < 70 (not overbought) |
| 规模 Size | Market Cap | Market cap > $50B |
| 板块 Sector | Sector/Industry filter | Tech, Healthcare, Consumer |
| 分红 Dividend | Div Yield, Payout Ratio | Div Yield > 2% |

### Step 2 — WebSearch for Candidates

Construct a targeted WebSearch query based on the user's criteria. Optimize query language based on target market:

**US Market** (English queries): Use specific financial terms, timeframes, and ranking intent.

| Scenario | Sample WebSearch Query |
|---|---|
| Low PE + high growth | `"stocks with PE ratio under 15 and revenue growth over 20% 2026"` |
| Large cap tech value | `"US tech stocks market cap over 50B PE under 25"` |
| High ROE | `"companies with ROE above 20% profitable 2026"` |
| Undervalued dividend | `"undervalued dividend stocks PE under 15 yield above 3%"` |
| Growth at reasonable price | `"GARP stocks 2026 PEG ratio under 1.5"` |
| Small cap growth | `"small cap growth stocks revenue growth 30% 2026"` |
| Sector leader | `"sector leader stocks strong balance sheet 2026"` |

### Step 3 — Extract & Rank Candidates

From search results, extract candidate symbols with key metrics. Use **cross-source verification** — prefer symbols appearing in 2+ sources; flag single-source candidates as "unverified."

Build a structured summary:

```
Search results identified these candidates meeting [criteria]:

## Cross-Source Confidence
Source A (VCP Scanner): AAPL, GOOGL, MSFT, AVGO, SMCI
Source B (MarketsHost): NVDA, ANET, CRDO, AVGO, MU
Source C (Yahoo Finance): SMCI, DUOL, CALM, GEN, UHS
→ Overlap (high confidence): AVGO (A+B), SMCI (A+C)
→ Single source (verify first): AAPL, DUOL, CALM, GEN, UHS

## Extracted Candidates
1. AAPL — PE: 28, Growth: 8%, Mkt Cap: $2.8T   [source: A only]
2. SMCI — PE: 17, Growth: 56%, Mkt Cap: $30B    [source: A+C]
3. DUOL — PE: 14, Growth: 35%, Mkt Cap: $6B     [source: C only]
...
```

⚠️ **WebSearch data is often imprecise or stale** — IRL testing showed a stock reported as PE 7.8 actually had PE 75.4. Always:
1. Cross-reference 2+ sources before trusting any single metric
2. Note source conflict clearly (e.g. "PE: 7.8 (src A) vs 75.4 (src B)")
3. Offer to enrich with AlphaMeta — the only source of truth

### Step 4 — Enrich with AlphaMeta (Phased Execution)

Run commands in **priority order** — stop early if a candidate fails the primary filter, saving API calls:

```text
Phase 1 — Quick Valuation Filter (run ALL candidates in parallel):
  calc-index <SYMBOL>       # PE/PB percentile → eliminates bad matches fast
  quote <SYMBOL>            # Current price, volume, spread

Phase 2 — Deep Dive (only for candidates that passed Phase 1):
  operating <SYMBOL>        # Revenue, margins, EPS, ROE trends
  consensus <SYMBOL>        # Analyst ratings, target price
  capital-flow <SYMBOL>     # Fund flow direction, MFI
  financial-report <SYMBOL> # Full financial KPIs (if more detail needed)
```

**Execution tips:**
- Run `calc-index` for ALL candidates first — it is the fastest filter
- Only proceed to Phase 2 for candidates whose PE/PB falls within the user's criteria
- All Phase 1 calls can run in parallel (one `bash` per symbol)
- All Phase 2 calls can also run in parallel per symbol
- If `consensus` returns no data (timeout or empty), skip it and note "no analyst data"
- If `operating` returns `None`/`null` for any field, fall back to WebSearch or mark as "N/A"

### Step 5 — Output Screening Table

Format results into a structured table. Handle missing data gracefully:

| Symbol | Price | PE | Rev Growth% | ROE% | Analyst Rating | Upside% | Flow |
|--------|-------|----|-------------|------|----------------|---------|------|
| AAPL | $198 | 28 | 8% | 35% | Buy (42) | +12% | +$120M |
| DUOL | $121 | 13.9 | 36% | 4.6% | Hold (23) | -12% | -$26M |
| UHS | $149 | 6.3 | N/A¹ | N/A¹ | Buy (20) | +43% | +$5.7M |
| SMCI | $42 | N/A² | 56% | — | — | — | — |

**Notes for missing data:**
- ¹ `operating` returned `None` for some quarters — show the latest quarter with data, mark missing as "N/A¥"
- ² `calc-index` returned `null` PE (negative earnings or data gap) — check `quote` for price, mark PE as "Neg" or "N/A"
- If `consensus` timed out (>20s), skip and note "no analyst data"

**Guide the user** with a recommendation: which symbols look most attractive based on combined criteria.

---

## WebSearch Fallback / WebSearch 兜底

| Situation | Response |
|---|---|
| WebSearch returns no useful candidates | "WebSearch could not find stocks matching your criteria. Suggest refining: try broader criteria (e.g., higher PE cap, lower growth floor) or a different market." |
| WebSearch returns symbols but no metrics | Extract symbols and run AlphaMeta commands to backfill data manually |
| AlphaMeta command fails for a symbol | Skip that symbol and note "data unavailable"; continue with remaining candidates |
| User wants real-time screening data | "AlphaMeta does not support bulk real-time screening. WebSearch provides approximate data. For live screening, consider dedicated platforms (Finviz, TradingView, Bloomberg)." |
| Criteria is too complex for a single search | Break into multiple WebSearch queries; cross-reference results for overlap |

## Errors / 错误处理

| Situation | Response |
|---|---|
| No criteria provided | "Please tell me what you're looking for — valuation range, sector, growth rate, or a specific metric." |
| No matching symbols found | "No stocks found matching these criteria. Try relaxing the constraints." |
| `calc-index` fails or returns `null` PE | Skip valuation check for that symbol; check `quote` for price; note "negative earnings" or "no data" |
| `operating` returns `None` for revenue/EPS fields | Mark those fields as "N/A" in the output table; use the latest available quarter only |
| `consensus` fails or times out (>20s) | Note "no analyst data"; proceed with other checks |
| `quote` returns `last: $0.00` (wide spread, no trade) | Use `(bid + ask) / 2` as the reference price; mark as "wide spread" |
| WebSearch unavailable | "Web search is not available right now. Please provide specific symbols for single-symbol screening." |
| Only 1-2 candidates found | Present what's available; note "limited matches" and suggest broader criteria |
| Command not found (e.g. `financial-report`) | Run `curl http://localhost:18080/api/v1/search` to find the correct command name; try alias if known |
| Multi-source PE conflict (e.g. 7.8 vs 75.4) | Always trust AlphaMeta `calc-index` as source of truth; note the discrepancy in output |
