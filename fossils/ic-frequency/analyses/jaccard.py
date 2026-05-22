#!/usr/bin/env python3
"""Extract stub identity sets and frequency data for Jaccard and coverage analysis.

Supports proc= field filtering via PROC_FILTER env var (e.g. PROC_FILTER=content).
When set, only ic-attach lines matching that process type are counted.

Outputs:
  - unique_hashes: comma-joined "kind:hash" strings (Tag, for set operations)
  - stub_freqs: semicolon-joined "kind:hash=count" (Tag, for frequency-weighted coverage)
  - unique_count: number of unique stubs
  - total_attaches: total attach events
"""
import json, os, sys, re
from collections import Counter

proc_filter = os.environ.get("PROC_FILTER", "content")
RE = re.compile(
    r'^(?:ts=\d+ )?ic-attach kind=(\w+) code=(\d+) aot=(\d+) hash=(\d+)(?:\s+proc=(\w+))?'
)

obs = json.load(sys.stdin)
stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()

freq = Counter()
for line in lines:
    m = RE.match(line)
    if not m:
        continue
    if proc_filter and m.group(5) and m.group(5) != proc_filter:
        continue
    freq[f"{m.group(1)}:{m.group(4)}"] += 1

metrics = {
    "unique_hashes": ",".join(sorted(freq.keys())),
    "stub_freqs": ";".join(f"{k}={v}" for k, v in freq.most_common()),
    "unique_count": len(freq),
    "total_attaches": sum(freq.values()),
}

json.dump(metrics, sys.stdout)
