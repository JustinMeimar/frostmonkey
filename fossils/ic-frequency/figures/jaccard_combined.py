#!/home/justin/tools/fossil/figures/.venv/bin/python
"""Jaccard similarity and frequency-weighted coverage in a single split matrix.

Lower triangle: Jaccard index (symmetric).
Upper triangle: frequency-weighted coverage (asymmetric, row corpus → col target).
Diagonal: set size per site (bold).
"""
import os
import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from fossil_figures import apply_style, font_sizes, load_stdin

BENCHMARKS = {"octane", "sunspider", "speedometer"}

apply_style(column="single")
fs = font_sizes()
data = load_stdin()
columns = data.column_names
if os.environ.get("SITES_ONLY"):
    columns = [c for c in columns if c not in BENCHMARKS]
n = len(columns)

if n < 2:
    print("Need at least 2 variants", file=sys.stderr)
    sys.exit(1)

stub_sets = {}
freqs = {}
for col in columns:
    m = data.columns[col]
    hashes = set()
    freq = {}
    if m.children and "unique_hashes" in m.children:
        child = m.children["unique_hashes"]
        if child.tag and child.tag.strip():
            hashes = set(child.tag.split(","))
    if m.children and "stub_freqs" in m.children:
        child = m.children["stub_freqs"]
        if child.tag and child.tag.strip():
            for entry in child.tag.split(";"):
                k, v = entry.rsplit("=", 1)
                freq[k] = int(v)
    stub_sets[col] = hashes
    freqs[col] = freq

jaccard = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        si = stub_sets[columns[i]]
        sj = stub_sets[columns[j]]
        inter = len(si & sj)
        union = len(si | sj)
        jaccard[i][j] = inter / union if union else 0.0

coverage = np.zeros((n, n))
for i in range(n):
    corpus = stub_sets[columns[i]]
    for j in range(n):
        target_freq = freqs[columns[j]]
        total = sum(target_freq.values())
        if total == 0:
            continue
        covered = sum(target_freq[k] for k in target_freq if k in corpus)
        coverage[i][j] = covered / total

universe = set()
all_inter = None
for s in stub_sets.values():
    universe |= s
    all_inter = s if all_inter is None else all_inter & s
all_inter = all_inter or set()

display = [c.capitalize() for c in columns]
cell = 0.52
w = cell * n + 1.6
h = cell * n + 0.9

cmap_j = plt.get_cmap("Blues")
cmap_c = plt.get_cmap("OrRd")
jac_off = jaccard[np.triu_indices(n, k=1)]
jac_lo = float(jac_off.min()) - 0.05 if jac_off.size else 0.0
jac_hi = float(jac_off.max()) + 0.05 if jac_off.size else 1.0
cov_off = coverage[np.triu_indices(n, k=1)]
cov_lo = max(float(cov_off.min()) - 0.05, 0.0) if cov_off.size else 0.0
cov_hi = min(float(cov_off.max()) + 0.02, 1.0) if cov_off.size else 1.0
norm_j = Normalize(vmin=jac_lo, vmax=jac_hi)
norm_c = Normalize(vmin=cov_lo, vmax=cov_hi)

fig, ax = plt.subplots(figsize=(w, h))
ax.grid(False)
ax.set_axisbelow(False)

blank = np.full((n, n), np.nan)
ax.imshow(blank, aspect="equal", cmap="Blues", vmin=0, vmax=1)

for i in range(n):
    for j in range(n):
        if i == j:
            ax.add_patch(plt.Rectangle(
                (j - 0.5, i - 0.5), 1, 1,
                facecolor="#e8e8e8", edgecolor="white", linewidth=1.5,
            ))
            ax.text(j, i, f"{len(stub_sets[columns[i]])}",
                    ha="center", va="center", fontweight="bold",
                    fontsize=fs["cell_bold"], color="#333333")
        elif i > j:
            v = jaccard[i][j]
            ax.add_patch(plt.Rectangle(
                (j - 0.5, i - 0.5), 1, 1,
                facecolor=cmap_j(norm_j(v)), edgecolor="white", linewidth=1.5,
            ))
            color = "white" if norm_j(v) > 0.6 else "black"
            ax.text(j, i, f"{v:.2f}",
                    ha="center", va="center", fontsize=fs["cell"], color=color)
        else:
            v = coverage[i][j]
            ax.add_patch(plt.Rectangle(
                (j - 0.5, i - 0.5), 1, 1,
                facecolor=cmap_c(norm_c(v)), edgecolor="white", linewidth=1.5,
            ))
            color = "white" if norm_c(v) > 0.6 else "black"
            ax.text(j, i, f"{v:.2f}",
                    ha="center", va="center", fontsize=fs["cell"], color=color)

ax.set_xlim(-0.5, n - 0.5)
ax.set_ylim(n - 0.5, -0.5)
ax.set_xticks(range(n))
ax.set_xticklabels(display, rotation=30, ha="right")
ax.set_yticks(range(n))
ax.set_yticklabels(display)
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_visible(False)

fig.subplots_adjust(right=0.82)
bbox = ax.get_position()
gap = 0.03
bar_w = 0.02
bar_h = (bbox.height - gap) / 2
x0 = bbox.x1 + 0.04

cax_j = fig.add_axes([x0, bbox.y0 + bar_h + gap, bar_w, bar_h])
sm_j = mpl.cm.ScalarMappable(cmap=cmap_j, norm=norm_j)
cbar_j = fig.colorbar(sm_j, cax=cax_j)
cbar_j.set_label("Jaccard", fontsize=fs["tick"])
cbar_j.ax.tick_params(labelsize=fs["tick"])

cax_c = fig.add_axes([x0, bbox.y0, bar_w, bar_h])
sm_c = mpl.cm.ScalarMappable(cmap=cmap_c, norm=norm_c)
cbar_c = fig.colorbar(sm_c, cax=cax_c)
cbar_c.set_label("Coverage", fontsize=fs["tick"])
cbar_c.ax.tick_params(labelsize=fs["tick"])

ax.set_title(
    f"Jaccard (\u25e3) / Coverage (\u25e5)"
    f"    |U|={len(universe)}  |$\\bigcap$|={len(all_inter)}",
    pad=10,
)

fig.savefig(sys.argv[1])
