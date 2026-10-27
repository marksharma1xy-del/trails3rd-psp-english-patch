"""prefix.py - remap the code pointers inside PSP scene side-file <scene>.pre after the .bin text changed.
.pre layout (verified on all 298 originals, arrays tile the file exactly):
  hdr 5 x u32: [0x14, n0, dir1, dir2, dir3]; n0 x u16 at 0x14 (NOT code pointers, left alone)
  dir1..dir2 : 16-byte slots (0,type,count,off) -> arrays of  8-byte recs, code ptr = u16 @+2
  dir2..dir3 : 16-byte slots                    -> arrays of 24-byte recs, code ptr = u16 @+4
  dir3..zero : 16-byte slots (ends with zero slot)-> arrays of 16-byte recs, code ptr = u16 @+4
Archives holding several scripts (u7000: u7000,_1.._5; u7001; ...) list slots script by script: a slot whose type does
not rise vs the previous slot (in the same group) starts the next script.  Script of a slot = smallest candidate script
(all ptrs of the array are instruction starts) that keeps the order non-decreasing.
usage:  python prefix.py ORIG_MC1_DIR INST_JSON OUT_DIR [replaced.txt]   -> OUT_DIR/<scene>.pre (+ report)"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psp_mc, falcom_lz as F

def slots_of(d):
    h = struct.unpack_from('<5I', d, 0)
    o3 = h[4]
    while True:
        s = struct.unpack_from('<4I', d, o3); o3 += 16
        if s == (0, 0, 0, 0): break
    return h, [(h[2], h[3], 8, 2), (h[3], h[4], 24, 4), (h[4], o3, 16, 4)]

def remap_pre(d, scripts, inst, replaced):
    """scripts: ordered script names in this archive (main first). inst[name]={'o':[..],'n':[..]}. replaced: set of names whose bin changed.
    returns (new_pre_bytes, stats). Raises ValueError on anything unexplained."""
    out = bytearray(d); h, groups = slots_of(d)
    S = {n: {v: i for i, v in enumerate(inst[n]['o'])} for n in scripts if n in inst}
    st = {'ptrs': 0, 'changed': 0, 'ambig_resolved': 0}
    for gi, (a, b, size, fld) in enumerate(groups):
        prev_script, prev_type = 0, -1
        for so in range(a, b, 16):
            _, typ, cnt, off = struct.unpack_from('<4I', d, so)
            if cnt == 0: continue
            ps = [off + k * size + fld for k in range(cnt)]
            vals = [struct.unpack_from('<H', d, p)[0] for p in ps]
            cands = [n for n in scripts if n in S and all(v in S[n] for v in vals)]
            cands = [n for n in cands if scripts.index(n) >= prev_script and (typ > prev_type or scripts.index(n) > prev_script or prev_type < 0)]
            if not cands: raise ValueError('no script explains slot g%d type %d off %x vals %s' % (gi, typ, off, vals[:5]))
            if len(cands) > 1: st['ambig_resolved'] += 1
            sc = cands[0]; prev_script = scripts.index(sc); prev_type = typ
            for p, v in zip(ps, vals):
                st['ptrs'] += 1
                if sc in replaced:
                    nv = inst[sc]['n'][S[sc][v]]
                    if nv > 0xFFFF: raise ValueError('offset overflow')
                    if nv != v: struct.pack_into('<H', out, p, nv); st['changed'] += 1
    return bytes(out), st

if __name__ == '__main__':
    src, ij, outd = sys.argv[1:4]
    inst = json.load(open(ij)); os.makedirs(outd, exist_ok=True)
    tot = {'ptrs': 0, 'changed': 0, 'ambig_resolved': 0}; nfile = nerr = 0
    for fn in sorted(os.listdir(src)):
        if not fn.endswith('.mc1'): continue
        sc = fn[:-4]; mc = open(os.path.join(src, fn), 'rb').read()
        ents = {n: (raw, us) for n, raw, us in psp_mc.entries(mc)}
        if sc + '.pre' not in ents: continue
        raw, us = ents[sc + '.pre']; d = F.psp_entry(raw)[0] if us else raw
        scripts = [n[:-4] for n, (r, u) in ents.items() if n.endswith('.bin') and n != 'sub000.bin']
        scripts.sort(key=lambda n: (n != sc, n))
        try:
            nd, s = remap_pre(d, scripts, inst, {sc})
        except Exception as e:
            print('ERR', sc, e); nerr += 1; continue
        assert len(nd) == len(d)
        open(os.path.join(outd, sc + '.pre'), 'wb').write(nd); nfile += 1
        for k in tot: tot[k] += s[k]
    print('files', nfile, 'errors', nerr, tot)
