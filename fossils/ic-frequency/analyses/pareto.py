#!/usr/bin/env python3
"""
Pareto distribution of IC stub bodies.

Groups ic-attach events by their CacheIR content hash, ranks by frequency,
and computes cumulative coverage. Output shows how many unique stub bodies
account for what fraction of total attaches.
"""
import json, sys, re
from collections import Counter

obs = json.load(sys.stdin)
stubs = Counter()
stub_bytes = {}
stub_aot = {}
corpus = {}  # (kind, hash) -> corpus_idx

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    # Parse corpus entries (emitted at startup when AOT ICs are loaded)
    m = re.match(r'^(?:ts=\d+ )?ic-corpus kind=(\w+) hash=(\d+) code=(\d+) idx=(\d+)', line)
    if m:
        key = (m.group(1), int(m.group(2)))
        corpus[key] = int(m.group(4))
        continue
    m = re.match(r'^(?:ts=\d+ )?ic-attach kind=(\w+) code=(\d+) aot=(\d+) hash=(\d+)', line)
    if not m:
        continue
    kind = m.group(1)
    code_size = int(m.group(2))
    is_aot = int(m.group(3))
    h = int(m.group(4))
    key = (kind, h)
    stubs[key] += 1
    stub_bytes[key] = code_size
    if is_aot:
        stub_aot[key] = True

total_attaches = sum(stubs.values())
unique_count = len(stubs)

if total_attaches == 0:
    json.dump({"error": "no ic-attach events with hash field"}, sys.stdout)
    sys.exit(0)

ranked = stubs.most_common()

cumulative = []
running = 0
for i, (key, count) in enumerate(ranked):
    running += count
    cumulative.append(running / total_attaches)

def coverage_at(n):
    if n >= len(cumulative):
        return 1.0
    return cumulative[n - 1]

aot_covered = sum(count for key, count in ranked if key in stub_aot)

metrics = {
    "total_attaches": total_attaches,
    "unique_stubs": unique_count,
    "reuse_factor": round(total_attaches / unique_count, 2),
    "top_10_coverage": round(coverage_at(10), 4),
    "top_25_coverage": round(coverage_at(25), 4),
    "top_50_coverage": round(coverage_at(50), 4),
    "top_100_coverage": round(coverage_at(100), 4),
    "top_200_coverage": round(coverage_at(200), 4),
    "top_500_coverage": round(coverage_at(500), 4),
    "aot_corpus_coverage": round(aot_covered / total_attaches, 4),
    "aot_corpus_stubs": len(stub_aot),
    "corpus_size": len(corpus),
}

# Encode top_20 as a single string so fossil's fold() passes it through
# rather than trying to compute mean/stddev on each field.
top_lines = []
for i, (key, count) in enumerate(ranked[:20]):
    kind, h = key
    idx = corpus.get(key)
    idx_s = str(idx) if idx is not None else "-"
    aot = "Y" if key in stub_aot else "N"
    top_lines.append(
        f"{i+1:2d}. {kind:12s} hash={h:>10d}  n={count:5d}  "
        f"bytes={stub_bytes[key]:3d}  aot={aot}  idx={idx_s:>4s}  "
        f"cum={cumulative[i]:.3f}"
    )
metrics["top_20"] = "\n".join(top_lines)

json.dump(metrics, sys.stdout)
