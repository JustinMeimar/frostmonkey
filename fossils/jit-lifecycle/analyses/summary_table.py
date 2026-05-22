#!/usr/bin/env python3
"""
Post-processor: reads fossil analyze JSON (summary) from stdin,
outputs fossil-table format JSON for the paper.

Aggregates metrics per tier across workloads. tp6 sites are grouped
into a single "tp6" row showing min–max range. Octane and speedometer
appear as individual rows.

Usage:
  fossil analyze --project spidermonkey jit-lifecycle -a summary \
    | python3 analyses/summary_table.py > figures/summary.json
"""
import json, sys

data = json.load(sys.stdin)

TP6_SITES = {
    "reddit", "wikipedia", "youtube", "amazon",
    "imdb", "bing", "fandom", "stackoverflow",
}

TIERS = [
    ("BL Interp", "blinterp_compiles", "blinterp_compile_bytes", "blinterp_discard_bytes"),
    ("Baseline",   "baseline_compiles", "baseline_compile_bytes", "baseline_discard_bytes"),
    ("Ion",        "ion_compiles",      "ion_compile_bytes",      "ion_discard_bytes"),
    ("IC stubs",   "ic_attaches",       "ic_attach_bytes",        "ic_detach_bytes"),
]


def val(d, key):
    v = d.get(key, {})
    if isinstance(v, dict) and "mean" in v:
        return v["mean"]
    return v if isinstance(v, (int, float)) else 0


def human_bytes(b):
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB"
    if b >= 1024:
        return f"{b / 1024:,.0f} KB"
    return f"{b:.0f} B"


def avg_size(total_bytes, count):
    if count == 0:
        return None
    return total_bytes / count


def retention(gen, disc):
    if gen == 0:
        return None
    return (gen - disc) / gen


def fmt_range(values, formatter):
    values = [v for v in values if v is not None]
    if not values:
        return "\u2014"
    lo, hi = min(values), max(values)
    if lo == hi:
        return formatter(lo)
    return f"{formatter(lo)}\u2013{formatter(hi)}"


def fmt_bytes(b):
    return human_bytes(b)


def fmt_pct(p):
    return f"{p * 100:.0f}%"


def tier_metrics(d, count_key, gen_key, disc_key):
    count = val(d, count_key)
    gen = val(d, gen_key)
    disc = val(d, disc_key)
    total = val(d, "total_jit_bytes_generated")
    return {
        "allocs": count,
        "generated": gen,
        "avg_size": avg_size(gen, count),
        "share": gen / total if total else None,
        "retention": retention(gen, disc),
    }


def make_row(label, metrics_list):
    allocs = [m["allocs"] for m in metrics_list]
    return [
        label,
        fmt_range(allocs, lambda v: f"{v:,.0f}"),
        fmt_range([m["generated"] for m in metrics_list], fmt_bytes),
        fmt_range([m["avg_size"] for m in metrics_list], fmt_bytes),
        fmt_range([m["share"] for m in metrics_list], fmt_pct),
        fmt_range([m["retention"] for m in metrics_list], fmt_pct),
    ]


standalone = {}
tp6_variants = {}

for name, d in data.items():
    if name.endswith("-aot"):
        continue
    if name in TP6_SITES:
        tp6_variants[name] = d
    else:
        standalone[name] = d

workload_groups = list(standalone.items())
if tp6_variants:
    workload_groups.append(("tp6", tp6_variants))

rows = []
for wl_name, wl_data in workload_groups:
    if isinstance(wl_data, dict) and any(isinstance(v, dict) and "mean" in v for v in wl_data.values()):
        variant_dicts = [wl_data]
    else:
        variant_dicts = list(wl_data.values())

    for tier_label, count_key, gen_key, disc_key in TIERS:
        metrics_list = [tier_metrics(d, count_key, gen_key, disc_key) for d in variant_dicts]
        row_label = f"{wl_name}: {tier_label}"
        rows.append(make_row(row_label, metrics_list))

json.dump({
    "header": ["Tier", "Allocs", "Generated", "Avg Size", "Share", "Retention"],
    "rows": rows,
}, sys.stdout, indent=2)
sys.stdout.write("\n")
