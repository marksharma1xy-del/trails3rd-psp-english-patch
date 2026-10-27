"""ed6_unpack.py - unpack Falcom 'LB DIR/LB DAT' archives (ED6_DTxx.dir/.dat) of the PC games.
Usage: python ed6_unpack.py ED6_DT22 outdir     (give the name WITHOUT extension; .dir/.dat next to it)
Entry layout (36 bytes, after a 16-byte header 'LB DIR\\x1a\\0' u32 count u32 0):
  name[16] (e.g. 'T_NAME  ._DT'), u32 size_a, u32 flag, u32 size_b, u32 timestamp, u32 offset
"""
import os, struct, sys
def read_dir(p):
    d = open(p + '.dir', 'rb').read()
    assert d[:6] == b'LB DIR', 'not an LB DIR file'
    n = struct.unpack('<I', d[8:12])[0]
    out = []
    for i in range(n):
        e = d[16 + i * 36: 16 + (i + 1) * 36]
        name = e[:16].split(b'\0')[0].decode('ascii', 'replace')
        a, flag, b, ts, off = struct.unpack('<IIIII', e[16:36])
        out.append((name, a, flag, b, ts, off))
    return out
def main():
    base = sys.argv[1]; outdir = sys.argv[2] if len(sys.argv) > 2 else base + '_out'
    ents = read_dir(base); dat = open(base + '.dat', 'rb').read()
    os.makedirs(outdir, exist_ok=True)
    ok = 0
    for name, a, flag, b, ts, off in ents:
        if name == '' or (a == 0 and b == 0): continue
        n = name.replace(' ', '')
        if off + a > len(dat):
            print('skip (not in this .dat):', name, off, a); continue
        open(os.path.join(outdir, n), 'wb').write(dat[off:off + a]); ok += 1
    print('extracted', ok, 'of', len(ents), 'entries to', outdir)
if __name__ == '__main__': main()
