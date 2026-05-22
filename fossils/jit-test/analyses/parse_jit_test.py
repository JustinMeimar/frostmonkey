#!/usr/bin/env python3
import json, sys, re

obs = json.load(sys.stdin)
metrics = {}
failures = []
timeouts = []

section = None
stdout = obs.get("stdout", [])
lines = stdout if isinstance(stdout, list) else stdout.splitlines()
for line in lines:
    if line == "FAILURES:":
        section = "failures"
        continue
    elif line == "TIMEOUTS:":
        section = "timeouts"
        continue
    elif line.startswith("PASSED ALL"):
        metrics["passed_all"] = True
        section = None
        continue

    if section == "failures" and line.startswith("    "):
        failures.append(line.strip())
    elif section == "timeouts" and line.startswith("    "):
        timeouts.append(line.strip())
    else:
        section = None

metrics["exit_code"] = obs.get("exit_code", -1)
metrics["failure_count"] = len(failures)
metrics["timeout_count"] = len(timeouts)

if failures:
    metrics["failures"] = failures
if timeouts:
    metrics["timeouts"] = timeouts

json.dump(metrics, sys.stdout)
