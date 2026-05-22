#!/usr/bin/env python3
import json, sys, re

obs = json.load(sys.stdin)

compiles = {"baseline": 0, "ion": 0, "blinterp": 0}
discards = {"baseline": 0, "ion": 0, "blinterp": 0}
compile_bytes = {"baseline": 0, "ion": 0, "blinterp": 0}
discard_bytes = {"baseline": 0, "ion": 0, "blinterp": 0}
ic_attaches = 0
ic_detaches = 0
ic_attach_bytes = 0
ic_detach_bytes = 0
ic_aot_attaches = 0
ic_aot_attach_bytes = 0
ic_jit_attaches = 0
ic_jit_attach_bytes = 0
ion_ic_attaches = 0
ion_ic_detaches = 0
ion_ic_attach_bytes = 0
ion_ic_detach_bytes = 0

RE_TS = re.compile(r'^ts=\d+\s+')
RE_IC_ATTACH = re.compile(
    r'^ic-attach kind=\w+ code=(\d+)'
    r'(?:\s+aot=(\d+))?'
    r'(?:\s+hash=\d+)?'
    r'(?:\s+engine=(\w+))?'
)
RE_IC_DETACH = re.compile(
    r'^ic-detach kind=\w+'
    r'(?:\s+code=(\d+))?'
    r'(?:\s+hash=\d+)?'
    r'(?:\s+engine=(\w+))?'
)

stderr = obs.get("stderr", [])
lines = stderr if isinstance(stderr, list) else stderr.splitlines()
for line in lines:
    line = RE_TS.sub('', line)
    m = re.match(r'^jit-compile tier=(\w+) bytes=(\d+)', line)
    if m:
        tier = m.group(1)
        sz = int(m.group(2))
        compiles[tier] = compiles.get(tier, 0) + 1
        compile_bytes[tier] = compile_bytes.get(tier, 0) + sz
        continue
    m = re.match(r'^jit-discard tier=(\w+) bytes=(\d+)', line)
    if m:
        tier = m.group(1)
        sz = int(m.group(2))
        discards[tier] = discards.get(tier, 0) + 1
        discard_bytes[tier] = discard_bytes.get(tier, 0) + sz
        continue
    m = RE_IC_ATTACH.match(line)
    if m:
        sz = int(m.group(1))
        aot = m.group(2)
        engine = m.group(3) or "baseline"
        if engine == "ion":
            ion_ic_attaches += 1
            ion_ic_attach_bytes += sz
        else:
            ic_attaches += 1
            ic_attach_bytes += sz
            if aot == "1":
                ic_aot_attaches += 1
                ic_aot_attach_bytes += sz
            else:
                ic_jit_attaches += 1
                ic_jit_attach_bytes += sz
        continue
    m = RE_IC_DETACH.match(line)
    if m:
        sz = int(m.group(1)) if m.group(1) else 0
        engine = m.group(2) or "baseline"
        if engine == "ion":
            ion_ic_detaches += 1
            ion_ic_detach_bytes += sz
        else:
            ic_detaches += 1
            ic_detach_bytes += sz

metrics = {
    "baseline_compiles": compiles["baseline"],
    "baseline_compile_bytes": compile_bytes["baseline"],
    "ion_compiles": compiles["ion"],
    "ion_compile_bytes": compile_bytes["ion"],
    "baseline_discards": discards["baseline"],
    "baseline_discard_bytes": discard_bytes["baseline"],
    "ion_discards": discards["ion"],
    "ion_discard_bytes": discard_bytes["ion"],
    "ic_attaches": ic_attaches,
    "ic_detaches": ic_detaches,
    "ic_attach_bytes": ic_attach_bytes,
    "ic_detach_bytes": ic_detach_bytes,
    "ion_ic_attaches": ion_ic_attaches,
    "ion_ic_detaches": ion_ic_detaches,
    "ion_ic_attach_bytes": ion_ic_attach_bytes,
    "ion_ic_detach_bytes": ion_ic_detach_bytes,
    "ic_aot_attaches": ic_aot_attaches,
    "ic_aot_attach_bytes": ic_aot_attach_bytes,
    "ic_jit_attaches": ic_jit_attaches,
    "ic_jit_attach_bytes": ic_jit_attach_bytes,
    "blinterp_compiles": compiles["blinterp"],
    "blinterp_compile_bytes": compile_bytes["blinterp"],
    "blinterp_discards": discards["blinterp"],
    "blinterp_discard_bytes": discard_bytes["blinterp"],
    "total_jit_bytes_generated": (
        compile_bytes["blinterp"] + compile_bytes["baseline"]
        + compile_bytes["ion"]
        + ic_attach_bytes + ion_ic_attach_bytes
    ),
}

json.dump(metrics, sys.stdout)
