#!/usr/bin/env python3
"""collect.py — Parallel morning-brief data collector for AlphaMeta API.

Fetches watchlist symbols (via qlist), index klines, watchlist klines,
batch quotes, calendar events, and optional capital-flow / news in parallel.
Outputs a compact structured digest (~3-5K tokens) for LLM consumption.

Usage:
    python3 collect.py                                        # Watchlist from qlist
    python3 collect.py --symbols AAPL,MSFT,NVDA               # Override watchlist
    python3 collect.py --news                                 # Include news fetching
    python3 collect.py --capital-flow                         # Include index capital flow
    python3 collect.py --health                               # Check server only
    python3 collect.py --help

Dependencies: Python stdlib only (urllib, json, threading, concurrent.futures,
              os, sys, datetime).
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta, date
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ── Constants ──

ALPHAMETA_BASE = os.environ.get("ALPHAMETA_URL", "http://localhost:18080")
EXECUTE_URL = "{}/api/v1/execute".format(ALPHAMETA_BASE)
HEALTH_URL = "{}/api/v1/health".format(ALPHAMETA_BASE)
TIMEOUT = 30
CST_TZ = timezone(timedelta(hours=8))

# Standard market indices used in the morning brief
INDEX_DEFS = [
    ("spx",  "I:SPX",  "S&P 500"),
    ("comp", "I:COMP", "Nasdaq Composite"),
    ("indu", "I:INDU", "Dow Jones"),
    ("vix",  "I:VIX",  "CBOE Volatility Index"),
]

# ── Helpers ──


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def now_cst():
    return datetime.now(CST_TZ).strftime("%Y-%m-%d %H:%M CST")


def today_str():
    return date.today().isoformat()


def compute_kline_dates():
    """Return (start_date, end_date) per morning-brief.md: start=today-5, end=today+1."""
    today = date.today()
    start = (today - timedelta(days=5)).isoformat()
    end = (today + timedelta(days=1)).isoformat()
    return start, end


# ── Numeric precision reducer ──


def slim(obj, depth=0, max_depth=5):
    if depth > max_depth:
        return obj
    if isinstance(obj, float):
        if obj == 0.0:
            return 0.0
        if abs(obj) >= 1000:
            return round(obj, 2)
        elif abs(obj) >= 1:
            return round(obj, 2)
        else:
            return round(obj, 4)
    if isinstance(obj, (int, str, bool)) or obj is None:
        return obj
    if isinstance(obj, list):
        return [slim(item, depth + 1, max_depth) for item in obj]
    if isinstance(obj, dict):
        return {k: slim(v, depth + 1, max_depth) for k, v in obj.items()}
    return obj


# ── HTTP helpers (urllib only, no subprocess) ──


def _http_request(method, url, data=None):
    req = Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"success": False, "error": {"code": str(e.code), "message": body}}
    except URLError as e:
        return {"success": False, "error": {"code": "CONNECTION_ERROR",
                                             "message": str(e.reason)}}
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return {"success": False, "error": {"code": "ERROR", "message": str(e)}}


def http_post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    return _http_request("POST", url, data)


def http_get(url):
    return _http_request("GET", url)


# ── Per-source fetcher ──


def fetch_source(name, cmd, raw_dir, retries=1):
    for attempt in range(retries + 1):
        resp = http_post(EXECUTE_URL, {"cmd": cmd})
        if resp.get("success"):
            break
        if attempt < retries:
            time.sleep(1)
    else:
        error_msg = resp.get("error", {}).get("message", "Unknown error")
        try:
            path = os.path.join(raw_dir, "{}.err".format(name))
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(error_msg))
        except (OSError, IOError):
            pass
        return {"ok": False, "error": str(error_msg)}

    result = resp.get("result")
    try:
        path = os.path.join(raw_dir, "{}.json".format(name))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except (OSError, IOError) as e:
        eprint("Warning: could not save {}.json: {}".format(name, e))
    return {"ok": True, "data": result}


# ── Watchlist helpers ──


def fetch_watchlist():
    """Fetch watchlist symbols from qlist.

    Calls POST /api/v1/execute with {"cmd": "qlist"}.
    Returns a list of symbol strings from all watchlist groups
    (excluding system auto-generated client-{id} groups).
    Returns None if qlist fails or returns empty.
    """
    resp = http_post(EXECUTE_URL, {"cmd": "qlist"})
    if not resp.get("success"):
        eprint("Warning: qlist failed: {}".format(
            resp.get("error", {}).get("message", "unknown")))
        return None

    result = resp.get("result", {})
    groups = result.get("groups") if isinstance(result, dict) else None
    if not groups or not isinstance(groups, dict):
        return None

    symbols = []
    for group_name, group_data in groups.items():
        if group_name.startswith("client-"):
            continue
        if isinstance(group_data, dict):
            syms = group_data.get("symbols", [])
            if isinstance(syms, list):
                for s in syms:
                    if isinstance(s, str) and s.strip():
                        symbols.append(s.strip().upper())
    return symbols if symbols else None


def extract_symbols_from_arg(arg):
    return [s.strip().upper() for s in arg.split(",") if s.strip()]


# ── Data extraction helpers ──


def _extract_list(data, *keys):
    if data is None:
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in keys:
            val = data.get(key)
            if isinstance(val, list):
                return val
        for val in data.values():
            if isinstance(val, list):
                return val
    return None


def extract_kline_bars(data):
    items = _extract_list(data, "list", "klines", "items", "candles", "candlesticks")
    if not items:
        return None
    if isinstance(items, dict):
        items = list(items.values())
    bars = []
    for item in items:
        if isinstance(item, dict):
            bar = {
                "date": (item.get("date") or item.get("timestamp")
                         or item.get("t") or ""),
                "close": (item.get("close") or item.get("c")),
                "open": (item.get("open") or item.get("o")),
                "high": (item.get("high") or item.get("h")),
                "low": (item.get("low") or item.get("l")),
                "volume": (item.get("volume") or item.get("v")),
            }
            bar = {k: v for k, v in bar.items() if v is not None}
            if bar.get("close") is not None:
                bars.append(bar)
    return bars if bars else None


# ── Trim functions ──


def trim_kline(data):
    bars = extract_kline_bars(data)
    if not bars:
        return None

    result_bars = []
    for i, bar in enumerate(bars):
        trimmed = {
            "date": bar.get("date", ""),
            "close": bar["close"],
        }
        if i > 0:
            prev_close = bars[i - 1].get("close")
            if prev_close and prev_close != 0:
                trimmed["change_pct"] = round(
                    (bar["close"] - prev_close) / prev_close * 100, 2)
        if bar.get("volume") is not None:
            trimmed["volume"] = bar["volume"]
        result_bars.append(trimmed)

    result = {"bars": result_bars[-5:]}

    if "total_bars" not in data:
        highs = [b.get("high") for b in bars if b.get("high") is not None]
        lows = [b.get("low") for b in bars if b.get("low") is not None]
        if highs and lows:
            result["250d_high"] = max(highs)
            result["250d_low"] = min(lows)

    return slim(result)


def trim_quote_batch(data):
    """Return dict of {symbol: {last, close, change_pct, volume}}.

    Handles both dict-per-symbol and list-of-quotes response formats.
    """
    if not data:
        return None

    result = {}

    if isinstance(data, dict):
        for sym, q in data.items():
            if isinstance(q, dict):
                trimmed = _trim_single_quote(q)
                if trimmed:
                    result[sym] = trimmed
        if result:
            return result

    items = _extract_list(data, "list", "quotes", "items", "results")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                sym = (item.get("symbol") or item.get("ticker")
                       or item.get("code") or "").upper()
                trimmed = _trim_single_quote(item)
                if sym and trimmed:
                    result[sym] = trimmed
        if result:
            return result

    # Fallback: return slimmed data
    return slim(data)


def _trim_single_quote(q):
    trimmed = {}
    for k in ("last", "close", "open", "high", "low", "volume",
              "change", "change_pct", "change_percent"):
        if k in q and q[k] is not None:
            trimmed[k] = q[k]
    if trimmed.get("last") is not None and trimmed.get("change") is None:
        close = trimmed.get("close")
        if close is not None and close != 0:
            trimmed["change_pct"] = round(
                (trimmed["last"] - close) / close * 100, 2)
    return trimmed if trimmed else None


def trim_trading_cal(data):
    if not data:
        return None
    result = {}
    days = _extract_list(data, "trading_days", "days", "list", "calendar")
    if isinstance(days, list):
        result["trading_days"] = days
        today = date.today()
        past_days = [d for d in days if isinstance(d, str) and d < today_str()]
        if past_days:
            result["last_rth_date"] = max(past_days)
        return result

    if isinstance(data, dict):
        return slim(data)

    return slim(data)


def trim_calendar(data):
    if not data:
        return None
    items = _extract_list(data, "list", "events", "items", "calendar")
    if not items:
        return slim(data)

    trimmed = []
    for item in items:
        if isinstance(item, dict):
            entry = {}
            for k in ("symbol", "date", "time", "event", "event_type",
                       "description", "importance", "previous", "estimate",
                       "consensus", "forecast", "actual"):
                if k in item and item[k] is not None:
                    entry[k] = item[k]
            if entry:
                trimmed.append(entry)
    return trimmed if trimmed else slim(items[:20])


def trim_capflow(data):
    if not data:
        return None
    result = {}
    for k in ("symbol", "flow_direction", "source", "as_of"):
        if k in data and data[k] is not None:
            result[k] = data[k]
    summary = data.get("summary")
    if isinstance(summary, dict):
        result["summary"] = {
            k: summary[k] for k in ("total_inflow", "total_outflow", "net_flow",
                                    "money_flow_index", "inflow_bar_pct")
            if k in summary and summary[k] is not None
        }
    bar_stats = data.get("bar_stats")
    if isinstance(bar_stats, dict):
        result["bar_stats"] = {k: bar_stats[k] for k in ("total_bars", "inflow_bars", "outflow_bars")
                               if k in bar_stats and bar_stats[k] is not None}
    return slim(result) if result else None


def trim_news(data):
    items = _extract_list(data, "list", "news", "items", "articles")
    if not items:
        return None
    trimmed = []
    for item in items[:5]:
        if isinstance(item, dict):
            entry = {}
            for k in ("title", "publisher", "published_at", "date",
                       "source", "summary", "url", "description"):
                if k in item and item[k] is not None:
                    entry[k] = item[k]
            if entry:
                trimmed.append(entry)
    return trimmed if trimmed else slim(items[:5])


# ── Job builder ──


def build_jobs(symbols, start_date, end_date, include_news, include_capflow):
    """Build complete job list for parallel execution.

    Each job is (name, cmd_string, group_name, trim_fn).

    group_name determines which output section the result belongs to.
    Multiple jobs with the same group_name get merged in the output.
    """
    jobs = []

    # 1. Calendar events (fixed, no symbol dependency)
    jobs.append(("trading_cal", "calendar trading",
                 "trading_cal", trim_trading_cal))
    jobs.append(("cal_earnings", "calendar earnings",
                 "cal_earnings", trim_calendar))
    jobs.append(("cal_econ", "calendar econ high",
                 "cal_econ", trim_calendar))
    jobs.append(("cal_ipo", "calendar ipo",
                 "cal_ipo", trim_calendar))

    # 2. Index klines (fixed 4)
    for name, idx_code, _label in INDEX_DEFS:
        cmd = "kline {} {} {} day".format(idx_code, start_date, end_date)
        jobs.append(("idx_{}".format(name), cmd, "index_klines", trim_kline))

    # 3. Per-watchlist symbol klines (adjusted)
    for sym in symbols:
        cmd = "kline {} {} {} day adj".format(sym, start_date, end_date)
        jobs.append(("kline_{}".format(sym.lower()), cmd,
                     "watchlist_klines", trim_kline))

    # 4. Batch quote (one call for all symbols)
    if symbols:
        cmd = "quote {}".format(" ".join(symbols))
        jobs.append(("quotes", cmd, "quotes", trim_quote_batch))

    # 5. Capital flow per watchlist symbol (optional)
    if include_capflow:
        for sym in symbols:
            cmd = "capital-flow {}".format(sym)
            jobs.append(("cap_{}".format(sym.lower()), cmd, "capital_flow", trim_capflow))

    # 6. News per watchlist symbol (optional)
    if include_news:
        for sym in symbols:
            cmd = "news {}".format(sym)
            jobs.append(("news_{}".format(sym.lower()), cmd, "news", trim_news))

    return jobs


# ── Output helpers ──


SECTION_DISPLAY = {
    "trading_cal":     "Trading Calendar",
    "cal_earnings":    "Calendar - Earnings",
    "cal_econ":        "Calendar - Economic",
    "cal_ipo":         "Calendar - IPO",
    "index_klines":    "Index Klines",
    "watchlist_klines": "Watchlist Klines (adj)",
    "quotes":          "Watchlist Quotes",
    "capital_flow":    "Capital Flow",
    "news":            "News",
}

MERGE_GROUPS = {"index_klines", "watchlist_klines", "capital_flow", "news"}


def print_section(title, data):
    print("\n===== {} =====".format(title))
    if data is None:
        print("N/A (no data)")
    elif isinstance(data, str):
        print(data)
    else:
        print(json.dumps(data, ensure_ascii=False, default=str))


# ── Core collector ──


def collect(symbols, start_date, end_date, include_news, include_capflow):
    """Collect all morning-brief data sources in parallel. Prints digest to stdout.

    Args:
        symbols: List of watchlist symbol strings.
        start_date: Kline start date (YYYY-MM-DD).
        end_date: Kline end date (YYYY-MM-DD).
        include_news: Whether to fetch news for each symbol.
        include_capflow: Whether to fetch capital flow per watchlist symbol.

    Returns:
        0 on success, 1 on critical failure.
    """
    if not symbols:
        eprint("Error: no symbols to fetch data for")
        return 1

    safe_ts = today_str().replace("-", "")
    raw_dir = "/tmp/am_morning_brief_{}".format(safe_ts)
    try:
        os.makedirs(raw_dir, exist_ok=True)
    except OSError:
        pass

    jobs = build_jobs(symbols, start_date, end_date,
                      include_news, include_capflow)

    if not jobs:
        eprint("Error: no jobs to execute")
        return 1

    results = {}

    eprint("Fetching {} data sources for {} watchlist symbols ...".format(
        len(jobs), len(symbols)))
    max_workers = min(len(jobs), 20)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        fut_map = {}
        for name, cmd, _group, _trim_fn in jobs:
            fut = pool.submit(fetch_source, name, cmd, raw_dir)
            fut_map[fut] = name

        for fut in as_completed(fut_map):
            jname = fut_map[fut]
            try:
                results[jname] = fut.result()
            except Exception as e:
                results[jname] = {"ok": False, "error": str(e)}

    print("MORNING_BRIEF: \u6668\u4f1a\u7eaa\u8981")
    print("COLLECTED_AT: {}".format(now_cst()))
    print("RAW_DIR: {}".format(raw_dir))
    print("  (raw JSON files stored here)")
    print("WATCHLIST_COUNT: {}".format(len(symbols)))
    print("KLINE_RANGE: {} to {}".format(start_date, end_date))

    print("\n===== Watchlist =====")
    print(json.dumps(symbols, ensure_ascii=False))

    for group in ("trading_cal", "cal_earnings", "cal_econ", "cal_ipo", "quotes"):
        _print_group(results, jobs, group)

    _print_merged_group(results, jobs, "index_klines", INDEX_DEFS)
    _print_merged_group_by_symbol(results, jobs, "watchlist_klines", symbols)

    if include_capflow:
        _print_merged_group_by_symbol(results, jobs, "capital_flow", symbols)

    if include_news:
        _print_merged_group_by_symbol(results, jobs, "news", symbols)

    print()
    return 0


def _print_group(results, jobs, group_name):
    for name, _cmd, grp, trim_fn in jobs:
        if grp != group_name:
            continue
        result = results.get(name, {"ok": False, "error": "not fetched"})
        display = SECTION_DISPLAY.get(grp, grp)
        if result["ok"]:
            data = result["data"]
            if trim_fn is not None:
                data = trim_fn(data)
            else:
                data = slim(data)
            print_section(display, data)
        else:
            print_section(display, "N/A ({})".format(result["error"]))
        break


def _print_merged_group(results, jobs, group_name, defs):
    merged = {}
    has_data = False
    for short_name, _idx_code, _label in defs:
        job_name = "{}_{}".format(
            "idx" if group_name == "index_klines" else "cap",
            short_name)
        result = results.get(job_name, {"ok": False})
        if result.get("ok"):
            trim_fn = None
            for _n, _c, grp, fn in jobs:
                if grp == group_name and fn is not None:
                    trim_fn = fn
                    break
            data = result["data"]
            if trim_fn is not None:
                data = trim_fn(data)
            else:
                data = slim(data)
            merged[_label] = data if data is not None else "N/A"
            if data is not None:
                has_data = True
        else:
            merged[_label] = "N/A"
    display = SECTION_DISPLAY.get(group_name, group_name)
    if has_data:
        print_section(display, merged)
    else:
        print_section(display, "N/A (all indices failed)")


def _print_merged_group_by_symbol(results, jobs, group_name, symbols):
    prefix_map = {
        "watchlist_klines": "kline",
        "capital_flow": "cap",
        "news": "news",
    }
    prefix = prefix_map.get(group_name, group_name)

    merged = {}
    has_data = False
    for sym in symbols:
        job_name = "{}_{}".format(prefix, sym.lower())
        result = results.get(job_name, {"ok": False})
        if result.get("ok"):
            trim_fn = None
            for _n, _c, grp, fn in jobs:
                if grp == group_name and fn is not None:
                    trim_fn = fn
                    break
            data = result["data"]
            if trim_fn is not None:
                data = trim_fn(data)
            else:
                data = slim(data)
            if data is not None:
                merged[sym] = data
                has_data = True
    display = SECTION_DISPLAY.get(group_name, group_name)
    if has_data:
        print_section(display, merged)
    else:
        print_section(display, "N/A (no data)")


# ── Health check ──


def health_check():
    eprint("Checking AlphaMeta server at {} ...".format(HEALTH_URL))
    result = http_get(HEALTH_URL)
    status = result.get("status", "unknown")
    if status == "ok":
        ib = result.get("ib_connected", "?")
        acct = result.get("account_id", "?")
        eprint("OK   server: running")
        eprint("     IBKR connected: {}".format(ib))
        eprint("     account: {}".format(acct))
        return True
    else:
        eprint("FAIL server status: {} ({})".format(
            status, result.get("message", "no details")))
        return False


def print_usage():
    print("""Usage: python3 collect.py [options]

Parallel morning-brief data collector for AlphaMeta API.
Fetches watchlist symbols, index klines, watchlist klines,
batch quotes, calendar events, and optional data in parallel.
Outputs a compact structured digest to stdout (consumed by LLM).

Options:
  --symbols AAPL,MSFT    Comma-separated watchlist override (skip qlist)
  --news                 Include news fetching per watchlist symbol
  --capital-flow         Include capital flow data per watchlist symbol
  --health               Check AlphaMeta server health only, then exit
  --help                 Show this help message and exit

Examples:
  python3 collect.py
  python3 collect.py --symbols AAPL,MSFT,NVDA,TSLA
  python3 collect.py --news --capital-flow
  python3 collect.py --health

Environment:
  ALPHAMETA_URL     AlphaMeta server base URL (default: http://localhost:18080)
""")


def main():
    args = [a for a in sys.argv[1:] if a]

    if "--help" in args or "-h" in args:
        print_usage()
        return

    if "--health" in args:
        health_check()
        return

    include_news = "--news" in args
    include_capflow = "--capital-flow" in args

    symbols_override = None
    for i, a in enumerate(args):
        if a == "--symbols" and i + 1 < len(args):
            symbols_override = extract_symbols_from_arg(args[i + 1])
            break

    if symbols_override:
        symbols = symbols_override
        eprint("Using --symbols override: {} symbols".format(len(symbols)))
    else:
        eprint("Fetching watchlist from qlist ...")
        symbols = fetch_watchlist()
        if not symbols:
            eprint("Warning: qlist returned no symbols. "
                   "Use --symbols to provide a watchlist.")
            eprint("Collecting index & calendar data only.")
            symbols = []

    if not symbols:
        eprint("Proceeding with index & calendar data only (no watchlist).")

    if not health_check():
        eprint("")
        eprint("Error: AlphaMeta server is not reachable.")
        eprint("Start it with: alphameta --ibkr")
        sys.exit(1)

    start_date, end_date = compute_kline_dates()
    eprint("Kline range: {} to {}".format(start_date, end_date))
    eprint("")

    sys.exit(collect(symbols, start_date, end_date,
                     include_news, include_capflow))


if __name__ == "__main__":
    main()
