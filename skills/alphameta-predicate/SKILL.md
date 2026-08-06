---
name: alphameta-predicate
description: 'Conditional trigger automation and scheduled tasks via AlphaMeta — if...then... triggers (RSI, EMA crossover, price threshold), scheduled timed tasks, and async task management. Use when: "条件单", "自动化", "触发", "止损", "EMA", "RSI", "定时任务", "schedule", "自动交易", "predicate", "conditional order", "ifthen", "automation", "when price", "auto-stop".'
---

# AlphaMeta Predicate

> **Response language**: match the user's input language (Simplified Chinese / Traditional Chinese / English).

## ⚠️ Critical

> **Conditions do NOT auto-expire**: After triggering, conditions continue monitoring repeatedly. Stop with `ifclear`, `ifrm`, or when funds exhausted.

See the [alphameta](../alphameta) skill for server setup and command execution syntax.

## Command Index

| Category | Commands | Use For |
|---|---|---|
| [Predicate Management](references/ref-predicate.md) | `ifthen`, `iflist`, `ifgroup`, `ifclear`, `ifrm`, `auto` | Conditional triggers |
| [Schedule](references/ref-schedule.md) | `sadd`, `scancel`, `slists` | Timed tasks |
| [Task Management](references/ref-task.md) | `tasklist`, `taskcancel` | Async batch operations |

## Key Concepts

### Predicate DSL

```
ifthen if <symbol> <indicator> <operator> <value>: <action>
```

| Example | Meaning |
|---|---|
| `ifthen if AAPL rsi > 80: sell AAPL 100` | Sell when RSI > 80 |
| `ifthen if NVDA ema crossover up: buy NVDA 50` | Buy on EMA golden cross |
| `ifthen if TSLA price > 250: close TSLA` | Stop profit at $250 |

### Schedule Syntax

```
sched-add <name> <HH:MM> "<command>"
```

> **Time must be in future**
> **Command must use double quotes**
> **Single execution only** (auto-deletes after run)

### Gotchas

- `if` must be **lowercase** (it's part of the DSL syntax)
- Scheduled tasks **do not repeat daily**
- Tasks in memory **disappear after restart**

For full reference, see [references/ref-predicate.md](references/ref-predicate.md), [references/ref-schedule.md](references/ref-schedule.md), and [references/ref-task.md](references/ref-task.md).