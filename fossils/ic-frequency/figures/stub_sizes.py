#!/home/justin/tools/fossil/figures/.venv/bin/python
import sys
import numpy as np
from fossil_figures import apply_style, load_stdin, palette
import matplotlib.pyplot as plt

apply_style(column="single")
data = load_stdin()
colors = palette(len(data.column_names))

fig, ax = plt.subplots()

for i, col in enumerate(data.column_names):
    m = data.columns[col]
    seq = None
    if m.children and "size_distribution" in m.children:
        child = m.children["size_distribution"]
        if child.sequence:
            seq = [s.mean for s in child.sequence]
    if not seq:
        continue

    ax.hist(
        seq,
        bins=np.logspace(np.log10(max(min(seq), 1)), np.log10(max(seq)), 30),
        alpha=0.6,
        label=col,
        color=colors[i],
        edgecolor="none",
    )

ax.set_xscale("log")
ax.set_xlabel("Stub code size (bytes)")
ax.set_ylabel("Count")
ax.legend()
fig.tight_layout()
fig.savefig(sys.argv[1])
