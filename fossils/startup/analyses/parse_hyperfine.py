#!/usr/bin/env python3
import json, sys

obs = json.load(sys.stdin)
stdout = obs.get("stdout", "")
hf = json.loads("\n".join(stdout) if isinstance(stdout, list) else stdout)

r = hf["results"][0]

metrics = {
    "mean_ms": r["mean"] * 1000,
    "stddev_ms": r["stddev"] * 1000,
    "median_ms": r["median"] * 1000,
    "min_ms": r["min"] * 1000,
    "max_ms": r["max"] * 1000,
    "user_ms": r["user"] * 1000,
    "system_ms": r["system"] * 1000,
}

if "memory_usage_byte" in r and r["memory_usage_byte"]:
    mem = [b for b in r["memory_usage_byte"] if b > 0]
    if mem:
        metrics["peak_mem_kb"] = max(mem) / 1024

json.dump(metrics, sys.stdout)
