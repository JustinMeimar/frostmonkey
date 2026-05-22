#!/home/justin/tools/fossil/figures/.venv/bin/python
"""
Table figure: raw JIT memory metrics across all worker counts.
Shows base and AOT side-by-side for each metric.
"""
import sys

from fossil_figures import apply_style, load_stdin, comparison_table

apply_style(column="double")
data = load_stdin()
table = data.flat_table()

workers = [1, 16, 64, 128, 256]


def get(variant, key):
    return table[variant][key].mean


def kb(v):
    if v == 0:
        return "\u2014"
    if v < 1:
        return f"{v:.1f}"
    return f"{v:,.1f}"


row_labels = []
cells = []

for n in workers:
    base = f"n{n}"
    aot = f"n{n}-aot"

    row_labels.append(f"n={n} base")
    cells.append([
        kb(get(base, "bl_compile_kb")),
        kb(get(base, "blinterp_runtime_kb")),
        kb(get(base, "ic_runtime_kb")),
        "\u2014",
        "\u2014",
    ])

    row_labels.append(f"n={n} AOT")
    cells.append([
        kb(get(aot, "bl_compile_kb")),
        kb(get(aot, "blinterp_aot_kb")),
        "\u2014",
        kb(get(aot, "ic_aot_corpus_kb")),
        str(int(get(aot, "ic_aot_attach_count"))),
    ])

col_labels = [
    "bl_compile\n(KB)",
    "blinterp\n(KB)",
    "IC runtime\n(KB)",
    "IC corpus\n(KB)",
    "IC AOT\nattaches",
]

fig = comparison_table(
    row_labels=row_labels,
    col_labels=col_labels,
    cells=cells,
    title="JIT memory breakdown by variant",
    fontsize=8,
)

fig.savefig(sys.argv[1])
