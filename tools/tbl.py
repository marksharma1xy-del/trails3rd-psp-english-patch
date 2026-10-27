"""tbl.py - parse / rebuild Falcom T_*._DT text tables (PC English and PSP Japanese share the layout).

File = u16 offset table (first u16 / 2 = N records), then N records (record i = data[off[i]:off[i+1]]).
Record = binary header (contains u16 LE absolute-file-offset pointers to its strings, any byte alignment) + string area of
NUL-terminated strings.  Special: some records are plain strings (no header) or pure pointer tables (e.g. T_TOWN rec 0).

parse(data)            -> list of Rec(start,end,hlen,header(bytes),strings[list of bytes])
find_split(data, a, b) -> header length of record [a,b) (see below)
rebuild(psp, pc, mode) -> new PSP-layout file whose strings come from PC (English) ; pointer fields are rewritten.
selftest(psp)          -> rebuild with PSP's own strings, must be byte-identical.
"""
import struct, sys, os


def offsets(d):
    """returns list of N+1 values: starts[0..N-1] and a final sentinel; use ends() for record ends."""
    first = struct.unpack_from('<H', d, 0)[0]
    n = first // 2
    return list(struct.unpack_from('<%dH' % n, d, 0)) + [len(d)]


def bounds(d):
    """per index (start,end) with end = next larger distinct start (records may be unordered/aliased)."""
    o = offsets(d)
    st = sorted(set(o))
    nxt = {a: st[k + 1] for k, a in enumerate(st[:-1])}
    return [(a, nxt.get(a, len(d))) for a in o[:-1]]


def _valid_area(d, p, b):
    # bytes d[p:b] must be NUL-terminated strings (end with NUL) or empty
    if p == b:
        return True
    return d[b - 1] == 0


def find_split(d, a, b):
    """return absolute position s0 where the string area of record [a,b) starts."""
    if b - a == 0:
        return b
    # candidates: positions p in [a,b] such that header d[a:p] contains u16 == p (any alignment) and tail valid
    hdr_ok = []
    for p in range(a + 1, b + 1):
        if not _valid_area(d, p, b):
            continue
        t = struct.pack('<H', p)
        if d.find(t, a, p) >= 0:
            hdr_ok.append(p)
    if _valid_area(d, a, b):
        hdr_ok.append(a)  # pure string record (fallback, least preferred)
    return hdr_ok


class Rec:
    def __init__(s, start, end, s0, d):
        s.start, s.end, s.s0 = start, end, s0
        s.header = d[start:s0]
        area = d[s0:end]
        if area:
            parts = area.split(b'\0')
            assert parts[-1] == b''
            parts = parts[:-1]
        else:
            parts = []
        s.strings = parts
        s.starts = []
        p = s0
        for x in parts:
            s.starts.append(p)
            p += len(x) + 1


def parse(d, hint=None):
    """list per index of Rec. hint[i] = header length (so PC and PSP use equal header length)."""
    recs = []
    for i, (a, b) in enumerate(bounds(d)):
        if hint is not None:
            s0 = a + hint[i]
        else:
            c = find_split(d, a, b)
            s0 = c[0] if c else b
        recs.append(Rec(a, b, s0, d))
    return recs


def best_split(psp, pc):
    """header lengths (psp, pc) per index; prefer a header length valid in both files."""
    pb, cb = bounds(psp), bounds(pc)
    hp, hc, flag = [], [], []
    for i, (a, b) in enumerate(pb):
        cp = [x - a for x in find_split(psp, a, b)]
        cc = [x - cb[i][0] for x in find_split(pc, *cb[i])] if i < len(cb) else []
        com = [x for x in cp if x in cc]
        if com:
            hp.append(com[0]); hc.append(com[0]); flag.append('pair')
        else:
            hp.append(cp[0] if cp else b - a)
            hc.append(cc[0] if cc else (cb[i][1] - cb[i][0] if i < len(cb) else 0))
            flag.append('split' if (cp and cc) else 'none')
    return hp, hc, flag


KEPT_OVERRIDE = {'ヨシュア'.encode('cp932'): b'Joshua'}   # PSP strings with no PC counterpart (kept strings only)

def _load_table_en():
    import os
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'queue', 'table_en.tsv')
    if not os.path.exists(f):
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'table_en.tsv')
    if os.path.exists(f):
        for l in open(f, encoding='utf-8'):
            l = l.rstrip('\n')
            if '\t' in l:
                j, e = l.split('\t', 1)
                j = j.replace('\\x01', '\x01').replace('\\x02', '\x02'); e = e.replace('\\x01', '\x01').replace('\\x02', '\x02')
                KEPT_OVERRIDE[j.encode('cp932')] = e.encode('cp932')
_load_table_en()
def _ovr(sx):
    best = None
    for j, e in KEPT_OVERRIDE.items():
        if sx.endswith(j) and (best is None or len(j) > len(best[0])): best = (j, e)
    if best: return sx[:-len(best[0])] + best[1]
    return sx


def rebuild_world2(psp):
    """t_world2 (PSP only): u16 offset table, record = 8-byte binary header + name\\0 + extra bytes. Names replaced by EXACT KEPT_OVERRIDE match."""
    o = offsets(psp); n = o[0] // 2
    recs = []
    for i in range(n):
        a, b = o[i], o[i + 1]
        h = psp[a:a + 8]; rest = psp[a + 8:b]
        k = rest.find(b'\0')
        name, tail = rest[:k], rest[k:]
        recs.append(h + KEPT_OVERRIDE.get(name, name) + tail)
    out = bytearray(); pos = n * 2; tab = []
    for r in recs:
        tab.append(pos); pos += len(r)
    out += struct.pack('<%dH' % n, *tab)
    for r in recs: out += r
    return bytes(out)


import textwrap as _tw
_DOOR_KEY = '\u6249'.encode('cp932')   # kanji for "door"
def _is_door(strs):
    return len(strs) == 17 and _DOOR_KEY in strs[7]

def _fix_door(lst, pcstrs):
    """PSP Sun/Moon/Star Door pages have narrow boxes (PC wrapped at ~35 chars): re-wrap riddle / info / bonus, restore the episode line,
    and keep the leading blank line the PSP riddle layout needs."""
    lst = list(lst)
    try:
        if lst[1].strip() == b'' and len(pcstrs) > 2 and pcstrs[2].strip() not in (b'', b' '):
            lst[1] = b' ' + pcstrs[2].strip()
        # riddle
        parts = lst[3].decode('cp932').split('\x01'); paras = []; cur = []
        for ln in parts:
            if ln.strip() == '':
                if cur: paras.append(' '.join(cur)); cur = []
            else: cur.append(ln.strip())
        if cur: paras.append(' '.join(cur))
        body = []
        for k, pa in enumerate(paras):
            if k: body.append(' ')
            body += [' ' + l for l in _tw.wrap(pa, 30, break_long_words=False)]
        lst[3] = '\x01'.join([' '] + body).encode('cp932')
        # info: unwrap, re-wrap to at most 3 lines
        info = ' '.join(x.strip() for x in lst[5].decode('cp932').split('\x01') if x.strip())
        for w in (30, 31, 32, 33):
            ls = _tw.wrap(info, w, break_long_words=False)
            if len(ls) <= 3: break
        lst[5] = '\x01'.join(ls).encode('cp932')
        # bonus: keep item lines, wrap long ones
        out = []
        for ln in lst[6].decode('cp932').split('\x01'):
            w2 = _tw.wrap(ln, 30, subsequent_indent='  ', break_long_words=False) or [ln]
            out += w2
        lst[6] = '\x01'.join(out).encode('cp932')
    except Exception:
        return list(lst)
    return lst

def rebuild(psp, pc, hp=None, hc=None, own=False, inline=False):
    """Return (newdata, report). English text is taken from the PC string that the SAME header pointer slot refers to
    (slot = position of a u16 in the record header; a slot is valid when it points to a string start in BOTH files).
    PSP strings with no slot: if the record has no header (plain string record) and string counts match -> by index; else kept.
    All pointer slots are rewritten to the new string positions; the leading offset table is rewritten too."""
    if hp is None:
        hp, hc, _ = best_split(psp, pc)
    pr = parse(psp, hp)
    cr = parse(pc, hc) if not own else pr
    report = {'replaced': 0, 'kept': 0, 'slots': 0, 'conflict': 0, 'kept_recs': []}
    pstart = {}  # psp string start -> (rec idx, k)
    for i, r in enumerate(pr):
        for k, st in enumerate(r.starts):
            pstart.setdefault(st, (i, k))
    cstart = {}
    for i, r in enumerate(cr):
        for k, st in enumerate(r.starts):
            cstart.setdefault(st, r.strings[k])
    uniq = {}
    for i, r in enumerate(pr):
        uniq.setdefault(r.start, i)
    order = sorted(uniq)
    # slots
    slots = []  # (rec idx, byte pos in header, psp string start)
    text = {}   # psp string start -> new bytes
    for st in order:
        i = uniq[st]; r = pr[i]
        oh = None if own else (cr[i].header if i < len(cr) and len(cr[i].header) == len(r.header) else None)
        if not own and oh is None:
            continue
        j = 0
        rstarts = set(r.starts)
        cstarts_i = set(cr[i].starts) if i < len(cr) else set()
        while j + 2 <= len(r.header):
            v = struct.unpack_from('<H', r.header, j)[0]
            if v in pstart and (not r.strings or v in rstarts):
                if own:
                    cv = v
                else:
                    cvv = struct.unpack_from('<H', oh, j)[0]
                    cv = cvv if (cvv in cstart and (not r.strings or cvv in cstarts_i)) else None
                if cv is not None:
                    slots.append((i, j, v))
                    t = pr[pstart[v][0]].strings[pstart[v][1]] if own else cstart[cv]
                    if v in text and text[v] != t:
                        report['conflict'] += 1
                    text.setdefault(v, t)
                    j += 2; continue
            j += 1
    report['slots'] = len(slots)
    newstr = {}
    for st in order:
        i = uniq[st]; r = pr[i]
        lst = []
        idx_ok = (not own and i < len(cr) and len(cr[i].header) == 0 and len(r.header) == 0 and len(cr[i].strings) == len(r.strings))
        for k, sx in enumerate(r.strings):
            if r.starts[k] in text:
                lst.append(_ovr(text[r.starts[k]])); report['replaced'] += 1
            elif idx_ok:
                lst.append(_ovr(cr[i].strings[k])); report['replaced'] += 1
            else:
                lst.append(_ovr(sx)); report['kept'] += 1
        if any(r.strings[k] != lst[k] or True for k in range(len(lst))):
            pass
        if not own and i < len(cr) and _is_door(r.strings) and len(cr[i].strings) > 2:
            lst = _fix_door(lst, cr[i].strings)
        newstr[st] = lst
        if len(lst) and all(lst[k] == r.strings[k] for k in range(len(lst))) and not own and any(x for x in r.strings):
            report['kept_recs'].append(i)
    # ---- inline header strings (t_shop / t_town: NUL-terminated cp932 JP text inside the record header, referenced by a header pointer)
    inl = {}   # st -> (rel_pos, old_len_incl_nul, new_bytes)
    if inline:
        for st in order:
            r = pr[uniq[st]]; h = r.header; best = None
            for j in range(0, len(h) - 1):
                v = struct.unpack_from('<H', h, j)[0]
                rel = v - r.start
                if 4 <= rel < len(h) and (v not in pstart):
                    e = h.find(b'\0', rel)
                    if e < 0 or e == rel: continue
                    txt = h[rel:e]
                    try: txt.decode('cp932')
                    except Exception: continue
                    if not any(b >= 0x81 for b in txt): continue
                    nt = _ovr(txt)
                    if nt != txt:
                        best = (rel, e - rel + 1, nt); break
            if best: inl[st] = best
    def _hm(st, rel):   # old header-relative position -> new
        if st in inl and rel >= inl[st][0] + inl[st][1]:
            return rel + len(inl[st][2]) + 1 - inl[st][1]
        return rel
    def _hlen(st): return len(pr[uniq[st]].header) + ((len(inl[st][2]) + 1 - inl[st][1]) if st in inl else 0)
    pos = len(pr) * 2
    newstart = {}; smap = {}
    for st in order:
        r = pr[uniq[st]]
        newstart[st] = pos
        p = pos + _hlen(st)
        for k, sx in enumerate(newstr[st]):
            smap[r.starts[k]] = p
            p += len(sx) + 1
        pos = p
    if pos > 0xFFFF:
        raise ValueError('file too large for u16 pointers: %d' % pos)
    hdrs = {}
    for st in order:
        h = bytearray(pr[uniq[st]].header)
        if st in inl:
            rel, ol, nt = inl[st]
            h = h[:rel] + bytearray(nt + b'\0') + h[rel + ol:]
        hdrs[st] = h
    for (i, j, v) in slots:
        st_ = pr[i].start
        struct.pack_into('<H', hdrs[st_], _hm(st_, j), smap[v])
    if inline:   # header-internal absolute pointers (title / pointer-array start) follow the record to its new position
        slotpos = set((pr[i].start, j) for (i, j, v) in slots)
        for st in order:
            r = pr[uniq[st]]; oh = r.header; done = set()
            for j in range(0, len(oh) - 1):
                if (st, j) in slotpos: continue
                if st in inl and inl[st][0] <= j < inl[st][0] + inl[st][1]: continue   # inside the inline text itself
                v = struct.unpack_from('<H', oh, j)[0]
                rel = v - r.start
                if 4 <= rel < len(oh) and v not in pstart and (j + 1) not in done and (j - 1) not in done:
                    struct.pack_into('<H', hdrs[st], _hm(st, j), newstart[st] + _hm(st, rel)); done.add(j)
    out = bytearray(struct.pack('<%dH' % len(pr), *[newstart[r.start] for r in pr]))
    for st in order:
        out += hdrs[st]
        for sx in newstr[st]:
            out += sx + b'\0'
    return bytes(out), report


def selftest(psp):
    pr = parse(psp)
    hp = [r.s0 - r.start for r in pr]
    new, rep = rebuild(psp, psp, hp, hp, own=True)
    return new == psp, rep


if __name__ == '__main__':
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    tdir = os.path.join(base, 'orig/psp/kit1/data_3rd/text')
    for f in sorted(os.listdir(tdir)):
        if not f.endswith('._dt'): continue
        d = open(os.path.join(tdir, f), 'rb').read()
        try:
            ok, rep = selftest(d)
        except Exception as e:
            ok, rep = 'ERR %r' % e, {}
        print(f, ok, rep.get('ptr_fixed'))


def fix_town(new):
    """t_town: offset table + rec0 pointer table address a continuous NUL-chunk stream (chunk = optional id byte + text).
    Chunks that are still JP (shop names) are replaced via KEPT_OVERRIDE (suffix match keeps the id byte) and EVERY u16 in the
    pointer region [0,S) that points into the stream is remapped."""
    S = struct.unpack_from('<H', new, 2)[0]
    chunks = new[S:].split(b'\0')
    assert chunks[-1] == b''
    chunks = chunks[:-1]
    old_st = []; p = S
    for c in chunks: old_st.append(p); p += len(c) + 1
    endold = p
    nch = [_ovr(c) for c in chunks]
    new_st = []; p = S
    for c in nch: new_st.append(p); p += len(c) + 1
    import bisect
    def mp(v):
        if v >= endold: return v - endold + p
        k = bisect.bisect_right(old_st, v) - 1
        return new_st[k] + min(v - old_st[k], len(nch[k]))
    hdr = bytearray(new[:S])
    for j in range(0, S - 1, 2):
        v = struct.unpack_from('<H', hdr, j)[0]
        if v >= S: struct.pack_into('<H', hdr, j, mp(v))
    out = bytes(hdr) + b''.join(c + b'\0' for c in nch)
    return out
