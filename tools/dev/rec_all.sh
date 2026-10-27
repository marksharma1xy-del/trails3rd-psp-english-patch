#!/bin/sh
# usage: tools/rec_all.sh ABS_PY_DIR ABS_OUT_JSON_DIR  (records English instruction bytes for every scene .py; 2 parallel)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -d /tmp/fakegp ] || python3 "$ROOT/tools/make_fakegp.py" /tmp/fakegp
export PYTHONPATH="$ROOT/third_party/patched/Decompiler:$ROOT/third_party/patched/PyLibs-master:$ROOT/tools/stubs"
mkdir -p "$2"
cd "$ROOT/third_party/patched/Decompiler"
ls "$1"/*.py | xargs -P 2 -I{} sh -c 'python3 "'"$ROOT"'/tools/rec_compile.py" "{}" "'"$2"'" < /dev/null > "'"$2"'/$(basename {}).log" 2>&1'
echo "recorded: $(ls "$2"/*.json | wc -l); failures: $(grep -l Traceback "$2"/*.log | wc -l)"
