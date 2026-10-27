"""psp_mc.py - list/extract entries of PSP map4 archives (.mc1 .mc2 .mc3 .mce .mcl .mcp .mcz .mcc)
Usage: python psp_mc.py c0301.mc1 outdir      -> writes c0301.bin (= PC-style ._SN script), .pre, .dtm, ...
Archive: u32 count x4, then count*32-byte entries: name[16], u32 offset, u32 packed, u32 unpacked, u32 0.
Entry with unpacked>0: [u32 in][u32 out][u32 mode=2|4] + ed6 frames (falcom_lz.psp_entry). 
Entries with unpacked==0 (.itp/.itc/.it3 images/models) use ANOTHER format -> saved raw as NAME.raw (not needed for text).
Batch: python psp_mc.py --scripts DIR_WITH_mc1 outdir   -> every *.mc1 -> outdir/<scene>._SN  (upper-case name)"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import falcom_lz as F

def entries(d):
    n = struct.unpack_from('<I', d, 0)[0]
    for i in range(n):
        name, off, ps, us, z = struct.unpack_from('<16sIIII', d, 16 + 32 * i)
        yield name.split(b'\0')[0].decode('latin1'), d[off:off + ps], us

def extract(path, outdir):
    os.makedirs(outdir, exist_ok=True); d = open(path, 'rb').read()
    for name, raw, us in entries(d):
        if us:
            data = F.psp_entry(raw)[0]; fn = name
        else:
            data = raw; fn = name + '.raw'
        open(os.path.join(outdir, fn), 'wb').write(data)

if __name__ == '__main__':
    if sys.argv[1] == '--scripts':
        src, out = sys.argv[2], sys.argv[3]; os.makedirs(out, exist_ok=True); k = 0
        for fn in sorted(os.listdir(src)):
            if not fn.lower().endswith('.mc1'): continue
            for name, raw, us in entries(open(os.path.join(src, fn), 'rb').read()):
                if name.lower().endswith('.bin'):
                    open(os.path.join(out, name[:-4].upper() + '._SN'), 'wb').write(F.psp_entry(raw)[0]); k += 1
        print('wrote', k, 'scripts to', out)
    else:
        extract(sys.argv[1], sys.argv[2])
