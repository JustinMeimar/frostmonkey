#!/usr/bin/env python3
import json, sys, re

obs = json.load(sys.stdin)
metrics = {}
stdout = obs.get("stdout", [])
lines = stdout if isinstance(stdout, list) else stdout.splitlines()
for line in lines:
    if m := re.match(r'^(\w[\w\s]*\w)\s*:\s*([\d.]+)\s*$', line):
        metrics[m.group(1).lower().replace(" ", "_")] = float(m.group(2))
    elif m := re.match(r'^Score\s*\(version \d+\)\s*:\s*(\d+)', line):
        metrics["score"] = int(m.group(1))
    elif m := re.match(r'^Score:\s*(\d+)', line):
        metrics["score"] = int(m.group(1))

json.dump(metrics, sys.stdout)
