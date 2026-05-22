#!/home/justin/tools/fossil/figures/.venv/bin/python
import sys
from fossil_figures import apply_style, load_stdin, comparison_table
from fossil_figures.types import Scalar

apply_style(column="single")
data = load_stdin()
table = data.flat_table()

rt = table.get("runtime-baseline", {})
aot = table.get("aot-full", {})

def fmt_scalar(s):
    if s is None:
        return "-"
    if s.stddev == 0 or s.mean == 0:
        return f"{s.mean:.0f}"
    return f"{s.mean:.0f} \u00b1 {s.stddev:.0f}"

def speedup(rt_s, aot_s):
    if rt_s is None or aot_s is None or aot_s.mean == 0:
        return "-"
    ratio = rt_s.mean / aot_s.mean
    return f"{ratio:.1f}x"

components = [
    ("Interpreter",  "jit_gen_interp_us",       "aot_load_interp_us"),
    ("IC Stubs",     "jit_gen_ics_us",          "aot_load_ics_us"),
    ("Self-hosted",  "jit_gen_selfhosted_us",   "aot_load_selfhosted_us"),
]

row_labels = []
cells = []
for label, rt_key, aot_key in components:
    rt_s = rt.get(rt_key)
    aot_s = aot.get(aot_key)
    row_labels.append(label)
    cells.append([
        fmt_scalar(rt_s),
        fmt_scalar(aot_s),
        speedup(rt_s, aot_s),
    ])

rt_total = sum(rt.get(k, Scalar(0, 0)).mean for _, k, _ in components)
aot_total = sum(aot.get(k, Scalar(0, 0)).mean for _, _, k in components)
row_labels.append("Total")
cells.append([
    f"{rt_total:.0f}",
    f"{aot_total:.0f}",
    f"{rt_total / aot_total:.1f}x" if aot_total > 0 else "-",
])

fig = comparison_table(
    row_labels=row_labels,
    col_labels=["Runtime Gen (\u00b5s)", "AOT Load (\u00b5s)", "Speedup"],
    cells=cells,
    fontsize=8,
)
fig.savefig(sys.argv[1])
