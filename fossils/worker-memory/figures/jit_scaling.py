#!/home/justin/tools/fossil/figures/.venv/bin/python
"""
Stacked bar chart: JIT memory scaling with worker count.

Baseline bars are all heap (solid). AOT bars show heap bl_compile (solid)
plus shared .text for blinterp and IC corpus (hatched). The .text sizes
are taken from n1-aot since they're shared mappings — the analysis script
sums per-worker events, overcounting by N.
"""
import sys

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from fossil_figures import apply_style, load_stdin

apply_style(column="single")
data = load_stdin()
table = data.flat_table()

workers = [1, 16, 64, 128, 256]
tags_base = [f"n{n}" for n in workers]
tags_aot = [f"n{n}-aot" for n in workers]

C_COMPILE = "#2E86AB"
C_BLINTERP = "#F18F01"
C_IC = "#C73E1D"


def get(variant, key):
    return table[variant][key].mean


bl_compile_base = [get(t, "bl_compile_kb") for t in tags_base]
blinterp_base = [get(t, "blinterp_runtime_kb") for t in tags_base]
ic_base = [get(t, "ic_runtime_kb") for t in tags_base]

bl_compile_aot = [get(t, "bl_compile_kb") for t in tags_aot]

blinterp_text = get("n1-aot", "blinterp_aot_kb")
ic_corpus_text = get("n1-aot", "ic_aot_corpus_kb")

fig, ax = plt.subplots()

x = np.arange(len(workers))
w = 0.35

ax.bar(x - w / 2, bl_compile_base, w, color=C_COMPILE)
ax.bar(x - w / 2, blinterp_base, w, bottom=bl_compile_base, color=C_BLINTERP)
ax.bar(
    x - w / 2, ic_base, w,
    bottom=[a + b for a, b in zip(bl_compile_base, blinterp_base)],
    color=C_IC,
)

ax.bar(
    x + w / 2, [ic_corpus_text] * len(workers), w,
    color=C_IC, alpha=0.5, hatch="//", edgecolor=C_IC,
)
ax.bar(
    x + w / 2, [blinterp_text] * len(workers), w,
    bottom=[ic_corpus_text] * len(workers),
    color=C_BLINTERP, alpha=0.5, hatch="//", edgecolor=C_BLINTERP,
)
bot_heap = [ic_corpus_text + blinterp_text] * len(workers)
ax.bar(x + w / 2, bl_compile_aot, w, bottom=bot_heap, color=C_COMPILE)

ax.set_xticks(x)
ax.set_xticklabels([str(n) for n in workers])
ax.tick_params(axis="x", pad=14)
ax.set_xlabel("Workers")
for i in range(len(workers)):
    ax.text(
        i - w / 2, -0.06, "base", transform=ax.get_xaxis_transform(),
        ha="center", va="top", fontsize=5, color="#555555",
    )
    ax.text(
        i + w / 2, -0.06, "AOT", transform=ax.get_xaxis_transform(),
        ha="center", va="top", fontsize=5, color="#555555",
    )
ax.set_yscale("log")
ax.set_ylabel("JIT memory (KB)")
ax.set_title("JIT memory by worker count")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))

handles = [
    mpatches.Patch(facecolor=C_COMPILE, label="Baseline compiles (heap)"),
    mpatches.Patch(facecolor=C_BLINTERP, label="Blinterp (heap)"),
    mpatches.Patch(facecolor=C_IC, label="IC stubs (heap)"),
    mpatches.Patch(facecolor=C_BLINTERP, alpha=0.5, hatch="//", label="Blinterp (.text)"),
    mpatches.Patch(facecolor=C_IC, alpha=0.5, hatch="//", label="IC corpus (.text)"),
]
ax.legend(
    handles=handles, fontsize=5.5, ncol=2,
    loc="lower center", bbox_to_anchor=(0.5, 1.0),
    frameon=False, columnspacing=1.0,
)

fig.tight_layout()
fig.subplots_adjust(top=0.82)
fig.savefig(sys.argv[1])
