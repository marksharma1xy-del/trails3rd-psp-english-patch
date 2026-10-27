"""rec_compile.py SCENE.py OUT_DIR  -> OUT_DIR/<SCENE>.json  = {'text': [[opcode, bytes_hex], ...] (text instructions only, file order), 'strtab': hex}
Runs a decompiled scene .py through the EDDecompiler ASSEMBLER but records every TEXT instruction as it is emitted instead of
writing the final file.  Works for scenes that would be > 64 KB (u16 offsets would overflow in the real compile): label operands are
placeholders (we never use them - the layout-keeping builder keeps the ORIGINAL bytes of every non-text instruction).
Run like compile_all.sh:  cd third_party/patched/Decompiler; PYTHONPATH=Decompiler:PyLibs-master:tools/stubs; needs /tmp/fakegp."""
import sys, os, json, runpy, tempfile
src, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
tmp = tempfile.mkdtemp()
sys.argv = [src, '--gp=/tmp/fakegp', tmp]
import ED63RDScenaFile as M
rec = []
orig = M.OpCodeHandler
TEXT = (0x5B, 0x54, 0x5C, 0x60, 0x5D, 0xCC)
def hook(op, args):
    """record the bytes of every TEXT instruction (also those nested inside another instruction's lambda body), in emission = file order"""
    if op not in TEXT: return orig(op, args)
    prev = M.scena.PrevousHandlerData
    if prev is None:
        fs = M.scena.fs; p0 = fs.tell()
        r = orig(op, args)
        p1 = fs.tell(); fs.seek(p0); data = fs.read(p1 - p0); fs.seek(p1)
    else:
        fs = prev.FileStream; p0 = fs.tell()
        r = orig(op, args)
        p1 = fs.tell(); fs.seek(p0); data = fs.read(p1 - p0); fs.seek(p1)
    rec.append([op, data.hex()])
    return r
M.OpCodeHandler = hook
def save():
    sc = M.scena
    st = b''
    if type(sc.StringTable) == list and len(sc.StringTable) > 0:
        st = '\x00'.join(sc.StringTable).encode(M.CODE_PAGE) + b'\x00'
    name = os.path.splitext(os.path.basename(src))[0]
    json.dump({'text': rec, 'strtab': st.hex(), 'nfunc': len(sc.ScpFunctionList)}, open(os.path.join(outdir, name + '.json'), 'w'))
    sc.fs.close()
M.SaveToFile = save
runpy.run_path(src, run_name='__main__')
