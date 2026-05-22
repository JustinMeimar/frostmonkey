#!/home/justin/tools/fossil/figures/.venv/bin/python
"""
Cleveland dot chart: JIT memory components by worker count.

Each metric is a separate marker at its true y position on a log scale.
Shape distinguishes heap vs .text, color distinguishes category.
Discovers worker counts from the input data automatically.
"""
import re
import sys

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np

from fossil_figures import apply_style, load_stdin

apply_style(column="double")
data = load_stdin()
table = data.flat_table()

base_re = re.compile(r"^n(\d+)$")
workers = sorted(
    int(base_re.match(c).group(1))
    for c in data.column_names
    if base_re.match(c)
)
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
blinterp_text = get(tags_aot[0], "blinterp_aot_kb")
ic_corpus_text = get(tags_aot[0], "ic_aot_corpus_kb")

fig, ax = plt.subplots(figsize=(5.0, 3.5))

x = np.arange(len(workers))
ms = 4
lw = 1.2

ax.plot(x, bl_compile_base, "o-", color=C_COMPILE, ms=ms, lw=lw)
ax.plot(x, blinterp_base, "o-", color=C_BLINTERP, ms=ms, lw=lw)
ax.plot(x, ic_base, "o-", color=C_IC, ms=ms, lw=lw)

ax.plot(x, bl_compile_aot, "s--", color=C_COMPILE, ms=ms, lw=lw)
ax.plot(x, [blinterp_text] * len(workers), "s--", color=C_BLINTERP, ms=ms, lw=lw)
ax.plot(x, [ic_corpus_text] * len(workers), "s--", color=C_IC, ms=ms, lw=lw)

ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels([str(n) for n in workers])
ax.set_xlabel("Workers")
ax.set_ylabel("JIT memory (KB)")
ax.set_title("JIT memory by worker count")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))

handles = [
    mlines.Line2D([], [], color=C_COMPILE, marker="o", ls="-", ms=ms, lw=lw, label="Baseline compiles"),
    mlines.Line2D([], [], color=C_BLINTERP, marker="o", ls="-", ms=ms, lw=lw, label="Blinterp"),
    mlines.Line2D([], [], color=C_IC, marker="o", ls="-", ms=ms, lw=lw, label="IC stubs"),
    mlines.Line2D([], [], color="grey", marker="o", ls="-", ms=ms, lw=lw, label="heap (base)"),
    mlines.Line2D([], [], color="grey", marker="s", ls="--", ms=ms, lw=lw, label=".text (AOT)"),
]
ax.legend(handles=handles, fontsize=7, loc="upper left")

fig.tight_layout()
fig.savefig(sys.argv[1])
