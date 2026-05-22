#!/usr/bin/env python3
"""Extract unique stub identity set for cross-benchmark overlap analysis.

Outputs:
  - unique_hashes: comma-joined "kind:hash" strings (for set reconstruction)
  - unique_count: number of unique stubs
  - total_attaches: total attach events
"""
import json, sys, re

obs = json.load(sys.stdin)
seen = set()
total = 0

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    m = re.match(r'^(?:ts=\d+ )?ic-attach kind=(\w+) code=(\d+) aot=(\d+) hash=(\d+)', line)
    if not m:
        continue
    total += 1
    key = f"{m.group(1)}:{m.group(4)}"
    seen.add(key)

metrics = {
    "unique_hashes": ",".join(sorted(seen)),
    "unique_count": len(seen),
    "total_attaches": total,
}

json.dump(metrics, sys.stdout)
