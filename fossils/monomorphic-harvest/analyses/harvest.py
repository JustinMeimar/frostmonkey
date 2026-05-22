#!/usr/bin/env python3
import json, sys, re

obs = json.load(sys.stdin)

RE_HARVEST = re.compile(
    r"\[BaselineAOT\]\s+Harvested\s+(\d+)/(\d+)\s+monomorphic IC profiles for '([^']+)'\s+\(key=(\d+)\)"
)
RE_SUMMARY = re.compile(
    r'\[BaselineAOT\]\s+IC profile harvest complete:\s+(\d+)\s+functions with profiles'
)

per_function = []
total_mono = 0
total_ics = 0
num_functions = 0

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    m = RE_HARVEST.search(line)
    if m:
        mono = int(m.group(1))
        total = int(m.group(2))
        name = m.group(3)
        key = int(m.group(4))
        ratio = round(mono / total, 4) if total > 0 else 0
        per_function.append({
            "name": name,
            "key": key,
            "monomorphic": mono,
            "total_ics": total,
            "ratio": ratio,
        })
        total_mono += mono
        total_ics += total
        continue
    m = RE_SUMMARY.search(line)
    if m:
        num_functions = int(m.group(1))

per_function.sort(key=lambda x: x["ratio"], reverse=True)

metrics = {
    "functions_with_profiles": num_functions,
    "total_monomorphic": total_mono,
    "total_ics": total_ics,
    "aggregate_ratio": round(total_mono / total_ics, 4) if total_ics > 0 else 0,
    "per_function": per_function,
}

json.dump(metrics, sys.stdout)
