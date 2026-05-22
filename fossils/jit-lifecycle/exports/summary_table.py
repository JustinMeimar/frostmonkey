#!/usr/bin/env python3
"""
Reshape fossil summary analysis output into a generic table JSON
consumable by the typst fossil-table function.

Input:  fossil analysis JSON on stdin (variant-keyed, mean/stddev wrapped)
Output: {"header": [...], "rows": [[...], ...]} on stdout
"""
import json, sys

raw = json.load(sys.stdin)

def scalar(v):
    if isinstance(v, dict) and "mean" in v:
        return v["mean"]
    return v

def human_bytes(b):
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB"
    if b >= 1024:
        return f"{b / 1024:,.0f} KB"
    return f"{b:.0f} B"

def pct(num, den):
    if den == 0:
        return "\u2014"
    return f"{num / den * 100:.1f}%"

for variant_name, m in raw.items():
    def val(key):
        return scalar(m.get(key, 0))

    interp_gen = val("blinterp_compile_bytes")
    interp_disc = val("blinterp_discard_bytes")
    interp_events = val("blinterp_compiles") + val("blinterp_discards")

    bl_gen = val("baseline_compile_bytes")
    bl_disc = val("baseline_discard_bytes")
    bl_events = val("baseline_compiles") + val("baseline_discards")

    ion_gen = val("ion_compile_bytes")
    ion_disc = val("ion_discard_bytes")
    ion_events = val("ion_compiles") + val("ion_discards")

    ic_gen = val("ic_attach_bytes")
    ic_disc = val("ic_detach_bytes")
    ic_events = val("ic_attaches") + val("ic_detaches")

    total_gen = val("total_jit_bytes_generated")
    total_events = interp_events + bl_events + ion_events + ic_events

    rows = [
        ["BL Interp", f"{interp_events:,.0f}", human_bytes(interp_gen), pct(interp_gen, total_gen), pct(interp_gen - interp_disc, interp_gen)],
        ["Baseline", f"{bl_events:,.0f}", human_bytes(bl_gen), pct(bl_gen, total_gen), pct(bl_gen - bl_disc, bl_gen)],
        ["Ion", f"{ion_events:,.0f}", human_bytes(ion_gen), pct(ion_gen, total_gen), pct(ion_gen - ion_disc, ion_gen)],
        ["IC stubs", f"{ic_events:,.0f}", human_bytes(ic_gen), pct(ic_gen, total_gen), pct(ic_gen - ic_disc, ic_gen)],
    ]

    ion_ic_gen = val("ion_ic_attach_bytes")
    ion_ic_disc = val("ion_ic_detach_bytes")
    ion_ic_events = val("ion_ic_attaches") + val("ion_ic_detaches")
    if ion_ic_events > 0:
        rows.append(["IC stubs (Ion)", f"{ion_ic_events:,.0f}", human_bytes(ion_ic_gen), pct(ion_ic_gen, total_gen), pct(ion_ic_gen - ion_ic_disc, ion_ic_gen)])
        total_events += ion_ic_events

    rows.append(["Total", f"{total_events:,.0f}", human_bytes(total_gen), "\u2014", "\u2014"])

    table = {
        "header": ["Tier", "Events", "Generated", "Share", "Retention"],
        "rows": rows,
    }
    json.dump(table, sys.stdout, indent=2, ensure_ascii=False)
    break
