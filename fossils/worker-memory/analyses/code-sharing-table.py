#!/usr/bin/env python3
"""
Post-processor: reads fossil analyze JSON (both variants) from stdin,
outputs fossil-table format JSON for the paper figure.

Usage:
  fossil analyze --project spidermonkey worker-memory \
    | python3 analyses/code-sharing-table.py > /path/to/figures/jit-code-sharing.json
"""
import json, sys

data = json.load(sys.stdin)

def val(variant, key):
    return data[variant][key]["mean"]

def kb(v):
    return f"{v:,.0f} KB" if v >= 1 else "0 KB"

def reduction(baseline, aot):
    if baseline == 0:
        return "--"
    pct = (1 - aot / baseline) * 100
    if abs(pct) < 0.5:
        return "0%"
    return f"{pct:.0f}%"

noaot = "octane-worker"
aot = "octane-worker-aot"

ic_priv = val(noaot, "ic_runtime_kb")
ic_priv_aot = val(aot, "ic_runtime_kb")
ic_corpus = val(aot, "ic_aot_corpus_kb")
bl = val(noaot, "bl_compile_kb")
bl_aot = val(aot, "bl_compile_kb")
priv = val(noaot, "private_jit_kb")
priv_aot = val(aot, "private_jit_kb")

json.dump({
    "header": ["Metric", "Non-AOT", "AOT", "Reduction"],
    "rows": [
        ["IC stubs (private)", kb(ic_priv), kb(ic_priv_aot), reduction(ic_priv, ic_priv_aot)],
        ["IC stubs (shared .text)", "--", kb(ic_corpus), "--"],
        ["Baseline compiles", kb(bl), kb(bl_aot), reduction(bl, bl_aot)],
        ["Private JIT total", kb(priv), kb(priv_aot), reduction(priv, priv_aot)],
    ],
}, sys.stdout, indent=2)
sys.stdout.write("\n")
