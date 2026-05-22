#!/home/justin/tools/fossil/figures/.venv/bin/python
"""Frequency-weighted coverage matrix across benchmarks.

Asymmetric matrix where cell (i,j) answers: "If we use benchmark i's
stub corpus as the AOT set, what fraction of benchmark j's runtime IC
attach requests are cache hits?"

This is the operationally relevant metric for FrostMonkey's PGO policy.
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
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
    print("Need at least 2 variants for coverage analysis", file=sys.stderr)
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

w = max(3.2, 0.95 * n + 1.0)
h = max(2.8, 0.85 * n + 0.6)
fig, ax = plt.subplots(figsize=(w, h))
ax.grid(False)
ax.set_axisbelow(False)
im = ax.imshow(coverage, cmap="Greens", vmin=0.5, vmax=1.0, aspect="equal")

for i in range(n):
    for j in range(n):
        v = coverage[i][j]
        color = "white" if v > 0.92 else "black"
        ax.text(j, i, f"{v:.0%}", ha="center", va="center",
                color=color, fontsize=fs["cell_bold"], fontweight="bold")

display = [c.capitalize() for c in columns]
ax.set_xticks(range(n))
ax.set_xticklabels(display, rotation=30, ha="right")
ax.set_yticks(range(n))
ax.set_yticklabels(display)
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_visible(False)

ax.set_ylabel("AOT Corpus Source")
ax.set_xlabel("Target Workload")

cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.06, shrink=0.85)
cbar.set_label("Request Coverage", fontsize=fs["tick"])
cbar.ax.tick_params(labelsize=fs["tick"])

fig.tight_layout()
fig.savefig(sys.argv[1])
