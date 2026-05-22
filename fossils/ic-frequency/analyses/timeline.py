#!/usr/bin/env python3
"""
IC population timeline.

Tracks attach/detach events over time. Native code bytes are only
available from attach events (detach events identify stubs by hash).
We track population count (attach - detach) and cumulative bytes generated.
"""
import json, sys, re

obs = json.load(sys.stdin)
events = []

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    m = re.match(r'^(?:ts=\d+ )?ic-attach kind=(\w+) code=(\d+)', line)
    if m:
        events.append(("attach", m.group(1), int(m.group(2))))
        continue
    m = re.match(r'^(?:ts=\d+ )?ic-detach kind=(\w+)', line)
    if m:
        events.append(("detach", m.group(1), 0))

if not events:
    json.dump({}, sys.stdout)
    sys.exit(0)

n = len(events)
buckets = 10
size = max(n // buckets, 1)

rows = []
population = 0
total_generated = 0
for b in range(buckets):
    start = b * size
    end = n if b == buckets - 1 else (b + 1) * size
    chunk = events[start:end]
    a = sum(1 for e in chunk if e[0] == "attach")
    d = sum(1 for e in chunk if e[0] == "detach")
    a_bytes = sum(e[2] for e in chunk if e[0] == "attach")
    population += a - d
    total_generated += a_bytes
    rows.append({
        "bucket": f"p{b}",
        "attach": a,
        "detach": d,
        "net": a - d,
        "population": population,
        "generated_bytes": total_generated,
    })

output = {
    "timeline": rows,
    "total_events": n,
    "final_population": population,
    "total_generated_bytes": total_generated,
}

json.dump(output, sys.stdout)
