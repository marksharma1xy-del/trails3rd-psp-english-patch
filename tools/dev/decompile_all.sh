#!/bin/sh
# usage: tools/decompile_all.sh DIR_WITH_SN_FILES     (Linux sandbox; ~0.5 s/file, runs 8 in parallel)
# Works for BOTH PC English ._SN and PSP Japanese scripts (PSP: use --cp=932; PC English: --cp=932 also fine).
# Needs: pip install xmltodict aiohttp rsa hexdump
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -d /tmp/fakegp ] || python3 "$ROOT/tools/make_fakegp.py" /tmp/fakegp
export PYTHONPATH="$ROOT/third_party/patched/Decompiler:$ROOT/third_party/patched/PyLibs-master:$ROOT/tools/stubs"
cd "$ROOT/third_party/patched/Decompiler"
ls "$1"/*._SN | xargs -P 2 -I{} sh -c 'python3 ED63RDScenarioScript.py --cp=932 --gp=/tmp/fakegp "{}" < /dev/null > "{}.log" 2>&1'
echo "done: $(ls "$1"/*.py | wc -l) .py files; failures: $(grep -l Traceback "$1"/*.log | wc -l)"
