#!/usr/bin/env python3
"""Parse AOT timing instrumentation lines from a single observation's stderr.

Fossil contract: read one Observation JSON from stdin, emit flat metrics JSON
to stdout. Fossil folds across iterations automatically.

Output metrics (all in microseconds):
    aot_load_interp_us, aot_load_selfhosted_us, aot_load_ics_us
    jit_gen_interp_us,  jit_gen_selfhosted_us,  jit_gen_ics_us
    jit_gen_baseline_us
    ics_compiled_count, ics_cached_count
"""

import json
import re
import sys

LINE_RE = re.compile(
    r"^(aot-load|jit-gen)\s+"
    r"component=(\S+)\s+"
    r"us=(\d+(?:\.\d+)?)"
)

CACHED_RE = re.compile(r"^ics-cached\b")

obs = json.load(sys.stdin)
stderr = obs.get("stderr", [])
if isinstance(stderr, str):
    stderr = stderr.splitlines()

totals = {}
counts = {}
ics_cached = 0

for line in stderr:
    line = line.strip()

    if CACHED_RE.match(line):
        ics_cached += 1
        continue

    m = LINE_RE.match(line)
    if not m:
        continue

    event = m.group(1)
    component = m.group(2)
    us = float(m.group(3))

    key = f"{event.replace('-', '_')}_{component}_us"
    totals[key] = totals.get(key, 0.0) + us
    count_key = f"{event.replace('-', '_')}_{component}_count"
    counts[count_key] = counts.get(count_key, 0) + 1

metrics = {}
metrics.update(totals)
metrics.update(counts)
if ics_cached > 0:
    metrics["ics_cached_count"] = ics_cached

json.dump(metrics, sys.stdout)
