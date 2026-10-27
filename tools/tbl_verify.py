"""verify rebuilt table: every PC pointer slot (valid in PC) resolves in the NEW file to the same string as in the PC file."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
import tbl
def verify(psp, pc, new):
    hp, hc, _ = tbl.best_split(psp, pc)
    nr = tbl.parse(new, hp); cr = tbl.parse(pc, hc); pr = tbl.parse(psp, hp)
    nstr = {}; cstr = {}
    for r in nr:
        for k, st in enumerate(r.starts): nstr[st] = r.strings[k]
    for r in cr:
        for k, st in enumerate(r.starts): cstr[st] = r.strings[k]
    pstr = {}
    for r in pr:
        for k, st in enumerate(r.starts): pstr[st] = r.strings[k]
    ok = bad = 0
    for i, r in enumerate(nr):
        if i >= len(cr): continue
        c = cr[i]; p = pr[i]
        if len(c.header) != len(r.header): continue
        if tbl._is_door(p.strings): continue   # door pages are re-wrapped on purpose (kit35)
        for j in range(len(c.header) - 1):
            cv = struct.unpack_from('<H', c.header, j)[0]; pv = struct.unpack_from('<H', p.header, j)[0]
            if cv in cstr and pv in pstr:
                nv = struct.unpack_from('<H', r.header, j)[0]
                if nstr.get(nv) == tbl._ovr(cstr[cv]): ok += 1
                else: bad += 1
    return ok, bad
if __name__ == '__main__':
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    P = os.path.join(base, 'orig/psp/kit1/data_3rd/text'); C = os.path.join(base, 'orig/pc_gog_extracted/DT22')
    for f in sys.argv[1:]:
        psp = open(os.path.join(P, f), 'rb').read(); pc = open(os.path.join(C, f.upper().replace('._DT','._DT')), 'rb').read()
        new, rep = tbl.rebuild(psp, pc)
        print(f, verify(psp, pc, new))
