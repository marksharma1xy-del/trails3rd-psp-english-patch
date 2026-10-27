"""battle_patch.py SRC_DIR OUT_DIR : patch NUL-terminated cp932 strings in battle/dat/*._dt in place (same size).
JP list = notes/battle_dat_jp_strings.tsv (idx=row order after header); EN = queue/battle_en*.tsv (later overrides).
EN bytes must be <= JP bytes (NUL padded). Literal backslash-n stays the 2 chars."""
import sys, os, glob
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
rows = [l.rstrip('\n').split('\t') for l in open(R + '/notes/battle_dat_jp_strings.tsv', encoding='utf-8')][1:]
en = {}
for f in sorted(glob.glob(R + '/queue/battle_en*.tsv')):
    for l in open(f, encoding='utf-8'):
        l = l.rstrip('\n')
        if '\t' in l:
            i, e = l.split('\t', 1)
            if i.isdigit(): en[int(i)] = e
m = {}
for i, r in enumerate(rows):
    if i in en:
        jp = r[2].encode('cp932'); e = en[i].encode('cp932')
        assert len(e) <= len(jp), (i, en[i])
        m[jp] = e
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
nf = ns = 0; hit = set()
for p in sorted(glob.glob(src + '/*')):
    d = bytearray(open(p, 'rb').read()); pos = 0; ch = 0
    for part in bytes(d).split(b'\0'):
        k = 0
        while k < len(part) and k < 3 and part[k] < 0x20: k += 1   # tolerate leading control bytes (monsnote)
        sub = part[k:]; e = m.get(sub)
        if e is not None and sub:
            d[pos + k:pos + len(part)] = e + b'\0' * (len(sub) - len(e)); ch += 1; hit.add(sub)
        pos += len(part) + 1
    assert len(d) == os.path.getsize(p)
    if ch:
        open(os.path.join(out, os.path.basename(p)), 'wb').write(d); nf += 1; ns += ch
print('files changed', nf, 'strings', ns, 'distinct JP hit', len(hit), 'of', len(m))
miss = [k.decode('cp932') for k in m if k not in hit]
print('unmatched', len(miss), miss[:10])
