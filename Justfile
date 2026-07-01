
DEFAULT_BUILD := "build-shell-release-aot"
BENCH_CPU := "2"
BROWSER_AOT := "build-browser-release-aot/dist/bin/firefox"
BROWSER_DEBUG_AOT := "build-browser-debug-aot/dist/bin/firefox"
IC_CORPI := "../frostmonkey/ic-corpi"
PGO_DIR := "/tmp/frostmonkey-pgo"
PGO_BUDGET := "65536"
PGO_WORKLOAD := "js/src/octane/run.js"

##~---- Build / Bootstrap ----~##

build TARGET=DEFAULT_BUILD:
    python3 drive.py build --build={{TARGET}}

bootstrap TARGET=DEFAULT_BUILD:
    python3 drive.py bootstrap --build={{TARGET}}

use BUILD:
    #!/usr/bin/env bash
    target="{{BUILD}}/dist/bin/js"
    [ -f "$target" ] || { echo "Error: $target not found"; exit 1; }
    ln -sfn "$target" jsshell
    echo "jsshell -> $target"

clean-aot:
    cp js/src/jit/AOTBaselineStub.S js/src/jit/AOTBaseline.S
    echo "Reset AOTBaseline.S to empty stub"

##~---- Run / Debug / Test ----~##

run FILE *FLAGS:
    ./jsshell --aot {{FLAGS}} --blinterp-eager --no-baseline -f {{FILE}}

debug FILE *FLAGS:
    gdb --args ./jsshell --aot {{FLAGS}} --blinterp-eager --no-baseline -f {{FILE}}

debug-expr EXPR *FLAGS:
    gdb --args ./jsshell --aot {{FLAGS}} --blinterp-eager --no-baseline -e "{{EXPR}}"

test *ARGS:
    cd js/src && python3 jit-test/jit_test.py --args="--aot --enforce-aot-ics" ../../jsshell {{ARGS}}

##~---- IC Corpus ----~##

collect-ics FILE:
    AOT_ICS_LOG_UNSEEN=1 AOT_ICS_DIR=js/src/ics \
    ./jsshell --aot --enforce-aot-ics -f {{FILE}}

collect-ics-browser:
    JIT_OPTION_useAOTInterp=true \
    JIT_OPTION_useAOTSelfHosted=true \
    JIT_OPTION_useAOTICs=true \
    JIT_OPTION_enforceAOTICs=true \
    AOT_ICS_LOG_UNSEEN=1 AOT_ICS_DIR=js/src/ics \
    MOZ_DISABLE_CONTENT_SANDBOX=1 \
    ./{{BROWSER_AOT}} --no-remote

use-ics CORPUS:
    #!/usr/bin/env bash
    src="{{IC_CORPI}}/{{CORPUS}}"
    dest="js/src/ics"
    [ -d "$src" ] || { echo "Error: $src not found"; exit 1; }
    find "$dest" -maxdepth 1 -name 'IC-*' -delete
    count=0
    for f in "$src"/IC-*; do
        [ -f "$f" ] || continue
        ln -s "$(realpath "$f")" "$dest/$(basename "$f")"
        count=$((count + 1))
    done
    echo "$count ICs symlinked from $src -> $dest"

move-ics:
    #!/usr/bin/env bash
    count=$(find . -maxdepth 1 -name 'IC-*' | wc -l)
    echo "Moving $count IC files to js/src/ics/ ..."
    find . -maxdepth 1 -name 'IC-*' -print0 | xargs -0 -P4 mv -t js/src/ics/
    echo "Done"

clean-ics:
    #!/usr/bin/env bash
    count=$(find . -maxdepth 1 -name 'IC-*' | wc -l)
    echo "Deleting $count IC files from CWD ..."
    find . -maxdepth 1 -name 'IC-*' -delete
    echo "Done"

##~---- Diff ----~##

view-rolling-diff:
    git diff 8ded3583f3587f130f1af9 | delta --side-by-side
    #git diff 8ded3583f3587f130f1af9 HEAD | delta --side-by-side

get-rolling-diff:
    git diff 8ded3583f358 HEAD

##~---- Browser ----~##

browser *FLAGS:
    JIT_OPTION_useAOTInterp=true \
    JIT_OPTION_useAOTSelfHosted=true \
    JIT_OPTION_useAOTICs=true \
    {{FLAGS}} \
    MOZ_DISABLE_CONTENT_SANDBOX=1 \
    ./{{BROWSER_AOT}} --no-remote

gdb-browser:
    MOZ_CRASHREPORTER_DISABLE=1 \
    JIT_OPTION_useAOTInterp=true \
    JIT_OPTION_useAOTSelfHosted=true \
    JIT_OPTION_useAOTICs=true \
    MOZ_DISABLE_CONTENT_SANDBOX=1 \
    gdb --args ./{{BROWSER_AOT}} --no-remote

debug-browser:
    #!/usr/bin/env bash
    echo "Content processes will pause at startup. Attach gdb with:"
    echo "  gdb -p <PID>"
    echo ""
    JIT_OPTION_useAOTInterp=true \
    JIT_OPTION_useAOTSelfHosted=true \
    JIT_OPTION_useAOTICs=true \
    MOZ_DISABLE_CONTENT_SANDBOX=1 \
    MOZ_DEBUG_CHILD_PROCESS=1 \
    ./{{BROWSER_AOT}} --no-remote

coredump-bt PID:
    coredumpctl debug {{PID}} --debugger=gdb --debugger-arguments="-batch -ex 'bt' -ex 'info reg' -ex 'x/10i \$rip-16' -ex 'quit'"

coredump-gdb PID:
    coredumpctl debug {{PID}} --debugger=gdb

##~---- Benchmarks ----~##

bench-lock:
    #!/usr/bin/env bash
    echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost
    echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
    echo 0 | sudo tee /sys/devices/system/cpu/cpu3/online
    echo "locked: boost=off governor=performance cpu3=offline pin=cpu{{BENCH_CPU}}"

bench-unlock:
    #!/usr/bin/env bash
    echo 1 | sudo tee /sys/devices/system/cpu/cpu3/online
    echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
    echo 1 | sudo tee /sys/devices/system/cpu/cpufreq/boost
    echo "unlocked: boost=on governor=powersave cpu3=online"

bench-octane *FLAGS:
    #!/usr/bin/env bash
    cd js/src/octane
    time taskset -c {{BENCH_CPU}} ../../../jsshell {{FLAGS}} -f run.js

##~---- PGO Corpus ----~##

pgo-profile WORKLOAD=PGO_WORKLOAD:
    #!/usr/bin/env bash
    mkdir -p {{PGO_DIR}}/dump
    rm -f {{PGO_DIR}}/dump/IC-*
    echo "Profiling: {{WORKLOAD}}"
    JS_AOT_INSTR=ic \
    JS_AOT_INSTR_FILE={{PGO_DIR}}/ic-profile.log \
    JS_AOT_PGO_DIR={{PGO_DIR}}/dump \
    taskset -c {{BENCH_CPU}} ./jsshell -f {{WORKLOAD}}
    stubs=$(find {{PGO_DIR}}/dump -name 'IC-*' | wc -l)
    lines=$(cat {{PGO_DIR}}/ic-profile.log.* 2>/dev/null | wc -l)
    echo "Dumped $stubs stub files, $lines ic events -> {{PGO_DIR}}"

pgo-select BUDGET=PGO_BUDGET:
    #!/usr/bin/env bash
    python3 js/src/jit/SelectAOTCorpus.py \
        --profiles {{PGO_DIR}}/ic-profile.log.* \
        --dump-dir {{PGO_DIR}}/dump \
        --output-dir js/src/ics \
        --budget {{BUDGET}}
    # Redump the AOT container from js/src/ics/ into AOTBaseline.S so the
    # next build picks up the new corpus + hints.
    IONFLAGS=bl-aot ./jsshell --dump-bl-interp --dump-aot-ics --dump-bl-self-hosted -e 'quit(0)'

pgo-full WORKLOAD=PGO_WORKLOAD BUDGET=PGO_BUDGET:
    #!/usr/bin/env bash
    echo "=== Phase 1: Profile collection ==="
    just pgo-profile {{WORKLOAD}}
    echo ""
    echo "=== Phase 2: Corpus selection + redump (B={{BUDGET}}) ==="
    just pgo-select {{BUDGET}}
    echo ""
    echo "=== Phase 3: Rebuild ==="
    just build
