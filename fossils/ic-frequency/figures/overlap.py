#!/home/justin/tools/fossil/figures/.venv/bin/python
"""Cross-benchmark IC stub overlap table."""
import sys
from fossil_figures import apply_style, load_stdin, comparison_table

apply_style(column="single")
data = load_stdin()
columns = data.column_names

stub_sets = {}
for col in columns:
    m = data.columns[col]
    hashes = set()
    if m.children and "unique_hashes" in m.children:
        child = m.children["unique_hashes"]
        if child.tag and child.tag.strip():
            hashes = set(child.tag.split(","))
    stub_sets[col] = hashes

n = len(columns)
if n < 2:
    print("Need at least 2 variants for overlap analysis", file=sys.stderr)
    sys.exit(1)

all_union = set()
all_intersection = None
for s in stub_sets.values():
    all_union |= s
    if all_intersection is None:
        all_intersection = set(s)
    else:
        all_intersection &= s

row_labels = []
cells = []
for i in range(n):
    for j in range(i + 1, n):
        si = stub_sets[columns[i]]
        sj = stub_sets[columns[j]]
        inter = len(si & sj)
        union = len(si | sj)
        row_labels.append(f"{columns[i]} \u2229 {columns[j]}")
        cells.append([
            str(len(si)),
            str(len(sj)),
            str(inter),
            f"{inter / union:.1%}" if union > 0 else "-",
        ])

row_labels.append("All benchmarks")
cells.append([
    "", "",
    str(len(all_intersection)) if all_intersection else "0",
    f"{len(all_intersection) / len(all_union):.1%}" if all_union and all_intersection else "-",
])

fig = comparison_table(
    row_labels=row_labels,
    col_labels=["|A|", "|B|", "|A \u2229 B|", "Jaccard"],
    cells=cells,
    fontsize=8,
)
fig.savefig(sys.argv[1])
