#!/usr/bin/env python3
import json, sys, re

obs = json.load(sys.stdin)
attaches = {}
detaches = {}

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    m = re.match(r'^(?:ts=\d+ )?ic-attach kind=(\w+)', line)
    if m:
        kind = m.group(1)
        attaches[kind] = attaches.get(kind, 0) + 1
        continue
    m = re.match(r'^(?:ts=\d+ )?ic-detach kind=(\w+)', line)
    if m:
        kind = m.group(1)
        detaches[kind] = detaches.get(kind, 0) + 1

all_kinds = sorted(set(attaches) | set(detaches), key=lambda k: -(detaches.get(k, 0)))
total_a = 0
total_d = 0
rows = []
for kind in all_kinds:
    a = attaches.get(kind, 0)
    d = detaches.get(kind, 0)
    total_a += a
    total_d += d
    rows.append({
        "kind": kind,
        "attach": a,
        "detach": d,
        "churn": round(d / a, 3) if a > 0 else 0,
    })

output = {
    "by_kind": rows,
    "total_attaches": total_a,
    "total_detaches": total_d,
    "churn_rate": round(total_d / total_a, 3) if total_a > 0 else 0,
}

json.dump(output, sys.stdout)
