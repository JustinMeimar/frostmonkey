#!/usr/bin/env python3
import json, sys

obs = json.load(sys.stdin)
stdout = obs.get("stdout", "")
raptor = json.loads("\n".join(stdout) if isinstance(stdout, list) else stdout)
subtests = raptor["suites"][0]["subtests"]

lookup = {s["name"]: s for s in subtests}

metrics = {}

if "score" in lookup:
    metrics["score"] = lookup["score"]["value"]

GEOMETRIC_SUFFIX = "-Geometric"
WORKER_PREFIXES = ["bomb-workers-", "segmentation-"]

for name, sub in lookup.items():
    if name.endswith(GEOMETRIC_SUFFIX):
        category = name[: -len(GEOMETRIC_SUFFIX)]
        metrics[f"{category}_geometric"] = sub["value"]
        continue

    for prefix in WORKER_PREFIXES:
        if name.startswith(prefix):
            workload = name[len(prefix):]
            category = prefix.rstrip("-")
            key = f"{category}_{workload}".replace("-", "_")
            metrics[key] = sub["value"]

json.dump(metrics, sys.stdout)
