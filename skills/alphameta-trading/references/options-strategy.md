# Options Strategy

Recommend and explain options strategies based on the user's market view (bullish/bearish/neutral) and current IV environment — grounded in live IBKR data via AlphaMeta.

> **Response language**: match the user's input language — Simplified Chinese / Traditional Chinese / English.

## When to Use

- "我看涨 NVDA，想用期权放大收益，有什么策略？" / "I'm bullish on NVDA, what option strategy fits?"
- "TSLA 财报前波动率很高，我该怎么操作？" / "TSLA IV is high before earnings, what should I do?"
- "我持有 AAPL，想买个保险" / "I hold AAPL and want downside protection"
- "跨式和宽跨式有什么区别？" / "Straddle vs strangle — which is better and when?"
- "SPY 现在是该卖波动率还是买波动率？" / "Should I be short or long vol on SPY right now?"
- "帮我看看这个期权组合的风险收益" / "Analyze this options combo for me"

For execution (placing the actual order) use this skill's order placement. For P&L/Greeks analysis of existing positions route to `alphameta-technical`.

## Workflow

1. **Clarify** the user's market view (direction + conviction), time horizon, and whether they want income, protection, or speculation.
2. **Fetch live data** via AlphaMeta:
   - `quote <SYMBOL>` — spot price, IV, HV
   - `chain <SYMBOL>` — available expiry dates
   - `chain <SYMBOL> <MM-DD>` — strikes and OCC symbols for nearest expiry
   - `info <OCC>` — IV, Greeks, premium for specific contracts
   - `maxpain <SYMBOL> <MM-DD>` — max pain strike for additional context
   - `align <SYMBOL> [width]` — batch add ATM straddle/strangle/spread quotes
   - `straddle <SYMBOL> <widths...>` — generate ATM straddle, strangle, iron condor, vertical spread quotes (fastest way to evaluate multi-leg combo bids/asks)
3. **Assess IV environment**: compare ATM IV from chain vs HV (from `quote`). IV/HV > 1.3 → rich, < 0.8 → cheap.
4. **Select 1-2 strategies** from the strategy matrix; determine approximate strikes (e.g., ATM, ±$5 wide).
5. **Verify prices before showing legs**:
   - Run `add <short_leg_OCC> <long_leg_OCC>` to subscribe to the candidate contracts
   - Run `info <OCC>` or `quote <OCC>` to get real bid/ask prices
   - Confirm the net credit/debit makes sense for the strategy (e.g., Bull Put Spread must net a credit)
   - If the spread is too narrow (bid/ask too wide) or net price is adverse, adjust strikes and re-verify
   - **Never estimate prices from IV alone** — real bid/ask can differ from theoretical price by 20%+
6. **Output** structured recommendation with REAL verified prices (template below).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll skip fetching IV data, the strategy matrix doesn't need it" | IV level determines whether to buy or sell premium. Without it, you'll recommend the wrong strategy. Always assess IV/HV ratio. |
| "I'll just use the first expiry I find" | Strategy choice depends on time horizon. Match expiry to the user's expected move timeline. |
| "I don't need to verify the OCC symbol exists" | Always run `chain <SYMBOL> <MM-DD>` to confirm the strike is liquid before showing example legs. |
| "I can estimate the option price from IV and skip add/info" | IV gives a theoretical mid price, NOT real bid/ask. Without `add` + `info`, you'll quote prices that don't exist. The market's bid/ask spread can change the net credit by 20-50%. Always verify. |
| "maxpain is irrelevant for directional strategies" | Max pain is a magnet at expiry — it affects short-term positioning even for directional plays. |
| "I'll recommend a strategy without clarifying direction or risk tolerance" | Never guess. A covered call and a long call serve very different purposes. Clarify first. |

## Red Flags

- User says "I don't know my market view" — they are not ready for options. Guide them to `alphameta-market-data` and `alphameta-technical` for market context first.
- IV/HV ratio is missing from the recommendation — incomplete analysis. Always compute it.
- Recommending short options (naked calls/puts) without warning about unlimited risk — must flag.
- Using IV from a single OTM strike instead of ATM — ATM IV is the standard reference.
- No clear recommendation tie-breaker when multiple strategies fit — present top 2 with trade-offs.
- Recommending specific option legs without running `add` + `info` to verify actual bid/ask prices — estimated prices can differ from real quotes by 20%+, leading to wrong net credit/debit calculations.

## Strategy Matrix

| Market view | IV level | Recommended strategy | Risk profile |
|---|---|---|---|
| Bullish | Any | Long call / bull call spread | Limited loss, capped or unlimited gain |
| Bullish | Any | **Short put / Cash-secured put** | **Collect premium, obligated to buy stock at strike** |
| Bullish | Rich | Bull put spread / Short put spread | Collect premium, limited risk |
| Bearish | Any | Long put / bear put spread | Limited loss, capped or large gain |
| Bearish | Rich | Bear call spread / Short call spread | Collect premium, limited risk |
| Neutral (range-bound) | Rich | Short strangle / short straddle | Collect premium, unlimited risk |
| Neutral (range-bound) | Rich | Iron condor | Collect premium, defined risk both sides |
| Neutral (vol expansion) | Cheap | Long straddle / long strangle | Pay premium, profit from large move |
| Income on holding | Any | Covered call | Reduce cost basis, cap upside |
| Downside protection | Any | Protective put | Insurance premium, preserve upside |
| Directional with precision | Any | Call/Put butterfly | Fixed risk, defined range, lower cost |
| Hold stock, cheap protection | Any | Collar | Premium collected or small cost, defined range |
| Neutral (time decay) | Rich near / fair far | Calendar spread | Limited loss, profit from time decay differential |
| Directional, longer time | Any | Diagonal spread | Defined risk, leveraged directional exposure |
| Strong directional | Any | Risk reversal | Synthetic position, defined or unlimited risk |
| Strong directional, lower cost | Any | Call/Put ratio spread / backspread | Defined risk, non-linear payoff |

## Output

Present results in markdown-native format with a structured recommendation.

### Strategy Recommendation Template

```
{Symbol} options strategy recommendation — Source: AlphaMeta / IBKR

[Market context]
- Spot: ${S}  |  Nearest expiry: {date}  |  ATM IV: ~X%
- HV20: X%  |  IV/HV ratio: {X} → {rich / fair / cheap}
- Max pain: ${X}  |  GEX: {bullish / bearish / neutral}

[Recommended strategy: {Name}]
Structure:
  Leg 1: {Buy/Sell} {N} {OCC} @ ${prem} (IV: X%)
  Leg 2: {Buy/Sell} {N} {OCC} @ ${prem} (IV: X%)

Key metrics:
  Net {debit/credit}: ${X}
  Max profit: ${X} (at S {condition})
  Max loss:   ${X} (at S {condition})
  Breakeven:  ${X}
  Theta:      ${X}/day
  Vega:       ${X}/1% IV change

Why this fits: {2-sentence rationale linking market view + IV + time horizon}

Risk note: {key risk of this strategy}

[Alternative: {Name}]
{Brief description, key trade-offs vs primary recommendation}

[How to execute]
Use this skill (alphameta-trading) with the legs above, or use /alphameta-trading for natural-language order placement.

⚠️ 以上分析仅供参考，不构成投资建议。For reference only. Not investment advice.
```

### Strategy Quick-Reference Table

| Strategy | When | Structure | Max Loss | Max Profit | Breakeven |
|---|---|---|---|---|---|
| **Short Put / Cash-Secured Put** | Willing to buy stock at lower price | Sell 1 OTM/ATM put + hold cash to cover | Strike − premium (if assigned) | Net premium received | Strike − premium |
| **Covered Call** | Hold stock, mild bullish | Hold 100 shares + Sell 1 OTM call | Stock drop to 0 | Premium + (strike − stock) | Stock price − premium |
| **Protective Put** | Hold stock, fear downside | Hold 100 shares + Buy 1 OTM put | Put premium + (stock − strike) | Unlimited (stock upside) | Stock price + premium |
| **Long Call** | Bullish, defined risk | Buy 1 call | Premium paid | Unlimited | Strike + premium |
| **Long Put** | Bearish, defined risk | Buy 1 put | Premium paid | Strike − premium | Strike − premium |
| **Bull Call Spread** | Bullish, capped gain | Buy low call + Sell high call | Net debit | (High − low) − debit | Low strike + debit |
| **Bear Put Spread** | Bearish, capped gain | Buy high put + Sell low put | Net debit | (High − low) − debit | High strike − debit |
| **Bull Put Spread** | Bullish, collect premium | Sell high put + Buy low put | (High − low) − credit | Net credit | High strike − credit |
| **Bear Call Spread** | Bearish, collect premium | Sell low call + Buy high call | (High − low) − credit | Net credit | Low strike + credit |
| **Long Straddle** | Big move expected | Buy ATM call + Buy ATM put | Combined premium paid | Unlimited (either direction) | Strike ± premium |
| **Long Strangle** | Big move, cheaper | Buy OTM call + Buy OTM put | Combined premium paid | Unlimited (either direction) | Low strike − prem / High strike + prem |
| **Short Straddle** | Range-bound, collect prem | Sell ATM call + Sell ATM put | Unlimited | Net credit received | Strike ± credit |
| **Short Strangle** | Range-bound, wider range | Sell OTM call + Sell OTM put | Unlimited (wider than straddle) | Net credit received | Wide range |
| **Iron Condor** | Range-bound, defined risk | Bear call spread + Bull put spread | Width − net credit | Net credit | Between short strikes |
| **Butterfly** | Pinpoint target | Buy low + Sell 2 mid + Buy high | Net debit | (Mid − low) − debit | At middle strike |
| **Collar** | Hedge stock at low cost | Hold 100 shares + Buy OTM put + Sell OTM call | (Stock − Put strike) + Put premium − Call premium | (Call strike − Stock) − Put premium + Call premium | Stock price + Put premium − Call premium |
| **Calendar Spread** | Time decay, same strike | Sell near-month + Buy far-month (same strike) | Net debit paid | Max at strike at near expiry | Near strike (approx) |
| **Diagonal Spread** | Time decay + direction | Sell near-month + Buy far-month (different strikes) | Net debit paid | Capped or large | Between strikes |
| **Risk Reversal** | Synthetic long / short | Sell OTM put + Buy OTM call (bullish) / Buy OTM put + Sell OTM call (bearish) | Put strike − credit (bullish) | Unlimited (bullish) | Call strike + debit (or − credit) |
| **Ratio Spread** | Reduced cost directional | Buy 1 ATM call + Sell 2 OTM calls | Limited (short strikes width) | Max at short strike | Between strikes |

## Command Index

| Category | Commands | Use For |
|---|---|---|
| Live Quotes | `add`, `quote`, `chain`, `info`, `align`, `straddle`, `range` | Spot price, option chain, IV, Greeks, multi-leg combo bids |
| Technical Indicators | `maxpain`, `gex` | Max pain, gamma exposure analysis |
| Contract Details | `details`, `info` | Contract metadata with Greeks |

For full command reference, see `alphameta-market-data` and `alphameta-technical`.

## Key Concepts

### OCC Symbol Format

```
SYMBOL + YYMMDD + C|P + 8-DIGIT_STRIKE

Example: NVDA260501C00175000
  NVDA    → AAPL
  260501  → May 1, 2026
  C       → Call
  00175000 → $175.00 (price × 1000, 8 digits)
```

**Always run `chain <SYMBOL> <MM-DD>` to discover valid OCC symbols before using them in strategies.**

### IV Environment Assessment

| IV/HV Ratio | Signal | Strategy Bias |
|---|---|---|
| < 0.8 | Cheap IV | Favor buying premium (long options, long straddle/strangle) |
| 0.8 – 1.2 | Fair IV | Neutral — use directional strategies |
| > 1.3 | Rich IV | Favor selling premium (credit spreads, iron condor, covered call) |

### Options Order Routing

For strategy execution, see this skill's multi-leg syntax (references/multi-leg.md):

```bash
# Bull Call Spread
buy "bto 1 <low_call_OCC> sto 1 <high_call_OCC>" <qty> AF @ <net_debit>

# Roll position
buy "btc 1 <old_OCC> sto 1 <new_OCC>" <qty> AF @ -<net_credit>
```

See [multi-leg.md](multi-leg.md) for full syntax.

## Error Handling

| Situation | Reply |
|---|---|
| Service not running (health fails) | Start the service: `alphameta start` |
| `quote` returns no data for symbol | Ask user to verify the ticker symbol |
| `chain` returns empty | No option chain available; stock may not have listed options |
| No liquid options near requested strike | Suggest widening the strike range or using a different expiry |
| User's market view is unclear | Ask clarifying questions: bullish/bearish/neutral? Time horizon? Risk tolerance? |
| IV/Greeks unavailable (market closed) | Use last available snapshot; note that IV may be stale |
