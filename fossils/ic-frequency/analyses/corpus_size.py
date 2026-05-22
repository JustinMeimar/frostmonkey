#!/usr/bin/env python3
"""
Coverage vs. corpus size analysis for AOT IC stub selection.

Ranks unique stub bodies by attach frequency, then accumulates both
coverage (fraction of runtime attaches) and corpus bytes as each stub
is added. Directly answers: how many bytes of stubs must the AOT
binary ship to reach a given coverage target?

Output:
  - cum_bytes: cumulative corpus byte array (one entry per unique stub)
  - cum_coverage: cumulative coverage fraction array
  - thresholds: {90,95,99} -> {stubs, bytes} needed to reach that coverage
  - total scalars for context
"""
import json, sys, re
from collections import Counter

obs = json.load(sys.stdin)
stubs = Counter()
stub_bytes = {}

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    m = re.match(
        r'^(?:ts=\d+ )?ic-attach kind=(\w+) code=(\d+)'
        r'(?:\s+aot=\d+)?'
        r'(?:\s+hash=(\d+))?',
        line,
    )
    if not m or not m.group(3):
        continue
    key = (m.group(1), int(m.group(3)))
    stubs[key] += 1
    stub_bytes[key] = int(m.group(2))

total_attaches = sum(stubs.values())
if total_attaches == 0:
    json.dump({"cum_bytes": [], "cum_coverage": [], "thresholds": {}}, sys.stdout)
    sys.exit(0)

ranked = stubs.most_common()

cum_bytes = []
cum_coverage = []
running_bytes = 0
running_attaches = 0

for key, count in ranked:
    running_bytes += stub_bytes[key]
    running_attaches += count
    cum_bytes.append(running_bytes)
    cum_coverage.append(running_attaches / total_attaches)

thresholds = {}
for target in [90, 95, 99]:
    frac = target / 100.0
    for i, cov in enumerate(cum_coverage):
        if cov >= frac:
            thresholds[str(target)] = {
                "stubs": i + 1,
                "bytes": cum_bytes[i],
            }
            break

json.dump({
    "cum_bytes": cum_bytes,
    "cum_coverage": cum_coverage,
    "total_attaches": total_attaches,
    "total_unique_stubs": len(ranked),
    "total_corpus_bytes": running_bytes,
    "thresholds": thresholds,
}, sys.stdout)
