#!/usr/bin/env python3
"""Parse browsertime pageload timing metrics from stdout.

Browsertime emits a line like:
  [timestamp] INFO: <url> TTFB: 174ms, firstPaint: 887ms, FCP: 887ms,
  DOMContentLoaded: 1.11s, LCP: 1.37s, CPUBenchmark: 60ms, Load: 4.57s

Extracts key metrics in milliseconds.
"""
import json, sys, re

obs = json.load(sys.stdin)
stdout = obs.get("stdout", [])
lines = stdout if isinstance(stdout, list) else stdout.splitlines()

def parse_time(s):
    """Convert '174ms' or '1.11s' to float milliseconds."""
    s = s.strip()
    if s.endswith("ms"):
        return float(s[:-2])
    if s.endswith("s"):
        return float(s[:-1]) * 1000
    return float(s)

FIELDS = {
    "TTFB": "ttfb_ms",
    "firstPaint": "first_paint_ms",
    "FCP": "fcp_ms",
    "DOMContentLoaded": "dom_content_loaded_ms",
    "LCP": "lcp_ms",
    "Load": "load_ms",
}

metrics = {}
for line in lines:
    if "INFO:" not in line or "TTFB:" not in line:
        continue
    for label, key in FIELDS.items():
        m = re.search(rf'{label}:\s*([0-9.]+(?:ms|s))', line)
        if m:
            metrics[key] = parse_time(m.group(1))
    break

if not metrics:
    metrics = {v: 0.0 for v in FIELDS.values()}

json.dump(metrics, sys.stdout)
