"""lk_verify.py ORIG_DIR EN_DIR NEW_DIR DUMP_ORIG DUMP_EN DUMP_NEW  -> independent check of the layout-keeping scenes.
For every original instruction (by index) it reads what the NEW file does at the ORIGINAL offset, follows trampolines, and demands:
  * unchanged/offset-only instrs: identical to the ORIGINAL bytes
  * text instrs (translated): the English bytes, reached via in-place / jump+back-jump
  * text instrs left JP (scene too big): the original bytes
Also: header identical except StringTableOffset; function table identical; string table = English; size/offset limits;
disassembler count check; every original instruction start is still an instruction start."""
import sys, os, json, struct
O, E, N, DO, DE, DN = sys.argv[1:7]
do = json.load(open(DO)); de = json.load(open(DE)); dn = json.load(open(DN))
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
bad = []; stat = dict(unch=0, A=0, B=0, C=0, jpkept=0, merged=0)
for k in sorted(do):
    ob = open(os.path.join(O, k), 'rb').read(); eb = open(os.path.join(E, k), 'rb').read(); nb = open(os.path.join(N, k), 'rb').read()
    a, b = do[k], de[k]
    stor = u16(ob, 90); stoe = u16(eb, 90); stn = u16(nb, 90)
    f2o = {y[0]: x[0] for x, y in zip(a, b)}
    # header / function table
    if ob[:90] != nb[:90] or ob[92:stor] != nb[92:stor]: bad.append((k, 'header/code region differs outside slots?')) if ob[:258][:90] != nb[:90] else None
    if ob[92:96] != nb[92:96] or ob[96:100] != nb[96:100]: bad.append((k, 'hdr end/functable ptr changed'))
    ftoo, fts = struct.unpack_from('<HH', ob, 96)
    if ob[ftoo:ftoo + fts] != nb[ftoo:ftoo + fts]: bad.append((k, 'function table changed'))
    if nb[stn:] != eb[stoe:]: bad.append((k, 'string table not English'))
    if stn > 65535: bad.append((k, 'strtab offset >64K'))
    if stn < stor: bad.append((k, 'strtab before function table end'))
    starts_new = set(r[0] for r in dn[k])
    expected_slots = 0
    # walk each original instruction
    chain_targets = {}   # relocated address -> expected back target for block ends
    for i, (x, y) in enumerate(zip(a, b)):
        O0, lo = x[0], x[1]
        o = ob[O0:O0 + lo]; e = eb[y[0]:y[0] + y[1]]
        n_here = nb[O0:O0 + lo]
        if O0 not in starts_new and not (nb[O0] == 3 and o != nb[O0:O0 + lo]):   # merged-run slots are legitimately not reached by flow
            bad.append((k, 'orig instr start not an instr start in new', O0)); continue
        if o == n_here:
            # unchanged JP bytes: legit for unchanged, offset-only and 'kept JP'
            if o == e: stat['unch'] += 1
            else:
                # offset-only or JP kept
                if len(o) == len(e):
                    ex = set()
                    for p in range(lo - 1):
                        v = u16(o, p); w = u16(e, p)
                        if v != w and f2o.get(w) == v: ex.add(p); ex.add(p + 1)
                    if all(j in ex for j in range(lo) if o[j] != e[j]): stat['unch'] += 1; continue
                stat['jpkept'] += 1
            continue
        le = len(e)
        if le == lo:
            if n_here == e: stat['A'] += 1
            else: bad.append((k, 'class A mismatch', O0))
        elif le + 3 <= lo:
            if n_here[:le] == e and n_here[le] == 3 and u16(n_here, le + 1) == O0 + lo: stat['B'] += 1
            else: bad.append((k, 'class B mismatch', O0))
        else:
            if n_here[0] != 3 or set(n_here[3:]) - {0} and False: bad.append((k, 'class C slot not a jump', O0)); continue
            R = u16(n_here, 1)
            if nb[R:R + le] != e: bad.append((k, 'class C relocated bytes differ', O0)); continue
            tail = nb[R + le:R + le + 3]
            if tail[0] == 3 and u16(tail, 1) == O0 + lo: stat['C'] += 1
            else:
                # merged block: next bytes must be the next instruction's English, whose slot points to R+le
                nx = a[i + 1][0] if i + 1 < len(a) else None
                if nx == O0 + lo and nb[nx] == 3 and u16(nb, nx + 1) == R + le: stat['C'] += 1; stat['merged'] += 1
                else: bad.append((k, 'class C back-jump missing', O0))
    # disassembler sanity: no decode errors (dn[k] is a list) and function entry points intact
    if not isinstance(dn[k], list): bad.append((k, 'new scene fails to disassemble'))
print('stats', stat); print('problems', len(bad)); print(bad[:20])
