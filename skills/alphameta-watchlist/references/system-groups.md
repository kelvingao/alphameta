# System Groups

Two group types are managed by the system, not created by the user.

## `client-{id}` (e.g. `client-0`, `client-2`) — Auto-generated live quote snapshot

- Created automatically by `qsnapshot` whenever quotes are added/removed (`add`, `remove`, `oadd`, `align`).
- Stores full IBKR Contract objects (not plain symbols) — `{"contracts": [...]}`.
- On startup, AlphaMeta restores from this snapshot first. Only if absent does it fall back to `global` group or built-in defaults (`SPY`, `QQQ`, `AAPL` + futures + indices).
- **Not a user watchlist.** `qadd`/`qremove` edits are overwritten on the next quote change. Do not `qdelete` unless you intend to reset saved state.
- Stored in diskcache under key `("quotes", f"client-{clientId}")`.

## `global` — Shared default fallback group

- Plain symbol-set group (`set("AAPL", "MSFT")`) created via `qsave`/`qadd`.
- Loaded only when no `client-{id}` snapshot exists on startup.
- Legacy fallback mechanism — still works but `client-{id}` takes priority.

## Comparison

| Feature | `client-{id}` | User groups |
|---------|---------------|-------------|
| Created by | `qsnapshot` (auto) | `qadd` / `qsave` (manual) |
| Data format | `{"contracts": [Contract, ...]}` | Plain symbol strings |
| Updated | Every add/remove (auto overwrite) | Only on manual edit |
| Restore priority | 1st (on startup) | N/A (or `global` as 2nd fallback) |

## Relationship to Quote Commands

The q* commands (qlist, qadd, qsave, qremove, qdelete) are the same system used by AlphaMeta's quote stream management. When you `qsave` or `qadd`, you're writing into the same quote-group namespace used by the live quote view. This means a watchlist group is also a "quote group" — it can be loaded into the live stream via `qrestore`.

## Red Flags

- **`client-{id}` groups are not user watchlists** — `qadd`/`qremove` edits will be overwritten. `qdelete` breaks startup auto-restore. Do not manage them manually.
- **`global` is a fallback** — `client-{id}` snapshot takes priority on startup. `global` is only loaded when no snapshot exists.
- **Group name collisions** — if `qadd` target doesn't exist, it creates it. If user said "add to group X" and X doesn't exist, warn them it'll be created.
