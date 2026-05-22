#!/home/justin/tools/fossil/figures/.venv/bin/python
"""
JIT lifecycle timeseries scatter plot.

x = time (ms since JIT init)
y = code size (bytes, log scale)
color = tier (baseline, ion, ic, ic_ion)
"""
import json, sys
import numpy as np
import matplotlib.pyplot as plt
from fossil_figures import apply_style
from fossil_figures.style import palette

apply_style(column="single")
plt.rcParams["figure.figsize"] = (7.0, 2.4)

raw = json.load(sys.stdin)

TIER_COLORS = {}
pal = palette(5)
for tier, color in zip(["blinterp", "baseline", "ic", "ic_ion", "ion"], pal):
    TIER_COLORS[tier] = color

TIER_LABELS = {
    "blinterp": "BL Interp",
    "baseline": "Baseline",
    "ion": "Ion",
    "ic": "IC (Baseline)",
    "ic_ion": "IC (Ion)",
}

ALLOC_ACTIONS = {"compile", "ic-attach"}

for variant_name, data in raw.items():
    def scalar(v):
        if isinstance(v, dict) and "mean" in v:
            return v["mean"]
        return v

    def extract_list(key):
        arr = data[key]
        if isinstance(arr, list):
            return [scalar(x) for x in arr]
        return []

    ts_us = extract_list("ts_us")
    bytes_arr = extract_list("bytes")
    tier_arr = extract_list("tier")
    action_arr = extract_list("action")

    if not ts_us:
        continue

    ts_ms = np.array([t / 1000.0 for t in ts_us])
    sizes = np.array([float(b) for b in bytes_arr])

    fig, ax = plt.subplots()

    for tier in ["blinterp", "baseline", "ic", "ic_ion", "ion"]:
        color = TIER_COLORS[tier]
        label = TIER_LABELS[tier]

        mask = np.array([
            t == tier and a in ALLOC_ACTIONS
            for t, a in zip(tier_arr, action_arr)
        ])

        if mask.any():
            ax.scatter(
                ts_ms[mask], sizes[mask],
                s=3, c=color, alpha=0.35, edgecolors="none",
                label=label,
            )

    ax.set_yscale("log")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Code size (bytes)")
    leg = ax.legend(loc="upper left", framealpha=0.8)
    for handle in leg.legend_handles:
        handle.set_sizes([20])
        handle.set_alpha(1.0)

    fig.savefig(sys.argv[1])
    break
