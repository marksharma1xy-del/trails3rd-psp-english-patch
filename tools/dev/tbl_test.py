import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
import tbl
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
P = os.path.join(base, 'orig/psp/kit1/data_3rd/text'); C = os.path.join(base, 'orig/pc_gog_extracted/DT22')
only = sys.argv[1:]
for f in sorted(os.listdir(P)):
    if not f.endswith('._dt') or (only and not any(f.startswith(o) for o in only)): continue
    cp = os.path.join(C, f.upper().replace('._DT', '._DT'))
    if not os.path.exists(cp): continue
    psp = open(os.path.join(P, f), 'rb').read(); pc = open(cp, 'rb').read()
    if psp == pc: print(f, 'IDENTICAL'); continue
    try:
        new, rep = tbl.rebuild(psp, pc)
        hp, hc, flag = tbl.best_split(psp, pc)
        ok = len(tbl.offsets(new)) == len(tbl.offsets(psp))
        print('%-14s %s recs=%d replaced=%d kept=%d slots=%d conflict=%d keptrecs=%s size %d->%d (pc %d)' % (f, ok, len(hp), rep['replaced'], rep['kept'], rep['slots'], rep['conflict'], rep['kept_recs'][:8], len(psp), len(new), len(pc)))
    except Exception as e:
        print(f, 'ERR', repr(e))
