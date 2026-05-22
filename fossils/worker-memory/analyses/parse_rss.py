#!/usr/bin/env python3
import json, sys, re

obs = json.load(sys.stdin)

stderr = obs.get("stderr", [])
stdout = obs.get("stdout", [])
lines_err = stderr if isinstance(stderr, list) else stderr.splitlines()
lines_out = stdout if isinstance(stdout, list) else stdout.splitlines()

peak_rss_kb = 0
steady_rss_kb = 0
num_workers = 0

for line in lines_err:
    m = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", line)
    if m:
        peak_rss_kb = int(m.group(1))

for line in lines_out:
    m = re.match(r"workers=(\d+)\s+rss_kb=(\d+)", line)
    if m:
        num_workers = int(m.group(1))
        steady_rss_kb = int(m.group(2))

metrics = {
    "peak_rss_kb": peak_rss_kb,
    "steady_rss_kb": steady_rss_kb,
    "num_workers": num_workers,
}

json.dump(metrics, sys.stdout)
