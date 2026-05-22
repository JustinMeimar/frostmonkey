#!/usr/bin/env python3
"""
Ranked IC stub distribution for CDF plotting.

Outputs a JSON list of attach counts sorted by rank (highest first).
The figure script computes the cumulative sum for the CDF curve.
"""
import json, sys, re
from collections import Counter

obs = json.load(sys.stdin)
stubs = Counter()

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    m = re.match(r'^(?:ts=\d+ )?ic-attach kind=(\w+) code=(\d+) aot=(\d+) hash=(\d+)', line)
    if not m:
        continue
    key = (m.group(1), int(m.group(4)))
    stubs[key] += 1

if not stubs:
    json.dump({"ranked_counts": []}, sys.stdout)
    sys.exit(0)

ranked = [count for _, count in stubs.most_common()]

json.dump({"ranked_counts": ranked}, sys.stdout)
