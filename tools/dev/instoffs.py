"""instoffs.py OUT.json FILE._SN [FILE._SN ...]  -> {name: sorted list of instruction start offsets} using the EDDecompiler disassembler.
Run from third_party/patched/Decompiler with PYTHONPATH=Decompiler:PyLibs-master:tools/stubs  (same env as decompile_all.sh)."""
import sys, os, json, io
sys.argv_saved = sys.argv[:]
out = sys.argv[1]; files = sys.argv[2:]
sys.argv = [sys.argv[0]]
import ED63RDScenarioScript as M
cp = '932'
M.CODE_PAGE = cp; M.ed63rd.CODE_PAGE = cp; M.ed63rd.ed63rd_op_table.CodePage = cp; M.setCodePage(cp)
gp = '/tmp/fakegp'
M.setGamePath(gp); M.initDatFileNameTable(gp)
rec = []
orig_cb = M.ScenarioInfo.DiasmInstructionCallback
def cb(self, data):
    try:
        if data.Reason == M.HANDLER_REASON_DISASM:
            rec.append(data.Instruction.Offset)
    except Exception: pass
    return orig_cb(self, data)
M.ScenarioInfo.DiasmInstructionCallback = cb
res = {}
for f in files:
    rec.clear()
    try:
        M.ed63rd.ResetIndex(); M.ed63rd.ResetLabmdaIndex()
        sc = M.ScenarioInfo(); sc.open(f)
        res[os.path.basename(f)[:-4].lower()] = sorted(set(rec))
    except BaseException as e:
        res[os.path.basename(f)[:-4].lower()] = 'ERR ' + repr(e)[:80]
json.dump(res, open(out, 'w'))
