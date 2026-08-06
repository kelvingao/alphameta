# Watchlist Group Management

Persistent named groups of securities (stocks, options, futures, indices), stored locally via AlphaMeta's quote group system.

Data lives in local diskcache — no network required for CRUD. Only live quote lookups need a running AlphaMeta service.

## Reading

1. Call `qlist` to get all groups.
2. `qlist` returns `{"groups": {"<name>": {"symbols": [...], "live": [...]}}}`.
   - `symbols`: all symbols saved in the group
   - `live`: subset of symbols currently streaming live quotes
3. Filter by group name (LLM-side) if user asks for a specific group.
4. To batch-check prices, pass symbols to `alphameta-market-data`.

### Output Format

Present watchlist data as markdown tables.

**List All Groups:**
```json
qlist → {"groups": {"tech": {"symbols": ["NVDA","AAPL","MSFT"], "live": ["NVDA","AAPL"]}, ...}}
```

| Group | Symbols | Live |
|-------|---------|:----:|
| **tech** | NVDA, AAPL, MSFT | NVDA ✓, AAPL ✓ |
| **semis** | NVDA, AMD, INTC | NVDA ✓ |

When `live` is non-empty, mark symbols that are actively streaming with a checkmark.

**Single Group Detail:**

| Group: tech | Symbols |
|-------------|---------|
| NVDA | ✓ (live) |
| AAPL | ✓ (live) |
| MSFT | — |

## Writing (one-shot, no two-step protocol)

All mutations are local (diskcache). No remote side effects.

- **Describe** what you are about to do in the user's language.
- **Execute** immediately — no explicit confirmation gate needed.
- **Exception**: for `qdelete` (irreversible), briefly confirm with the user before executing.

| Action | Command | Notes |
|--------|---------|-------|
| Create group + add symbols | `qsave <group> <symbol...>` | If no symbols given, saves currently streaming quotes into the group |
| Add symbols to existing group | `qadd <group> <symbol...>` | Creates group if it doesn't exist |
| Remove specific symbols | `qremove <group> <symbol...>` | Supports glob patterns (`qremove mygroup AAPL*`) |
| Remove all symbols from group | `qremove <group>` | Clears the group but keeps it |
| Delete entire group | `qdelete <group...>` | Can delete multiple at once. **Briefly confirm before executing.** |

### Output Examples

**After Adding Symbols:**
```json
qadd tech GOOGL → {"added": ["GOOGL"], "failed": []}
```
> Added GOOGL to **tech**. ✓ Success.
> *(optional chained query)* → "Would you like to see the current price of GOOGL?"

**After Removing Symbols:**
```json
qremove tech AAPL → null (success)
```
> Removed AAPL from **tech**.

### Common Rationalizations

| Rationalization | Reality |
|----------------|---------|
| "I'll just use the raw JSON output" | The `qlist` response is already structured. Present it as a readable table — group name as header, symbols as a comma-separated list. |
| "I'll rephrase qlist as watchlist since it's what the user understands" | **Correct.** The backend calls them "quote groups"; the skill layer should call them "watchlist groups". Translate terminology for the user. |
| "I need to run two-step confirmation for all mutations" | **Wrong.** These are local writes — no broker state change. Only `qdelete` warrants a quick check. |
| "I'll hardcode `qadd` → `qsave` mapping" | `qadd` appends to an existing group (or creates if missing). `qsave` overwrites. Use `qadd` for "add to", `qsave` for "create new group". |

### Chained Workflows

| User asks | Flow |
|-----------|------|
| "My watchlist stocks' gainers today" | `qlist` → extract symbols → `alphameta-market-data` |
| "Are any of my watchlist options ITM?" | `qlist` → extract symbols → `alphameta-technical` |
| "Check if these positions are in my portfolio" | `qlist` → extract symbols → `alphameta-portfolio` |
| "Save my current quotes as a watchlist group" | `qsave <name>` (no symbols → saves live quotes) |

## Group Semantics

| Concept | Detail |
|---------|--------|
| Group names | Free-form strings (avoid special characters) |
| Symbols | Any valid IBKR symbol: `NVDA`, `AAPL260515P00200000`, `/ESM6`, `I:VIX` |
| Empty groups | Show as `(empty)` in listings |
| Symbol casing | Case-sensitive. `AAPL` and `aapl` are different. |
| `live` field | Subset of symbols that are currently streaming real-time quotes |

## Additional Commands

These q* commands are part of the same quote-group system but used less frequently:

| Command | Description |
|---------|-------------|
| `qsnapshot` | Save current subscriptions (auto-loaded on restart) |
| `qclean <group>` | Remove expired options from a group |
| `qsave <name>` | Persist config to file |
| `qrestore <name>` | Restore config from file |
| `qloadsnapshot` | Load saved contract snapshot |

## Error Handling

| Situation | Reply |
|-----------|-------|
| Service not running | `alphameta start` to start the service |
| `qlist` returns empty groups | "No watchlist groups yet. Create one with `qadd <name> <symbols>`." |
| `qadd` returns `failed: [...]` | "Could not qualify: AAPL. Check symbol spelling." |
| `qdelete` on non-existent group | "Group not found. Run `qlist` to see available groups." |
| `qremove` no matching symbols | "No matching symbols found in that group. Use `qlist <group>` to check contents." |
| Permission error (403) | "This command requires a PRO-tier API key. Set `ALPHAMETA_API_KEY`." |
| Other API error | Surface the error message verbatim. |
