#!/usr/bin/env python3
"""
render_charts.py - thin chart renderer for alphameta-earnings.

Reads RAW_DIR JSON files produced by collect.py and renders PNG charts via
the ChartBuilder library in generate_report.py. Charts are written into an
output directory (default: charts/ under the skill dir) so the run_script
artifact snapshot registers them as previewable products.

Usage:
    python3 render_charts.py --raw-dir /tmp/am_earnings_aapl
    python3 render_charts.py --raw-dir /tmp/am_earnings_aapl --chart revenue analyst-pt

Charts: revenue, eps, beat-rate, price-action, analyst-pt, segments
(RAW_DIR files: income_stmt.json, earnings.json, kline.json, quote.json,
 consensus.json, segment.json)
"""
import argparse, json, os, shutil

from generate_report import ChartBuilder

CHART_NAMES = ("revenue", "eps", "beat-rate", "price-action", "analyst-pt", "segments")
cb = ChartBuilder()


def _load(raw_dir: str, name: str):
    try:
        with open(os.path.join(raw_dir, name + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, IOError, ValueError):
        return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _income_series(income, kpi: str):
    if not isinstance(income, dict):
        return [], {}
    stmt = income.get("IS", income)
    if not isinstance(stmt, dict):
        return [], {}
    periods = stmt.get("periods", [])
    metrics = stmt.get("metrics", {})
    metric = metrics.get(kpi) if isinstance(metrics, dict) else None
    if not isinstance(metric, dict):
        return [], {}
    return periods, metric.get("values", {})


def _zip_valid(periods, values, limit: int):
    pairs = [(str(p), _num(v)) for p, v in zip(periods, values)]
    pairs = [(p, v) for p, v in pairs if v is not None]
    pairs = pairs[-limit:]
    return ([p for p, _ in pairs], [v for _, v in pairs])


def _save_copy(src: str, out_dir: str, name: str) -> str:
    dest = os.path.join(out_dir, name + ".png")
    shutil.copy(src, dest)
    return dest


def _current(quote):
    if not isinstance(quote, dict):
        return None
    quotes = quote.get("quotes")
    q = quotes[0] if isinstance(quotes, list) and quotes else quote
    if not isinstance(q, dict):
        return None
    return _num(q.get("last") or q.get("close") or q.get("price"))


def _price_target(consensus):
    if not isinstance(consensus, dict):
        return (None, None, None, None)
    pt = (consensus.get("price_target") or consensus.get("target_price")
          or consensus.get("price_targets"))
    if not isinstance(pt, dict):
        return (None, None, None, None)

    def g(*keys):
        for k in keys:
            if k in pt:
                v = _num(pt[k])
                if v is not None:
                    return v
        return None
    return (g("mean", "targetMean", "average", "avg"),
            g("high", "targetHigh", "high_estimate"),
            g("low", "targetLow", "low_estimate"),
            g("num_analysts", "numAnalysts", "analyst_count", "count"))


def _render_revenue(out_dir, income):
    periods, values = _income_series(income, "Revenue")
    vals = [v / 1000.0 if v is not None else None for v in
            (values.get(p) for p in periods)]
    quarters, series = _zip_valid(periods, vals, 8)
    if len(series) < 2:
        return None, "income_stmt: Revenue series unavailable"
    return _save_copy(
        cb.quarterly_bar("Revenue Trend", quarters, series, ylabel="$B"),
        out_dir, "revenue"), None


def _render_eps(out_dir, income):
    periods, values = _income_series(income, "EPS (Diluted)")
    quarters, series = _zip_valid(periods, [values.get(p) for p in periods], 8)
    if len(series) < 2:
        return None, "income_stmt: EPS (Diluted) series unavailable"
    return _save_copy(
        cb.quarterly_bar("EPS (Diluted)", quarters, series, ylabel="USD"),
        out_dir, "eps"), None


def _render_beat_rate(out_dir, earnings):
    if not isinstance(earnings, dict):
        return None, "earnings: data unavailable"
    rows = earnings.get("quarterly", [])
    if not isinstance(rows, list):
        return None, "earnings: quarterly unavailable"
    dates, vals = [], []
    for r in rows:
        if isinstance(r, dict):
            v = _num(r.get("eps_surprise_pct"))
            if v is not None:
                dates.append(str(r.get("quarter_end", ""))[:10])
                vals.append(v)
    if len(vals) < 2:
        return None, "earnings: eps_surprise_pct series unavailable"
    return _save_copy(
        cb.growth_lines("EPS Surprise % (Beat/Miss)", dates,
                        [{"label": "Surprise %", "values": vals}]),
        out_dir, "beat-rate"), None


def _render_price_action(out_dir, kline, quote):
    if not isinstance(kline, dict):
        return None, "kline: data unavailable"
    rows = kline.get("last_20", [])
    dates, closes = [], []
    for r in rows:
        if isinstance(r, dict):
            c = _num(r.get("close"))
            if c is not None:
                dates.append(str(r.get("date", ""))[:10])
                closes.append(c)
    if len(closes) < 2:
        return None, "kline: last_20 closes unavailable"
    cur = _current(quote)
    label = f"${cur:,.2f}" if cur is not None else "current"
    return _save_copy(
        cb.price_action("Price Action (20 sessions)", dates, closes,
                        cur, label, ylabel="Price"),
        out_dir, "price-action"), None


def _render_analyst_pt(out_dir, consensus, quote):
    mean, high, low, n = _price_target(consensus)
    cur = _current(quote)
    if mean is None or cur is None:
        return None, "consensus/quote: price target or current price unavailable"
    label = f"${cur:,.2f}"
    return _save_copy(
        cb.analyst_pt_hbar("Analyst Price Target", cur, label,
                           target_mean=mean, target_high=high, target_low=low,
                           num_analysts=n),
        out_dir, "analyst-pt"), None


def _render_segments(out_dir, segment):
    if not isinstance(segment, dict):
        return None, "segment: data unavailable"
    segs = segment.get("segments", {})
    if not isinstance(segs, dict):
        return None, "segment: segments dict unavailable"
    names, vals = [], []
    for name, info in segs.items():
        if isinstance(info, dict):
            v = _num(info.get("latest_q"))
            if v is not None:
                names.append(str(name))
                vals.append(v)
    if len(names) < 2:
        return None, "segment: latest_q values unavailable"
    return _save_copy(
        cb.grouped_bar("Segment Revenue (Latest Quarter)", names,
                       [{"label": "Latest Q", "values": vals}], ylabel="$"),
        out_dir, "segments"), None


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="render_charts.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--raw-dir", required=True,
                        help="RAW_DIR printed by collect.py")
    parser.add_argument("--out-dir", default="charts",
                        help="PNG output dir (relative to skill dir; default: charts)")
    parser.add_argument("--chart", nargs="+", choices=CHART_NAMES,
                        help="Chart(s) to render (space-separated; default: all)")
    args = parser.parse_args()

    if not os.path.isdir(args.raw_dir):
        print(f"ERROR: raw dir not found: {args.raw_dir}")
        return 1

    data = {
        "income_stmt": _load(args.raw_dir, "income_stmt"),
        "consensus": _load(args.raw_dir, "consensus"),
        "earnings": _load(args.raw_dir, "earnings"),
        "kline": _load(args.raw_dir, "kline"),
        "quote": _load(args.raw_dir, "quote"),
        "segment": _load(args.raw_dir, "segment"),
    }
    os.makedirs(args.out_dir, exist_ok=True)
    wanted = args.chart or list(CHART_NAMES)

    renders = [
        ("revenue", _render_revenue, (data["income_stmt"],)),
        ("eps", _render_eps, (data["income_stmt"],)),
        ("beat-rate", _render_beat_rate, (data["earnings"],)),
        ("price-action", _render_price_action, (data["kline"], data["quote"])),
        ("analyst-pt", _render_analyst_pt, (data["consensus"], data["quote"])),
        ("segments", _render_segments, (data["segment"],)),
    ]

    rendered, skipped = [], []
    for name, fn, fargs in renders:
        if name not in wanted:
            continue
        try:
            path, why = fn(args.out_dir, *fargs)
        except Exception as e:
            path, why = None, f"{type(e).__name__}: {e}"
        if path:
            rendered.append(path)
        else:
            skipped.append(f"{name} ({why})")

    for p in rendered:
        print(f"PNG: {p}")
    for s in skipped:
        print(f"SKIP: {s}")
    print(f"rendered {len(rendered)}/{len(wanted)} charts")
    return 0 if rendered else 1


if __name__ == "__main__":
    raise SystemExit(main())
