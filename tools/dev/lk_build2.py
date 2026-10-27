"""lk_build2.py ORIG_SN_DIR REC_DIR DUMP_ORIG.json OUT_DIR [REPORT]
Layout-keeping builder v2 (see lk_build.py) + EXTRA SCRIPT overflow.
 * English text instrs come from tools/rec_compile.py JSON (REC_DIR/<SCENE>.json) - works for scenes that can't be compiled normally.
 * If tail+strtab exceeds LIMIT, the biggest class-C text instrs are moved into functions of an extra SUB000 copy (per ARCHIVE) instead of staying JP:
     slot = Call(SLOT, func) [05 slot u16] + Jump next [03 u16]; function = instr bytes + Return [01].
 * OUT_DIR/<SCENE>._SN  and OUT_DIR/extra/<archive>__sub000.bin
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lk_build as L
T = {0x5B, 0x54, 0x5C, 0x60, 0x5D, 0xCC}
LIMIT = 65000; SLOT = 6; SUBID = 0x210001
PARENT = {'U7000_1': 'u7000', 'U7000_2': 'u7000', 'U7000_3': 'u7000', 'U7000_4': 'u7000', 'U7000_5': 'u7000', 'U7001_5': 'u7001',
          'U7002_4': 'u7002', 'U7002_5': 'u7002', 'U7003_4': 'u7003', 'U7003_5': 'u7003'}
def u16(b, o): return struct.unpack_from('<H', b, o)[0]

class Ext:
    def __init__(self, base):
        self.base = base; self.ftoo, self.fts = struct.unpack_from('<HH', base, 96); self.stor = u16(base, 90)
        assert self.ftoo + self.fts == self.stor
        self.nf = self.fts // 2; self.funcs = []
    def add(self, data):
        self.funcs.append(data + b'\x01'); return self.nf + len(self.funcs) - 1
    def build(self):
        k = len(self.funcs); b = self.base
        code0 = self.ftoo + self.fts + 2 * k; offs = []; p = code0
        for f in self.funcs: offs.append(p); p += len(f)
        out = bytearray(b[:self.ftoo + self.fts]) + b''.join(struct.pack('<H', o) for o in offs) + b''.join(self.funcs)
        struct.pack_into('<H', out, 90, len(out)); struct.pack_into('<H', out, 98, self.fts + 2 * k)
        out += b[self.stor:]
        assert len(out) <= 65535 and len(out) - len(b[self.stor:]) <= 65535
        return bytes(out)

def items_for(ob, a, rec):
    ti = [i for i, x in enumerate(a) if x[2] in T]
    if len(ti) != len(rec['text']): raise RuntimeError('text instr count mismatch %d vs %d' % (len(ti), len(rec['text'])))
    items = []
    for i, (op, h) in zip(ti, rec['text']):
        x = a[i]; e = bytes.fromhex(h); assert op == x[2]
        if e != ob[x[0]:x[0] + x[1]]: items.append(dict(idx=i, off=x[0], lo=x[1], e=e, op=x[2]))
    return items

def build(ob, a, rec, ext):
    stor = u16(ob, 90); en_str = bytes.fromhex(rec['strtab']); items = items_for(ob, a, rec)
    moved = {}; dropped = set()
    while True:
        res = None
        for merge in (True, False):
            r = L.layout(ob, items, stor, set(moved) | dropped, merge)
            if res is None or r[3] < res[3]: res = r
        sel, addr, place, tail = res
        if tail + len(en_str) <= LIMIT: break
        cand = sorted([it for it in sel if len(it['e']) + 3 > it['lo']], key=lambda it: -(len(it['e']) - it['lo']))
        if not cand: raise RuntimeError('cannot fit')
        over = tail + len(en_str) - LIMIT; got = 0
        for it in cand:
            if it['lo'] >= 7 and ext is not None: moved[it['idx']] = it
            else: dropped.add(it['idx'])
            got += len(it['e']) + 3
            if got >= over: break
    new = bytearray(ob[:stor]) + b'\x00' * (tail - stor)
    for it in sel:
        le, lo, o = len(it['e']), it['lo'], it['off']
        if le == lo: new[o:o + lo] = it['e']
        elif le + 3 <= lo:
            new[o:o + lo] = b'\x00' * lo; new[o:o + le] = it['e']; new[o + le:o + le + 3] = L.jump(o + lo)
        else: new[o:o + lo] = b'\x00' * lo
    for p, bts in place: new[p:p + len(bts)] = bts
    for it in sel:
        le, lo = len(it['e']), it['lo']
        if le + 3 > lo and le != lo: new[it['off']:it['off'] + 3] = L.jump(addr[it['idx']])
    for idx, it in moved.items():
        fn = ext.add(it['e']); o = it['off']
        new[o:o + it['lo']] = b'\x00' * it['lo']
        new[o:o + 7] = b'\x05' + bytes([SLOT]) + struct.pack('<H', fn) + L.jump(o + it['lo'])
    struct.pack_into('<H', new, 90, tail); new += en_str
    if moved:
        cur = struct.unpack_from('<I', new, 0x20 + 4 * SLOT)[0]
        if cur not in (0xFFFFFFFF, SUBID): raise RuntimeError('slot %d busy: %x' % (SLOT, cur))
        struct.pack_into('<I', new, 0x20 + 4 * SLOT, SUBID)
    return bytes(new), dict(items=len(items), moved=sorted(moved), dropped=sorted(dropped), tail=tail, orig=len(ob),
                            moved_info=[(i, it['off'], it['lo'], len(it['e'])) for i, it in sorted(moved.items())])

def main():
    O, R, DO, OUT = sys.argv[1:5]; rep = open(sys.argv[5], 'w') if len(sys.argv) > 5 else sys.stdout
    do = json.load(open(DO)); os.makedirs(OUT + '/extra', exist_ok=True)
    sub = open(os.path.join(O, 'SUB000._SN'), 'rb').read(); exts = {}; jl = []; nm = nd = 0
    for k in sorted(do):
        s = k[:-4]
        if s == 'SUB000': continue
        ob = open(os.path.join(O, k), 'rb').read(); rec = json.load(open(os.path.join(R, s + '.json')))
        arch = PARENT.get(s, s.lower()); ext = exts.setdefault(arch, Ext(sub))
        new, r = build(ob, do[k], rec, ext)
        open(os.path.join(OUT, k), 'wb').write(new); nm += len(r['moved']); nd += len(r['dropped'])
        rep.write('%-9s orig %6d new %6d items %4d tail %6d ext-moved %3d JP-kept %d\n' % (s, len(ob), len(new), r['items'], r['tail'], len(r['moved']), len(r['dropped'])))
    for arch, e in exts.items():
        if e.funcs: open('%s/extra/%s__sub000.bin' % (OUT, arch), 'wb').write(e.build()); rep.write('EXTRA %s: %d funcs\n' % (arch, len(e.funcs)))
    rep.write('TOTAL moved to ext %d, JP kept %d\n' % (nm, nd))
if __name__ == '__main__': main()
