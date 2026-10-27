"""find_jp_text.py ISO "ラインフォルト社製" - lists every file inside the ISO that contains the Japanese text (Shift-JIS and UTF-8).
Also looks inside .mc* archives (stored/packed entries are NOT decompressed, so only raw hits are reported).  Prints file path + offset."""
import sys, struct
sys.stdout.reconfigure(encoding='utf8')
SECTOR = 2048
def walk(f, lba, size, prefix, out):
    f.seek(lba * SECTOR); data = f.read(size); pos = 0
    while pos < len(data):
        n = data[pos]
        if n == 0: pos = (pos // SECTOR + 1) * SECTOR; continue
        rec = data[pos:pos + n]; pos += n
        elba = struct.unpack('<I', rec[2:6])[0]; esize = struct.unpack('<I', rec[10:14])[0]
        nl = rec[32]; raw = rec[33:33 + nl]
        if raw in (b'\x00', b'\x01'): continue
        name = raw.decode('ascii', 'replace').split(';')[0]
        if rec[25] & 2: walk(f, elba, esize, prefix + name + '/', out)
        else: out[prefix + name] = (esize, elba)
iso, text = sys.argv[1], sys.argv[2]
keys = {'sjis': text.encode('cp932', 'ignore'), 'utf8': text.encode('utf8'), 'utf16': text.encode('utf-16le')}
with open(iso, 'rb') as f:
    f.seek(16 * SECTOR); pvd = f.read(SECTOR)
    rl = struct.unpack('<I', pvd[158:162])[0]; rs = struct.unpack('<I', pvd[166:170])[0]
    files = {}; walk(f, rl, rs, '', files); hits = 0
    for name, (sz, lba) in sorted(files.items()):
        if sz > 120_000_000: continue
        f.seek(lba * SECTOR); d = f.read(sz)
        for enc, k in keys.items():
            i = d.find(k)
            if i >= 0: print('%-6s %s @%d (file size %d)' % (enc, name, i, sz)); hits += 1
    print('files scanned:', len(files), ' hits:', hits)
