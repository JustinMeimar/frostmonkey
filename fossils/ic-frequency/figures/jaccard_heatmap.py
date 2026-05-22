#!/home/justin/tools/fossil/figures/.venv/bin/python
"""Jaccard similarity and overlap coefficient heatmap across benchmarks.

Produces an annotated heatmap showing pairwise Jaccard index with overlap
coefficient in parentheses. Subtitle shows universe size and three-way
intersection.
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from fossil_figures import apply_style, font_sizes, load_stdin, palette

BENCHMARKS = {"octane", "sunspider", "speedometer"}

apply_style(column="single")
fs = font_sizes()
data = load_stdin()
columns = data.column_names
if os.environ.get("SITES_ONLY"):
    columns = [c for c in columns if c not in BENCHMARKS]
n = len(columns)

if n < 2:
    print("Need at least 2 variants for Jaccard analysis", file=sys.stderr)
    sys.exit(1)

stub_sets = {}
for col in columns:
    m = data.columns[col]
    hashes = set()
    if m.children and "unique_hashes" in m.children:
        child = m.children["unique_hashes"]
        if child.tag and child.tag.strip():
            hashes = set(child.tag.split(","))
    stub_sets[col] = hashes

jaccard = np.zeros((n, n))
overlap = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        si = stub_sets[columns[i]]
        sj = stub_sets[columns[j]]
        inter = len(si & sj)
        union = len(si | sj)
        min_sz = min(len(si), len(sj))
        jaccard[i][j] = inter / union if union else 0.0
        overlap[i][j] = inter / min_sz if min_sz else 0.0

universe = set()
three_inter = None
for s in stub_sets.values():
    universe |= s
    three_inter = s if three_inter is None else three_inter & s

w = max(3.2, 0.95 * n + 1.0)
h = max(2.8, 0.85 * n + 0.6)
fig, ax = plt.subplots(figsize=(w, h))
ax.grid(False)
ax.set_axisbelow(False)
im = ax.imshow(jaccard, cmap="Blues", vmin=0, vmax=1, aspect="equal")

for i in range(n):
    for j in range(n):
        jv = jaccard[i][j]
        ov = overlap[i][j]
        color = "white" if jv > 0.55 else "black"
        if i == j:
            ax.text(j, i, f"{len(stub_sets[columns[i]])}",
                    ha="center", va="center", color=color,
                    fontsize=fs["cell_bold"], fontweight="bold")
        else:
            ax.text(j, i, f"{jv:.2f}",
                    ha="center", va="center", color=color,
                    fontsize=fs["cell"])

display = [c.capitalize() for c in columns]
ax.set_xticks(range(n))
ax.set_xticklabels(display, rotation=30, ha="right")
ax.set_yticks(range(n))
ax.set_yticklabels(display)
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_visible(False)

cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.06, shrink=0.85)
cbar.set_label("Jaccard Index", fontsize=fs["tick"])
cbar.ax.tick_params(labelsize=fs["tick"])

three_inter = three_inter or set()
ax.set_title(
    f"|Universe| = {len(universe)},  "
    f"|$\\bigcap$| = {len(three_inter)}",
    pad=8,
)

fig.tight_layout()
fig.savefig(sys.argv[1])
