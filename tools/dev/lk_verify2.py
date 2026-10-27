"""lk_verify2.py ORIG_DIR REC_DIR NEW_DIR DUMP_ORIG DUMP_NEW   - independent check of lk_build2 output (incl. extra-script calls)."""
import sys, os, json, struct, glob
O, R, N, DO, DN = sys.argv[1:6]
T = {0x5B, 0x54, 0x5C, 0x60, 0x5D, 0xCC}
do = json.load(open(DO)); dn = json.load(open(DN)); bad = []; st = dict(same=0, A=0, B=0, C=0, ext=0, jp=0)
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
exts = {}
for f in glob.glob(N + '/extra/*__sub000.bin'): exts[os.path.basename(f).split('__')[0]] = open(f, 'rb').read()
PAR = {'U7000': 'u7000', 'U7001': 'u7001', 'U7002': 'u7002', 'U7003': 'u7003'}
for k in sorted(do):
    s = k[:-4]
    if s == 'SUB000': continue
    ob = open(f'{O}/{k}', 'rb').read(); nb = open(f'{N}/{k}', 'rb').read(); rec = json.load(open(f'{R}/{s}.json'))
    a = do[k]; d = dn[k]
    if not isinstance(d, list): bad.append((s, 'new scene fails to disassemble')); continue
    starts = set(x[0] for x in d)
    stor = u16(ob, 90); stn = u16(nb, 90); ftoo, fts = struct.unpack_from('<HH', ob, 96)
    if ob[ftoo:ftoo + fts] != nb[ftoo:ftoo + fts]: bad.append((s, 'functable'))
    hd = [i for i in range(0x64) if ob[i] != nb[i] and not (90 <= i < 92)]
    if hd and not all(0x38 <= i < 0x3c for i in hd): bad.append((s, 'header diff', hd[:5]))
    if nb[stn:] != bytes.fromhex(rec['strtab']): bad.append((s, 'strtab'))
    if stn > 65535 or len(nb) > 65535 + 0: bad.append((s, 'size', len(nb)))
    arch = s.lower() if os.path.exists(f'/home/claude/w/work/orig/psp/scripts_mc1/{s.lower()}.mc1') else PAR.get(s[:5], s.lower())
    ex = exts.get(arch)
    ti = [i for i, x in enumerate(a) if x[2] in T]; recs = iter(rec['text']); tset = set(ti)
    for i, x in enumerate(a):
        o0, lo = x[0], x[1]; o = ob[o0:o0 + lo]; n = nb[o0:o0 + lo]
        if i in tset:
            op, h = next(recs); e = bytes.fromhex(h); le = len(e)
            if o0 not in starts and n[0] != 3 and n[0] != 5: bad.append((s, 'not instr start', o0)); continue
            if n == o and e != o: st['jp'] += 1; continue
            if n == o: st['same'] += 1
            elif le == lo and n == e: st['A'] += 1
            elif le + 3 <= lo and n[:le] == e and n[le] == 3 and u16(n, le + 1) == o0 + lo: st['B'] += 1
            elif n[0] == 3:
                R_ = u16(n, 1)
                if nb[R_:R_ + le] == e: st['C'] += 1
                else: bad.append((s, 'C bytes', o0))
            elif n[0] == 5 and n[1] == 6 and nb[o0 + 4] == 3 and u16(nb, o0 + 5) == o0 + lo and ex is not None:
                fn = u16(n, 2); ft, fs_ = struct.unpack_from('<HH', ex, 96)
                if fn >= fs_ // 2: bad.append((s, 'ext fn range', fn)); continue
                fo = u16(ex, ft + 2 * fn)
                if ex[fo:fo + le] == e and ex[fo + le] == 1: st['ext'] += 1
                else: bad.append((s, 'ext bytes', o0))
            else: bad.append((s, 'text slot unknown', o0))
        else:
            if n != o and not (o0 in starts and False): bad.append((s, 'non-text instr changed', o0))
print('stats', st); print('problems', len(bad)); print(bad[:15])
