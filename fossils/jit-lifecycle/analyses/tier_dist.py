#!/usr/bin/env python3
"""
Tier distribution over execution lifetime.

Divides the event stream into N buckets and tracks cumulative live bytes
per tier (baseline, ion, ic) at each bucket boundary. Output is suitable
for a stacked area chart showing how JIT code volume distributes across
tiers over the program lifetime.

IC events are split into baseline and ion engine variants when the
engine= tag is present; untagged events are assumed to be baseline.
"""
import json, sys, re

obs = json.load(sys.stdin)
events = []

RE_TS = re.compile(r'^ts=\d+\s+')
RE_COMPILE = re.compile(r'^jit-compile tier=(\w+) bytes=(\d+)')
RE_DISCARD = re.compile(r'^jit-discard tier=(\w+) bytes=(\d+)')
RE_IC_ATTACH = re.compile(
    r'^ic-attach kind=(\w+) code=(\d+)'
    r'(?:\s+aot=\d+)?'
    r'(?:\s+hash=(\d+))?'
    r'(?:\s+engine=(\w+))?'
)
RE_IC_DETACH = re.compile(
    r'^ic-detach kind=(\w+)'
    r'(?:\s+code=(\d+))?'
    r'(?:\s+hash=(\d+))?'
    r'(?:\s+engine=(\w+))?'
)

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    line = RE_TS.sub('', line)
    m = RE_COMPILE.match(line)
    if m:
        events.append(("compile", m.group(1), int(m.group(2)), None))
        continue
    m = RE_DISCARD.match(line)
    if m:
        events.append(("discard", m.group(1), int(m.group(2)), None))
        continue
    m = RE_IC_ATTACH.match(line)
    if m:
        h = m.group(3)
        engine = m.group(4) or "baseline"
        tier = "ic" if engine == "baseline" else "ic_ion"
        events.append(("compile", tier, int(m.group(2)), h))
        continue
    m = RE_IC_DETACH.match(line)
    if m:
        code_bytes = int(m.group(2)) if m.group(2) else 0
        h = m.group(3)
        engine = m.group(4) or "baseline"
        tier = "ic" if engine == "baseline" else "ic_ion"
        events.append(("discard", tier, code_bytes, h))

if not events:
    json.dump({"buckets": [], "peak": {}}, sys.stdout)
    sys.exit(0)

n = len(events)
num_buckets = 20
size = max(n // num_buckets, 1)

ic_hash_size = {}
for action, tier, sz, h in events:
    if action == "compile" and tier in ("ic", "ic_ion") and h:
        ic_hash_size[h] = sz

live = {"blinterp": 0, "baseline": 0, "ion": 0, "ic": 0, "ic_ion": 0}
peak = {"blinterp": 0, "baseline": 0, "ion": 0, "ic": 0, "ic_ion": 0}
buckets = []

for b in range(num_buckets):
    start = b * size
    end = n if b == num_buckets - 1 else (b + 1) * size
    for action, tier, sz, h in events[start:end]:
        if action == "compile":
            live[tier] = live.get(tier, 0) + sz
        else:
            dsz = sz if sz > 0 else ic_hash_size.get(h, 0)
            live[tier] = max(0, live.get(tier, 0) - dsz)
        peak[tier] = max(peak[tier], live.get(tier, 0))
    buckets.append({
        "bucket": b,
        "blinterp_bytes": live["blinterp"],
        "baseline_bytes": live["baseline"],
        "ion_bytes": live["ion"],
        "ic_bytes": live["ic"],
        "ic_ion_bytes": live["ic_ion"],
        "total_bytes": live["blinterp"] + live["baseline"] + live["ion"] + live["ic"] + live["ic_ion"],
    })

output = {
    "buckets": buckets,
    "peak": peak,
    "final": dict(live),
}

json.dump(output, sys.stdout)
