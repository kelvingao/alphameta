# Anomaly / 异动检测

Detects unusual price movements, volume spikes, or abnormal market activity.

## Partial AlphaMeta Coverage

AlphaMeta does not have a dedicated anomaly detection scanner. The closest available signals:

| Signal | AlphaMeta Command |
|---|---|
| Market-level strength signals | `advice` (VWAP distances, EMA crossovers) |
| Capital flow intensity | `capital-flow <symbol>` (MFI, net flow direction) |
| Price and volume | `kline <symbol> day 20` (compare recent bars for volume spikes) |
| Quote & price check | `quote <symbol>` |
| News catalyst | `news <symbol>` |

## Single-Symbol Workflow

1. Identify the symbol or market to scan.
2. Use `advice` for broad market signals, `capital-flow` for flow anomalies.
3. Compare recent kline volume against historical average as a simple volume anomaly check:
   - Run `kline <symbol> day 20`
   - Calculate average volume over 20 days
   - Flag as anomaly if today's volume > 2x the 20-day average
4. Check `news <symbol>` for potential catalysts (earnings, M&A, regulatory).

---

## Market-wide Anomaly Scan / 全市场异动扫描

When the user asks **"任何异动"**, **"unusual activity today"**, **"abnormal volume"**, or **"有什么不正常的"**, use WebSearch to discover anomalies across markets, then verify with AlphaMeta.

### Step 1 — Identify Anomaly Type

Clarify what kind of anomaly the user is looking for:

| Anomaly Type | Description | Typical WebSearch Query |
|---|---|---|
| 📊 成交量异常 Volume Spike | Volume > 3x average, no obvious reason | `"unusual stock market activity today"` or `"stocks with unusual volume today"` |
| 💰 价格跳空 Price Gap | Significant gap open (>3%) | `"stocks with large gap today"` |
| 🎯 期权异动 Unusual Options Flow | Abnormal options volume, large blocks | `"unusual options activity today"` or `"abnormal options flow today"` |
| 📰 新闻驱动 News-Driven Gap | Pre-market gap on news/catalyst | `"stocks moving on news today"` |
| 📉 板块异动 Sector-wide Move | Entire sector moving abnormally | `"sector unusual movement today"` |
| 🔥 做空挤压 Short Squeeze | High short interest + price spike | `"short squeeze candidates today"` |

### Step 2 — WebSearch Discovery

Run targeted WebSearch queries based on the anomaly type:

**Volume & Price Anomalies:**

```
"unusual stock market activity today"
"stocks with unusual volume today"
"biggest stock gaps today"
"stocks with unusual price movement today"
```

**Options Flow Anomalies:**

```
"unusual options activity today"
"abnormal options flow large blocks"
"big options trades today"
```

**News-Driven Anomalies:**

```
"stocks halted or volatile today"
"unusual market activity unusual options activity"
```

### Step 3 — Extract & Categorize Anomalies

From search results, extract potential anomalies and categorize them. **Note the volume window used by each source** (20d vs 50d vs "avg") — wider windows produce higher "anomaly" ratios for volatile stocks.

**Important distinction:** Options flow anomalies (high V/OI ratio on option contracts) and share volume anomalies (high share trading volume) are **independent dimensions**. A stock can have:
- Share volume spike ✅ + Options flow spike ✅ → Strong conviction signal
- Share volume spike ✅ + Options flow normal → Retail/sentiment driven
- Share volume normal + Options flow spike ✅ → Institutional positioning/hedging

Attach the correct anomaly type tag to each candidate:

```
Potential Anomalies Detected (WebSearch):
1. GME — Volume 5x avg, +15%, no clear catalyst  →  Volume Spike
2. NVDA — Options flow $200M OTM calls            →  Unusual Options
3. XYZ — Gap +8% open, pre-market halt            →  Price Gap
4. BBBY — +25%, social media buzz, high SI        →  Short Squeeze Candidate
5. SPY — Sector rotation out of energy            →  Sector-wide Move
```

### Step 4 — Verify with AlphaMeta (Phased Execution)

**Critical: separate volume anomalies from options flow anomalies — they use different verification methods.**

#### Phase 1 — Quick Filter (run ALL candidates in parallel)

```text
kline <SYMBOL> day 20    # Check actual share volume vs 20-day avg
quote <SYMBOL>           # Current price, open/close for gap %
```

#### Phase 2 — Confirmation (only for Phase 1 passes)

```text
capital-flow <SYMBOL>    # Check if fund flow confirms the move
news <SYMBOL>            # Check for catalyst (earnings, M&A, regulatory)
advice                   # Broader market context
```

#### Verification by Anomaly Type

**Share Volume Spike** — use `kline day 20`:
- Extract `volume` from each bar
- Compute `avg_volume_20d = sum(volumes) / 20`
- If `latest_volume > 2 * avg_volume_20d` → **Confirmed Volume Anomaly** ⚠️
- If `latest_volume > 3 * avg_volume_20d` → **Strong Volume Anomaly** 🚨
- ⚠️ WebSearch sources may use 50-day avg (not 20-day). If kline shows <2x but WebSearch claimed >5x, the window mismatch is likely the cause. Note: "WebSearch uses 50d avg; AlphaMeta 20d avg shows X ratio."

**Price Gap** — use `quote`:
- `gap_pct = (quote.open - quote.close_prev) / quote.close_prev`
- If `|gap_pct| > 3%` → **Confirmed Price Gap** ⚠️
- Compare with typical ATR for context

**Options Flow Anomaly** — this is a **separate dimension** from share volume:
- AlphaMeta cannot directly verify options flow. The WebSearch is the primary source.
- Do NOT run kline volume check for this type — options volume ≠ share volume
- Verify the underlying stock's price action: `kline <SYMBOL> day 5` + `quote <SYMBOL>`
- If stock price confirms the options signal direction → higher confidence
- Example: MSFT had V/OI 78 on puts ($584K premium). Share volume was normal (1.2x), but stock was +3.0%. This suggests the put buying may be hedging, not directional.

### Step 5 — Output Anomaly Table

| Symbol | Anomaly Type | Signal | Volume vs Avg | Price Δ | Flow | Catalyst |
|--------|-------------|--------|--------------|---------|------|----------|
| GME | 📊 Volume Spike | 5.2x avg | 52.3M (avg: 10.1M) | +15.2% | +$45M | Social media buzz |
| NVDA | 🎯 Options Flow | $200M OTM calls | 1.8x avg | +3.5% | +$280M | AI conference |
| XYZ | 💰 Price Gap | +8.2% gap open | 3.1x avg | +8.2% | +$12M | Takeover rumor |
| BBBY | 🔥 Short Squeeze | SI: 45%, +25% | 8.5x avg | +25.1% | +$85M | Retail frenzy |

Add a **confidence rating** for each anomaly:
- ✅ **Confirmed** — Both WebSearch and AlphaMeta agree (volume + flow both confirm)
- ⚠️ **Plausible** — One source shows signal, AlphaMeta partially confirms
- ❓ **Unverified** — WebSearch only, AlphaMeta data unavailable

### Step 6 — Provide Context & Actionable Insight

For each confirmed anomaly, add a brief assessment:

```
🚨 GME: Volume spike confirmed (5.2x avg). No fundamental catalyst found.
  → Likely retail/social media driven. Caution advised.
  
🎯 NVDA: $200M in OTM call options, AI conference catalyst.
  → Bullish institutional positioning. Monitor for continuation.
  
💰 XYZ: Gap +8% on takeover rumor. News unconfirmed.
  → Speculative. Wait for official announcement before acting.
```

---

## WebSearch Fallback / WebSearch 兜底

| Situation | Response |
|---|---|
| WebSearch returns no anomalies | "No unusual activity detected across major sources. Market appears orderly today." |
| WebSearch yields too many results | Filter to top 5 most significant (largest % change, highest volume ratio) |
| WebSearch data conflicts with AlphaMeta | Prefer AlphaMeta for price/volume; note discrepancy |
| User wants real-time anomaly alerts | "AlphaMeta does not support real-time anomaly alerts. For live monitoring, consider dedicated tools (Unusual Whales, Barchart, or Bloomberg)." |
| AlphaMeta kline volume data is stale | Use WebSearch volume data as reference; add freshness note |

## Errors / 错误处理

| Situation | Response |
|---|---|
| No anomaly type specified | Default to volume spike scan; ask for preference |
| `kline` volume data incomplete | Use WebSearch for volume comparison; note "volume data approximate" |
| `capital-flow` fails | Skip flow confirmation; rely on volume + price signals |
| `advice` shows no market-level signals | Anomaly may be stock-specific; proceed with individual checks |
| WebSearch volume anomaly >5x but kline shows <2x | Likely window mismatch (WebSearch uses 50d avg, AlphaMeta uses 20d avg). Note: "window difference" and present both ratios |
| WebSearch price change differs from kline close change >10% | Trust AlphaMeta kline; WebSearch data may be intraday vs daily close mismatch |
| Options flow detected but stock volume is normal | This is expected — options volume ≠ share volume. Verify stock price action instead. |
| Server not running | "AlphaMeta server offline. Anomaly detection limited to WebSearch data only." |
| All anomalies are unconfirmed | Report as "potential anomalies requiring further investigation" |
| User wants to monitor a specific anomaly | Suggest setting up alerts via [alphameta-predicate](../../alphameta-predicate) for price/volume triggers |
