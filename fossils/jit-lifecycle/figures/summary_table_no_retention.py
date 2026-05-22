#!/home/justin/tools/fossil/figures/.venv/bin/python
import sys
from fossil_figures import apply_style, load_stdin, comparison_table

apply_style(column="double")
data = load_stdin()
table = data.flat_table()


def val(m, key):
    s = m.get(key)
    return s.mean if s else 0.0


def human_bytes(b):
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB"
    if b >= 1024:
        return f"{b / 1024:,.0f} KB"
    return f"{b:.0f} B"


def avg(total_bytes, count):
    if count == 0:
        return "\u2014"
    return human_bytes(total_bytes / count)


def pct(num, den):
    if den == 0:
        return "\u2014"
    return f"{num / den * 100:.1f}%"


rows = []
cells = []

for variant_name, m in table.items():
    interp_compiles = val(m, "blinterp_compiles")
    interp_gen = val(m, "blinterp_compile_bytes")

    bl_compiles = val(m, "baseline_compiles")
    bl_gen = val(m, "baseline_compile_bytes")

    ion_compiles = val(m, "ion_compiles")
    ion_gen = val(m, "ion_compile_bytes")

    ic_attaches = val(m, "ic_attaches")
    ic_gen = val(m, "ic_attach_bytes")

    total_gen = val(m, "total_jit_bytes_generated")

    tiers = [
        ("BL Interp", interp_compiles, interp_gen),
        ("Baseline", bl_compiles, bl_gen),
        ("Ion", ion_compiles, ion_gen),
        ("IC stubs", ic_attaches, ic_gen),
    ]

    for i, (tier, count, gen) in enumerate(tiers):
        if i == 0:
            label = f"{variant_name}: {tier}"
        else:
            label = f"  {tier}"
        rows.append(label)
        cells.append([
            f"{count:,.0f}",
            human_bytes(gen),
            avg(gen, count),
            pct(gen, total_gen),
        ])

fig = comparison_table(
    row_labels=rows,
    col_labels=["Allocs", "Generated", "Avg Size", "Share"],
    cells=cells,
    title="JIT lifecycle summary",
    fontsize=8,
)

fig.savefig(sys.argv[1])
