"""dumpins.py OUT.json FILE._SN ...  -> {name: [[offset,size,opcode,nbranch],...]} via EDDecompiler disassembler (run with PYTHONPATH like decompile_all.sh)"""
import sys, os, json
out=sys.argv[1]; files=sys.argv[2:]
sys.argv=[sys.argv[0]]
import ED63RDScenarioScript as M
cp='932'
M.CODE_PAGE=cp; M.ed63rd.CODE_PAGE=cp; M.ed63rd.ed63rd_op_table.CodePage=cp; M.setCodePage(cp)
M.setGamePath('/tmp/fakegp'); M.initDatFileNameTable('/tmp/fakegp')
rec={}
orig_cb=M.ScenarioInfo.DiasmInstructionCallback
def cb(self,data):
    try:
        if data.Reason==M.HANDLER_REASON_DISASM:
            i=data.Instruction
            rec[i.Offset]=[i.Offset,i.Size,i.OpCode,len(i.BranchTargets or [])]
    except Exception: pass
    return orig_cb(self,data)
M.ScenarioInfo.DiasmInstructionCallback=cb
res={}
import contextlib
for f in files:
    rec.clear()
    try:
        M.ed63rd.ResetIndex(); M.ed63rd.ResetLabmdaIndex()
        sc=M.ScenarioInfo(); sc.open(f)
        res[os.path.basename(f)]=sorted(rec.values())
    except BaseException as e:
        res[os.path.basename(f)]='ERR '+repr(e)[:100]
json.dump(res,open(out,'w'))
