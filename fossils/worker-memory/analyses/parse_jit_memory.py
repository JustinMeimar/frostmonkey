#!/usr/bin/env python3
import json, sys, re

obs = json.load(sys.stdin)

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()

blinterp_runtime_bytes = 0
blinterp_aot_bytes = 0
bl_compile_bytes = 0
bl_compile_count = 0

ic_runtime_bytes = 0
ic_runtime_count = 0
ic_aot_attach_count = 0
ic_detach_runtime_bytes = 0

aot_corpus = {}
aot_hashes = set()

re_blinterp = re.compile(r"jit-compile tier=blinterp bytes=(\d+) aot=(\d)")
re_compile = re.compile(r"jit-compile tier=baseline bytes=(\d+)")
re_attach = re.compile(r"ic-attach kind=\w+ code=(\d+) aot=(\d) hash=(\d+)")
re_detach = re.compile(r"ic-detach kind=\w+ code=(\d+) hash=(\d+)")

for line in lines:
    m = re_blinterp.search(line)
    if m:
        b, aot = int(m.group(1)), int(m.group(2))
        if aot:
            blinterp_aot_bytes += b
        else:
            blinterp_runtime_bytes += b
        continue

    m = re_compile.search(line)
    if m:
        bl_compile_bytes += int(m.group(1))
        bl_compile_count += 1
        continue

    m = re_attach.search(line)
    if m:
        b, aot, h = int(m.group(1)), int(m.group(2)), m.group(3)
        if aot:
            ic_aot_attach_count += 1
            aot_corpus[h] = b
            aot_hashes.add(h)
        else:
            ic_runtime_bytes += b
            ic_runtime_count += 1
        continue

    m = re_detach.search(line)
    if m:
        b, h = int(m.group(1)), m.group(2)
        if h not in aot_hashes:
            ic_detach_runtime_bytes += b

def kb(b):
    return round(b / 1024, 1)

ic_aot_corpus_bytes = sum(aot_corpus.values())

json.dump({
    "blinterp_runtime_kb": kb(blinterp_runtime_bytes),
    "blinterp_aot_kb": kb(blinterp_aot_bytes),
    "bl_compile_kb": kb(bl_compile_bytes),
    "bl_compile_count": bl_compile_count,
    "ic_runtime_kb": kb(ic_runtime_bytes),
    "ic_runtime_count": ic_runtime_count,
    "ic_aot_corpus_kb": kb(ic_aot_corpus_bytes),
    "ic_aot_corpus_count": len(aot_corpus),
    "ic_aot_attach_count": ic_aot_attach_count,
}, sys.stdout)
