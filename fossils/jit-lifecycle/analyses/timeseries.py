#!/usr/bin/env python3
"""
JIT code lifecycle timeseries for scatter visualization.

Each event represents a JitCode artifact allocation (compile/ic-attach).
Output structure:
  - ts_us: timestamp array (microseconds since JIT init epoch)
  - bytes: code size array
  - tier: category string array (baseline, ion, ic, ic_ion)
  - action: event type array (compile, ic-attach)
  - total_events: count

Parallel arrays avoid the List-of-Maps folding overhead in fossil's
Quantity system and keep the figure script simple.
"""
import json, sys, re

RE_TS = re.compile(r'^ts=(\d+)\s+')
RE_COMPILE = re.compile(r'^jit-compile tier=(\w+) bytes=(\d+)')
RE_IC_ATTACH = re.compile(
    r'^ic-attach kind=(\w+) code=(\d+)'
    r'(?:\s+aot=\d+)?'
    r'(?:\s+hash=\d+)?'
    r'(?:\s+engine=(\w+))?'
)
obs = json.load(sys.stdin)
ts_us = []
bytes_arr = []
tier_arr = []
action_arr = []

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    ts = 0
    m = RE_TS.match(line)
    if m:
        ts = int(m.group(1))
        line = line[m.end():]

    m = RE_COMPILE.match(line)
    if m:
        ts_us.append(ts)
        bytes_arr.append(int(m.group(2)))
        tier_arr.append(m.group(1))
        action_arr.append("compile")
        continue
    m = RE_IC_ATTACH.match(line)
    if m:
        engine = m.group(3) or "baseline"
        ts_us.append(ts)
        bytes_arr.append(int(m.group(2)))
        tier_arr.append("ic" if engine == "baseline" else "ic_ion")
        action_arr.append("ic-attach")

json.dump({
    "ts_us": ts_us,
    "bytes": bytes_arr,
    "tier": tier_arr,
    "action": action_arr,
    "total_events": len(ts_us),
}, sys.stdout)
