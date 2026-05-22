#!/usr/bin/env python3
"""Per-stub size distribution for histogram plotting.

Outputs:
  - size_distribution: list of individual stub sizes (for histogram)
  - by_kind: dict of kind -> {total_bytes, count, avg}
  - summary scalars: total_bytes, total_stubs, avg_stub_size
"""
import json, sys, re
from collections import defaultdict

obs = json.load(sys.stdin)
sizes_by_kind = defaultdict(list)
all_sizes = []

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    m = re.match(r'^(?:ts=\d+ )?ic-attach kind=(\w+) code=(\d+)', line)
    if not m:
        continue
    kind = m.group(1)
    code_size = int(m.group(2))
    sizes_by_kind[kind].append(code_size)
    all_sizes.append(code_size)

metrics = {}

for kind in sorted(sizes_by_kind, key=lambda k: -sum(sizes_by_kind[k])):
    s = sizes_by_kind[kind]
    metrics[f"bytes_{kind}"] = sum(s)
    metrics[f"avg_{kind}"] = round(sum(s) / len(s), 1)
    metrics[f"count_{kind}"] = len(s)

metrics["total_bytes"] = sum(all_sizes)
metrics["total_stubs"] = len(all_sizes)
metrics["avg_stub_size"] = round(sum(all_sizes) / len(all_sizes), 1) if all_sizes else 0

metrics["size_distribution"] = sorted(all_sizes)

json.dump(metrics, sys.stdout)
