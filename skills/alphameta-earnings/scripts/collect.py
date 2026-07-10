#!/usr/bin/env python3
"""collect.py — Parallel earnings-data collector for AlphaMeta API.

Fetches 10 (lite) or 12 (full) data sources in parallel via HTTP POST,
saves raw JSON responses to TMPDIR, and prints a compact digest (~3-4K tokens).

Usage:
    python3 collect.py AAPL
    python3 collect.py AAPL --full
    python3 collect.py --health
    python3 collect.py --help

Dependencies: Python stdlib only (urllib, json, threading, concurrent.futures,
              tempfile, os, sys, datetime).
"""

import json
import os
import re
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ── Constants ──

ALPHAMETA_BASE = os.environ.get("ALPHAMETA_URL", "http://localhost:18080")
EXECUTE_URL = "{}/api/v1/execute".format(ALPHAMETA_BASE)
HEALTH_URL = "{}/api/v1/health".format(ALPHAMETA_BASE)
TIMEOUT = 120
CST_TZ = timezone(timedelta(hours=8))


def eprint(*args, **kwargs):
    """Print to stderr (status messages only — never on stdout)."""
    print(*args, file=sys.stderr, **kwargs)


def now_cst():
    """Current datetime in CST (Asia/Shanghai)."""
    return datetime.now(CST_TZ).strftime("%Y-%m-%d %H:%M CST")



# ── Numeric precision reducer ──


def slim(obj, depth=0, max_depth=5):
    """Reduce numeric precision recursively. Floats → 2-4 decimal places."""
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
    """Make an HTTP request. Returns parsed JSON dict."""
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
    """POST JSON payload. Returns parsed response dict."""
    data = json.dumps(payload).encode("utf-8")
    return _http_request("POST", url, data)


def http_get(url):
    """GET URL. Returns parsed response dict."""
    return _http_request("GET", url)


# ── Per-source fetcher ──


def fetch_source(name, cmd, raw_dir):
    """Fetch one data source, save raw JSON, return {ok, data/error}."""
    resp = http_post(EXECUTE_URL, {"cmd": cmd})
    try:
        os.makedirs(raw_dir, exist_ok=True)
    except OSError:
        pass

    if resp.get("success"):
        result = resp.get("result")
        try:
            path = os.path.join(raw_dir, "{}.json".format(name))
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except (OSError, IOError) as e:
            eprint("Warning: could not save {}.json: {}".format(name, e))
        return {"ok": True, "data": result}
    else:
        error_msg = resp.get("error", {}).get("message", "Unknown error")
        try:
            path = os.path.join(raw_dir, "{}.err".format(name))
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(error_msg))
        except (OSError, IOError):
            pass
        return {"ok": False, "error": str(error_msg)}


# ── Extract list from API response (flexible key paths) ──


def _extract_list(data, *keys):
    """Extract a list from data using multiple possible key paths."""
    if data is None:
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in keys:
            val = data.get(key)
            if isinstance(val, list):
                return val
        # Last resort: first list value found in the dict
        for val in data.values():
            if isinstance(val, list):
                return val
    return None


# ── Trim functions (reduce verbosity while preserving key signals) ──


def trim_filings(data):
    """Keep id, title, type, date for first 5 filings."""
    items = _extract_list(data, "list", "filings", "items")
    if not items:
        return None
    trimmed = []
    for item in items[:5]:
        if isinstance(item, dict):
            entry = {}
            for k in ("id", "title", "type", "date", "filing_date",
                       "form_type", "period_end", "description"):
                if k in item:
                    entry[k] = item[k]
            if entry:
                trimmed.append(entry)
    return trimmed if trimmed else slim(items[:5])


def trim_consensus(data):
    """Keep ratings, price target, current estimates, beat/miss history."""
    if not data:
        return None
    result = {}
    # Ratings
    for k in ("analyst_ratings", "rating_summary", "recommendation"):
        if k in data:
            result[k] = data[k]
            break
    # Price target
    for k in ("price_target", "target_price", "price_targets"):
        if k in data:
            result[k] = data[k]
            break
    # EPS estimates (current 3 periods)
    for k in ("eps_estimates", "estimates", "consensus_estimates",
               "current_estimates", "earnings_estimates"):
        if k in data:
            est = data[k]
            if isinstance(est, list):
                result[k] = slim(est[:3])
            else:
                result[k] = slim(est)
            break
    # Beat/miss history (last 8)
    for k in ("beat_miss_history", "surprise_history", "earnings_surprises"):
        if k in data:
            hist = data[k]
            if isinstance(hist, list):
                result[k] = slim(hist[-8:] if len(hist) > 8 else hist)
            else:
                result[k] = slim(hist)
            break
    # Include key valuation fields
    for k in ("forward_pe", "trailing_pe", "peg_ratio", "market_cap"):
        if k in data:
            result[k] = data[k]
    return slim(result) if result else slim(data)


def trim_news(data):
    """Keep title, publisher, published_at, summary for first 10."""
    items = _extract_list(data, "list", "news", "items", "articles")
    if not items:
        return None
    trimmed = []
    for item in items[:10]:
        if isinstance(item, dict):
            entry = {}
            for k in ("title", "publisher", "published_at", "summary",
                       "date", "source", "url", "description"):
                if k in item:
                    entry[k] = item[k]
            if entry:
                trimmed.append(entry)
    return trimmed if trimmed else slim(items[:10])


def trim_kline(data):
    """Keep last 20 closes (date + close) + 250d high/low summary."""
    items = _extract_list(data, "list", "klines", "items", "candles",
                          "candlesticks")
    if not items:
        return None
    if isinstance(items, dict):
        items = list(items.values())
    highs, lows = [], []
    result = {}
    recent = items[-20:] if len(items) > 20 else items
    result["last_20"] = []
    for item in recent:
        if isinstance(item, dict):
            entry = {
                "date": (item.get("date") or item.get("timestamp")
                         or item.get("t") or ""),
                "close": (item.get("close") or item.get("c")),
                "open": (item.get("open") or item.get("o")),
                "high": (item.get("high") or item.get("h")),
                "low": (item.get("low") or item.get("l")),
                "volume": (item.get("volume") or item.get("v")),
            }
            entry = {k: v for k, v in entry.items() if v is not None}
            result["last_20"].append(entry)
        h = item.get("high") or item.get("h")
        l = item.get("low") or item.get("l")
        if h is not None:
            highs.append(h)
        if l is not None:
            lows.append(l)
    if highs and lows:
        result["250d_high"] = max(highs)
        result["250d_low"] = min(lows)
    result["total_bars"] = len(items)
    return slim(result)


def trim_operating(data):
    """Keep metrics array with period, revenue, netIncome, eps, margins."""
    items = _extract_list(data, "list", "metrics", "items",
                          "operating_metrics", "operating")
    if not items:
        # Try dict-of-periods format
        if isinstance(data, dict):
            items = []
            for k, v in data.items():
                if isinstance(v, dict):
                    v["_period"] = k
                    items.append(v)
        if not items:
            return None
    if isinstance(items, dict):
        items = list(items.values())
    trimmed = []
    for item in items:
        if isinstance(item, dict):
            entry = {}
            for k in ("period", "date", "period_label",
                       "revenue", "netIncome", "net_income",
                       "eps", "diluted_eps", "adjusted_eps",
                       "grossMargin", "gross_margin", "gross_profit",
                       "operatingMargin", "operating_margin",
                       "netMargin", "net_margin",
                       "ebitda", "ebit", "free_cash_flow"):
                v = item.get(k)
                if v is not None:
                    entry[k] = v
            if entry:
                trimmed.append(entry)
    return slim(trimmed) if trimmed else slim(data)


def trim_segment(data):
    """Extract segment breakdown with YoY comparison. Auto-detects SEG format."""
    if not data:
        return None
    segments = data.get("segments")
    periods = data.get("periods", [])
    if not segments:
        return None

    if _is_grouped(segments):
        return _seg_grouped(segments, periods)
    return _seg_flat(segments, periods)


def _is_grouped(segments):
    return any(
        isinstance(v, dict) and any(isinstance(sv, dict) for sv in v.values())
        for v in segments.values()
    )


def _sorted_keys(periods):
    def _key(p):
        try:
            y, q = str(p).split("Q")
            return (-int(y), -int(q))
        except (ValueError, TypeError, IndexError, AttributeError):
            return (0, 0)
    return sorted(periods, key=_key)


def _prior_period(key):
    try:
        y, q = str(key).split("Q")
        return f"{int(y) - 1}Q{q}"
    except (ValueError, IndexError):
        return None


def _seg_grouped(segments, periods):
    sorted_p = _sorted_keys(periods)
    result = {}
    for group, items in segments.items():
        if not isinstance(items, dict):
            continue
        # Determine latest period available in this group
        # (different groups may have different period coverage)
        group_periods = set()
        for v in items.values():
            if isinstance(v, dict):
                group_periods.update(v.keys())
        latest = next((p for p in sorted_p if p in group_periods), None)
        if latest is None:
            continue
        prior = _prior_period(latest) if len(sorted_p) >= 2 else None

        trimmed = {}
        for name, vals in items.items():
            if not isinstance(vals, dict):
                continue
            entry = {}
            cv = vals.get(latest)
            if cv is not None:
                entry["latest_q"] = cv
            if prior:
                pv = vals.get(prior)
                if cv is not None and pv is not None and pv != 0:
                    entry["q_yoy_pct"] = round((cv - pv) / pv * 100, 1)
            if entry:
                trimmed[name] = entry
        if trimmed:
            result[group] = trimmed

    return slim(result) if result else slim(segments)


def _seg_flat(segments, periods):
    q_labels = sorted((p for p in periods if "(Q" in p), reverse=True)
    ytd_labels = sorted((p for p in periods if "YTD" in p), reverse=True)
    cur_q, pri_q = _find_prior_period(q_labels)
    cur_y, pri_y = _find_prior_period(ytd_labels)

    result = {}
    for name, info in segments.items():
        vals = info.get("values", {}) if isinstance(info, dict) else {}
        if not vals:
            continue
        entry = {}
        if cur_q:
            cv = vals.get(cur_q)
            if cv is not None:
                entry["latest_q"] = cv
            if pri_q:
                pv = vals.get(pri_q)
                if cv is not None and pv is not None and pv != 0:
                    entry["q_yoy_pct"] = round((cv - pv) / pv * 100, 1)
        if cur_y:
            cv = vals.get(cur_y)
            if cv is not None:
                entry["latest_ytd"] = cv
            if pri_y:
                pv = vals.get(pri_y)
                if cv is not None and pv is not None and pv != 0:
                    entry["ytd_yoy_pct"] = round((cv - pv) / pv * 100, 1)
        if entry:
            result[name] = entry

    return slim(result) if result else slim(segments)


def _find_prior_period(labels):
    """Return (current, prior_year) pair by matching quarter label."""
    if not labels:
        return None, None
    cur = labels[0]
    m = re.search(r'\(Q[1-4]\)', cur)
    if m and len(labels) > 1:
        label = m.group()
        for p in labels[1:]:
            if label in p:
                return cur, p
    return cur, labels[1] if len(labels) > 1 else None


def trim_earnings(data):
    """Keep next earnings date, forward estimates, recent quarters, beat rate."""
    if not data:
        return None
    result = {}
    if "next_earnings_date" in data:
        result["next_earnings_date"] = data["next_earnings_date"]
    if "next_eps_estimate" in data:
        result["next_eps_estimate"] = slim(data["next_eps_estimate"])
    if "next_revenue_estimate" in data:
        result["next_revenue_estimate"] = slim(data["next_revenue_estimate"])
    if "quarterly" in data and isinstance(data["quarterly"], list):
        result["quarterly"] = slim([
            {k: q[k] for k in ("quarter_end", "eps_actual", "eps_estimate",
                               "eps_difference", "eps_surprise_pct")
             if k in q}
            for q in data["quarterly"]
        ])
    if "beat_rate" in data:
        result["beat_rate"] = data["beat_rate"]
    return slim(result) if result else None


# ── Job definitions ──
# Each: (name, cmd_template, section_title, trim_function)

JOB_DEFS = [
    ("filings",
     "filings {symbol}",
     "Filings (latest 5)",
     trim_filings),
    ("income_stmt",
     "financial-report {symbol} IS p8",
     "Income Statement (8 quarters)",
     None),
     ("consensus",
      "consensus {symbol}",
      "Consensus (estimate vs actual)",
      trim_consensus),
    ("earnings",
     "earnings {symbol}",
     "Earnings Calendar & Beat Rate",
     trim_earnings),
    ("calc_index",
     "calc-index {symbol}",
     "Valuation Percentile (5yr PE/PB)",
     None),
    ("operating",
     "operating {symbol} p8",
     "Operating KPIs (8 quarters)",
     trim_operating),
    ("kline",
     "kline {symbol} day 250",
     "Daily OHLCV (250d)",
     trim_kline),
    ("quote",
     "quote {symbol}",
     "Current Quote",
     None),
    ("news",
     "news {symbol}",
     "News (latest 10)",
     trim_news),
      ("segment",
       "financial-report {symbol} SEG p8",
       "Segment Breakdown",
       trim_segment),
]

FULL_JOBS = [
    ("balance_sheet",
     "financial-report {symbol} BS p8",
     "Balance Sheet (8 quarters)",
     None),
    ("cash_flow",
     "financial-report {symbol} CF p8",
     "Cash Flow (8 quarters)",
     None),
]


# ── Output helpers ──


def print_section(title, data):
    """Print a section with '===== title =====' header and one-line JSON."""
    print("\n===== {} =====".format(title))
    if data is None:
        print("N/A (no data)")
    elif isinstance(data, str):
        print(data)
    else:
        # Single-line compact JSON
        print(json.dumps(data, ensure_ascii=False, default=str))


# ── Core collector ──


def collect(symbol, full=False):
    """Collect all data sources for symbol. Prints digest to stdout."""
    symbol = symbol.strip().upper()
    safe = symbol.lower().replace(".", "_")
    raw_dir = os.path.join(tempfile.gettempdir(), "am_earnings_{}".format(safe))
    try:
        os.makedirs(raw_dir, exist_ok=True)
    except OSError:
        pass

    ordered_jobs = JOB_DEFS + (FULL_JOBS if full else [])
    results = {}

    # Parallel fetch
    with ThreadPoolExecutor(max_workers=len(ordered_jobs)) as pool:
        fut_map = {}
        for name, cmd_tpl, _, _ in ordered_jobs:
            cmd = cmd_tpl.format(symbol=symbol)
            fut = pool.submit(fetch_source, name, cmd, raw_dir)
            fut_map[fut] = name

        for fut in as_completed(fut_map):
            name = fut_map[fut]
            try:
                results[name] = fut.result()
            except Exception as e:
                results[name] = {"ok": False, "error": str(e)}

    print("SYMBOL: {}".format(symbol))
    print("COLLECTED_AT: {}".format(now_cst()))
    print("RAW_DIR: {}".format(raw_dir))
    print("  (raw JSON files stored here \u2014 reuse, do not re-fetch)")
    print("FULL_MODE: {}".format("yes" if full else "no"))

    for name, _, sec_title, trim_fn in ordered_jobs:
        result = results.get(name, {"ok": False, "error": "not fetched"})
        if result["ok"]:
            data = result["data"]
            if trim_fn is not None:
                data = trim_fn(data)
            else:
                data = slim(data)
            print_section(sec_title, data)
        else:
            print_section(sec_title, "N/A ({})".format(result["error"]))

    print()
    return 0


# ── Health check ──


def health_check():
    """Quick GET to /api/v1/health. Returns True if server is OK."""
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
    print("""Usage: python3 collect.py <SYMBOL> [options]

Parallel earnings-data collector for AlphaMeta API.
Fetches 10 (lite) or 12 (full) data sources in parallel, saves raw JSON,
and prints a compact digest to stdout (consumed by the LLM for earnings analysis).

Arguments:
  SYMBOL            Stock symbol (e.g., AAPL, MSFT, NVDA)

Options:
  --full            Fetch full data (includes balance sheet & cash flow)
  --health          Check AlphaMeta server health only, then exit
  --help            Show this help message and exit

Examples:
  python3 collect.py AAPL
  python3 collect.py AAPL --full
  python3 collect.py MSFT
  python3 collect.py MSFT --full
  python3 collect.py --health

Environment:
  ALPHAMETA_URL     AlphaMeta server base URL (default: http://localhost:18080)
""")


def main():
    args = [a for a in sys.argv[1:] if a]

    if not args or "--help" in args or "-h" in args:
        print_usage()
        return

    if "--health" in args:
        health_check()
        return

    full = "--full" in args
    symbol_args = [a for a in args if not a.startswith("--")]
    if not symbol_args:
        eprint("Error: SYMBOL argument is required")
        print_usage()
        sys.exit(1)

    symbol = symbol_args[0]

    if not health_check():
        eprint("")
        eprint("Error: AlphaMeta server is not reachable.")
        eprint("Start it with: alphameta --ibkr")
        sys.exit(1)

    eprint("")
    eprint("Collecting {} data sources for {} (full={}) ...".format(
        len(JOB_DEFS) + (len(FULL_JOBS) if full else 0),
        symbol, full))

    sys.exit(collect(symbol, full))


if __name__ == "__main__":
    main()
