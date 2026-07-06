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

if "score-internal" in lookup:
    reps = lookup["score-internal"]["replicates"]
    metrics["score_min"] = min(reps)
    metrics["score_max"] = max(reps)

if "total" in lookup:
    metrics["total_ms"] = lookup["total"]["value"]

if "cpuTime" in lookup:
    metrics["cpu_time_ms"] = lookup["cpuTime"]["value"]

for gc in ("perfstats-MajorGC", "perfstats-MinorGC", "perfstats-NonIdleMajorGC"):
    if gc in lookup:
        key = gc.replace("perfstats-", "").lower() + "_ms"
        metrics[key] = lookup[gc]["value"]

# Cold vs warm split: replicate 0 of each subtest is the first Speedometer
# iteration, where cold-code effects (IC warmup, tiering, startup) live.
totals = [s for s in subtests
          if s["name"].endswith("/total") and s.get("replicates")]
if totals:
    metrics["cold_iter_ms"] = sum(s["replicates"][0] for s in totals)
    metrics["warm_iter_ms"] = sum(
        sum(s["replicates"][1:]) / len(s["replicates"][1:])
        for s in totals if len(s["replicates"]) > 1)

json.dump(metrics, sys.stdout)
