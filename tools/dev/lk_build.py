"""lk_build.py  ORIG_SN_DIR EN_SN_DIR DUMP_ORIG.json DUMP_EN.json OUT_DIR [REPORT.txt]

LAYOUT-KEEPING scene builder.
Goal: every instruction that exists in the original JP scene stays at EXACTLY its original offset (so old JP savegames, which store
script positions, resume correctly), while the text is the English one.

How: start from the ORIGINAL JP bytes. For every instruction whose bytes differ (because of text):
   A) English length == JP length      -> English written in place
   B) English + 3 <= JP length          -> English in place + 'Jump <next instruction>' (3 bytes), rest dead (0x00)
   C) English longer                    -> slot becomes 'Jump <relocated copy>'; the copy (English instr + 'Jump back') is packed
                                           into dead bytes of other trampolined instructions, or appended after the function table.
Instructions that differ only by code-offset operands keep the ORIGINAL bytes (the targets are original offsets).
Header: original, except StringTableOffset (u16 @90) -> the English string table, appended as the LAST thing in the file.
Function table (original offsets) stays where it is.  If a scene does not fit under 64 KB, the largest-growth lines are left JP.
"""
import sys, os, json, struct

def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def jump(t):
    assert 0 <= t <= 0xFFFF, t
    return b'\x03' + struct.pack('<H', t)


def classify(ob, eb, a, b):
    """-> list of dicts for instructions whose bytes differ because of text"""
    f2o = {y[0]: x[0] for x, y in zip(a, b)}
    items = []
    for idx, (x, y) in enumerate(zip(a, b)):
        o = ob[x[0]:x[0] + x[1]]; e = eb[y[0]:y[0] + y[1]]
        if o == e: continue
        if len(o) == len(e):
            ex = set()
            for p in range(len(o) - 1):
                v = u16(o, p); w = u16(e, p)
                if v != w and f2o.get(w) == v: ex.add(p); ex.add(p + 1)
            if all(i in ex for i in range(len(o)) if o[i] != e[i]): continue   # offsets only -> keep original bytes
        items.append(dict(idx=idx, off=x[0], lo=len(o), e=e, op=x[2]))
    return items


def layout(ob, items, stor, dropped, merge):
    """returns (placements, tail_end) or None.  placements: list of (addr, bytes) to write; slots are written separately."""
    sel = [it for it in items if it['idx'] not in dropped]
    holes = []   # [start, length]
    cs = []
    for it in sel:
        le = len(it['e']); lo = it['lo']
        if le == lo: continue
        if le + 3 <= lo:
            if lo - le - 3 > 0: holes.append([it['off'] + le + 3, lo - le - 3])
            continue
        if lo - 3 > 0: holes.append([it['off'] + 3, lo - 3])
        cs.append(it)
    # blocks = runs of adjacent class-C instructions
    blocks = []
    cur = []
    for it in cs:
        if merge and cur and cur[-1]['idx'] + 1 == it['idx'] and cur[-1]['off'] + cur[-1]['lo'] == it['off']:
            cur.append(it)
        else:
            if cur: blocks.append(cur)
            cur = [it]
    if cur: blocks.append(cur)
    order = sorted(range(len(blocks)), key=lambda i: -sum(len(x['e']) for x in blocks[i]))
    addr = {}      # idx -> relocated address of its English bytes
    backs = []     # (address of back-jump, target)
    tail = stor
    place = []
    for bi in order:
        blk = blocks[bi]; size = sum(len(x['e']) for x in blk) + 3
        best = None
        for h in holes:
            if h[1] >= size and (best is None or h[1] < best[1]): best = h
        if best is not None:
            base = best[0]; best[0] += size; best[1] -= size
        else:
            base = tail; tail += size
        p = base
        for x in blk:
            addr[x['idx']] = p; place.append((p, x['e'])); p += len(x['e'])
        nxt = blk[-1]['off'] + blk[-1]['lo']
        place.append((p, jump(nxt)))
    return sel, addr, place, tail


def build_scene(ob, eb, a, b):
    stor = u16(ob, 90); stoe = u16(eb, 90)
    ftoo, fts = struct.unpack_from('<HH', ob, 96)
    assert ftoo + fts == stor
    en_str = eb[stoe:]
    items = classify(ob, eb, a, b)
    dropped = set()
    best = None
    while True:
        res = None
        for merge in (True, False):
            r = layout(ob, items, stor, dropped, merge)
            if res is None or r[3] < res[3]: res = r
        sel, addr, place, tail = res
        if tail + len(en_str) <= 65535: break
        # drop the not-yet-dropped class-C item with biggest growth
        cand = [it for it in sel if len(it['e']) + 3 > it['lo']]
        if not cand: raise RuntimeError('cannot fit')
        # drop a batch proportional to the overshoot to keep it quick
        over = tail + len(en_str) - 65535
        cand.sort(key=lambda it: -(len(it['e']) - it['lo']))
        got = 0
        for it in cand:
            dropped.add(it['idx']); got += len(it['e']) - it['lo'] + 6
            if got >= over: break
    new = bytearray(ob[:stor])
    new += b'\x00' * (tail - stor)
    for it in sel:
        le = len(it['e']); lo = it['lo']; o = it['off']
        if le == lo: new[o:o + lo] = it['e']
        elif le + 3 <= lo:
            new[o:o + lo] = b'\x00' * lo
            new[o:o + le] = it['e']; new[o + le:o + le + 3] = jump(o + lo)
        else:
            # clear the dead bytes first (holes may be reused by blocks below)
            new[o:o + lo] = b'\x00' * lo
    # holes must be cleared BEFORE blocks are written -> write slots (clearing) first, then blocks, then slot jumps
    for p, bts in place: new[p:p + len(bts)] = bts
    for it in sel:
        le = len(it['e']); lo = it['lo']
        if le + 3 > lo and le != lo:
            new[it['off']:it['off'] + 3] = jump(addr[it['idx']])
    strpos = tail
    new += en_str
    struct.pack_into('<H', new, 90, strpos)
    return bytes(new), dict(items=len(items), dropped=sorted(dropped), tail=tail, stor=stor, orig=len(ob),
                            nA=sum(1 for it in sel if len(it['e']) == it['lo']),
                            nB=sum(1 for it in sel if len(it['e']) != it['lo'] and len(it['e']) + 3 <= it['lo']),
                            nC=sum(1 for it in sel if len(it['e']) + 3 > it['lo'] and len(it['e']) != it['lo']),
                            dead_ok=True, items_detail=[(it['idx'], it['off'], it['lo'], len(it['e'])) for it in items if it['idx'] in dropped])


def main():
    O, E, DO, DE, OUT = sys.argv[1:6]
    rep = open(sys.argv[6], 'w') if len(sys.argv) > 6 else sys.stdout
    do = json.load(open(DO)); de = json.load(open(DE))
    os.makedirs(OUT, exist_ok=True)
    tot = dict(items=0, dropped=0)
    for k in sorted(do):
        ob = open(os.path.join(O, k), 'rb').read(); eb = open(os.path.join(E, k), 'rb').read()
        new, r = build_scene(ob, eb, do[k], de[k])
        open(os.path.join(OUT, k), 'wb').write(new)
        tot['items'] += r['items']; tot['dropped'] += len(r['dropped'])
        rep.write('%-14s orig %6d new %6d  text-instr %4d  inplace=A%d/B%d  trampolined=C%d  tail_end %6d  dropped(JP kept) %d\n' % (
            k, len(ob), len(new), r['items'], r['nA'], r['nB'], r['nC'], r['tail'], len(r['dropped'])))
        for d in r['items_detail']: rep.write('     JP kept: ins#%d @%d jplen %d englen %d\n' % d)
    rep.write('TOTAL text instr %d, left JP %d\n' % (tot['items'], tot['dropped']))


if __name__ == '__main__':
    main()
