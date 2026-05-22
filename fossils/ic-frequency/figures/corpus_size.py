#!/home/justin/tools/fossil/figures/.venv/bin/python
"""
Coverage vs. corpus size curve.

X = cumulative corpus size (bytes, shown as KB)
Y = cumulative coverage (fraction of runtime attaches)

Annotates threshold lines at 90%, 95%, 99% showing the byte cost.
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from fossil_figures import apply_style, load_stdin, palette
from fossil_figures.style import palette as get_palette

apply_style(column="single")
data = load_stdin()
colors = palette(max(len(data.column_names), 1))

fig, ax = plt.subplots()

for i, col in enumerate(data.column_names):
    m = data.columns[col]

    def extract_list(key):
        if not m.children or key not in m.children:
            return []
        child = m.children[key]
        if child.sequence:
            return [s.mean for s in child.sequence]
        return []

    def extract_scalar(key):
        if not m.children or key not in m.children:
            return None
        child = m.children[key]
        return child.mean if child.mean is not None else None

    cum_bytes = extract_list("cum_bytes")
    cum_coverage = extract_list("cum_coverage")
    if not cum_bytes:
        continue

    x = np.array(cum_bytes) / 1024.0
    y = np.array(cum_coverage) * 100.0

    ax.plot(x, y, color=colors[i], linewidth=1.5, label=col)

    for target in [90, 95, 99]:
        key = f"thresholds.{target}"
        if not m.children or key not in m.children:
            continue
        node = m.children[key]
        if not node.children:
            continue
        b_node = node.children.get("bytes")
        s_node = node.children.get("stubs")
        if not b_node or b_node.mean is None:
            continue
        bx = b_node.mean / 1024.0
        n_stubs = int(s_node.mean) if s_node and s_node.mean is not None else "?"
        ax.axhline(target, color="grey", linewidth=0.4, linestyle="--", zorder=0)
        ax.plot(bx, target, "o", color=colors[i], markersize=4, zorder=3)
        ax.annotate(
            f"{bx:.0f} KB ({n_stubs} stubs)",
            xy=(bx, target),
            xytext=(8, -2),
            textcoords="offset points",
            fontsize=6,
            color=colors[i],
        )

ax.set_xlabel("Corpus size (KB)")
ax.set_ylabel("Coverage (%)")
ax.set_ylim(0, 102)
ax.set_xscale("log")
if len(data.column_names) > 1:
    ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(sys.argv[1])
