#!/usr/bin/env python3
import json, sys, re

obs = json.load(sys.stdin)
kinds = {}
total = 0
total_bytes = 0
aot_hits = 0
unique_hashes = set()

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    m = re.match(r'^(?:ts=\d+ )?ic-attach kind=(\w+) code=(\d+) aot=(\d+)(?: hash=(\d+))?', line)
    if not m:
        continue
    kind = m.group(1)
    code_size = int(m.group(2))
    is_aot = int(m.group(3))
    h = m.group(4)
    kinds[kind] = kinds.get(kind, 0) + 1
    total += 1
    total_bytes += code_size
    if is_aot:
        aot_hits += 1
    if h:
        unique_hashes.add((kind, int(h)))

metrics = {}
for kind, count in sorted(kinds.items(), key=lambda x: -x[1]):
    metrics[f"kind_{kind}"] = count

metrics["total_attaches"] = total
metrics["total_code_bytes"] = total_bytes
metrics["aot_hits"] = aot_hits
metrics["aot_hit_rate"] = round(aot_hits / total, 4) if total > 0 else 0
metrics["unique_kinds"] = len(kinds)
metrics["unique_stubs"] = len(unique_hashes)

json.dump(metrics, sys.stdout)
