#!/home/justin/tools/fossil/figures/.venv/bin/python
"""Grouped bar chart comparing pageload timing: default JIT vs FrostMonkey.

Expects variants named '<site>-default' and '<site>-fm'.
Three panels: FCP, DOMContentLoaded, LCP.
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from fossil_figures import apply_style, load_stdin, palette

apply_style(column="double")
data = load_stdin()
columns = data.column_names

sites = {}
for col in columns:
    if col.endswith("-default"):
        site = col[: -len("-default")]
        sites.setdefault(site, {})["default"] = col
    elif col.endswith("-fm"):
        site = col[: -len("-fm")]
        sites.setdefault(site, {})["fm"] = col

sites = {s: v for s, v in sites.items() if "default" in v and "fm" in v}
site_names = sorted(sites.keys())
n = len(site_names)

if n == 0:
    print("No matched site pairs found", file=sys.stderr)
    sys.exit(1)

def get_scalar(col, metric):
    m = data.columns[col]
    if m.children and metric in m.children:
        s = m.children[metric].scalar
        if s:
            return s.mean, s.stddev
    if m.scalar:
        return m.scalar.mean, m.scalar.stddev
    return 0.0, 0.0

metrics = [
    ("fcp_ms", "FCP (ms)"),
    ("dom_content_loaded_ms", "DCL (ms)"),
]

fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0))
colors = palette(2)

for ax, (metric, ylabel) in zip(axes, metrics):
    ax.grid(False)
    x = np.arange(n)
    w = 0.35

    default_means = []
    default_errs = []
    fm_means = []
    fm_errs = []

    for site in site_names:
        dm, de = get_scalar(sites[site]["default"], metric)
        fm, fe = get_scalar(sites[site]["fm"], metric)
        default_means.append(dm)
        default_errs.append(de)
        fm_means.append(fm)
        fm_errs.append(fe)

    ax.bar(x - w / 2, default_means, w, yerr=default_errs,
           label="Default", color=colors[0], edgecolor="none")
    ax.bar(x + w / 2, fm_means, w, yerr=fm_errs,
           label="FrostMonkey", color=colors[1], edgecolor="none")

    display = [s.capitalize() for s in site_names]
    ax.set_xticks(x)
    ax.set_xticklabels(display, rotation=45, ha="right", fontsize=6)
    ax.set_ylabel(ylabel, fontsize=7)
    if ax is axes[0]:
        ax.legend(fontsize=6, loc="upper left")

fig.tight_layout()
fig.savefig(sys.argv[1])
