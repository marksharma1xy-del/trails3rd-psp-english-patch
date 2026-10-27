#!/bin/sh
# usage: tools/compile_all.sh ABS_DIR_WITH_py ABS_OUTDIR   (recompiles decompiled/patched scene .py -> ._SN; 2 parallel)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -d /tmp/fakegp ] || python3 "$ROOT/tools/make_fakegp.py" /tmp/fakegp
export PYTHONPATH="$ROOT/third_party/patched/Decompiler:$ROOT/third_party/patched/PyLibs-master:$ROOT/tools/stubs"
mkdir -p "$2"
cd "$1"
ls *.py | xargs -P 2 -I{} sh -c 'python3 "{}" --gp=/tmp/fakegp "'"$2"'" < /dev/null > "'"$2"'/{}.log" 2>&1'
echo "compiled: $(ls "$2"/*._SN | wc -l); failures: $(grep -l Traceback "$2"/*.log | wc -l)"
