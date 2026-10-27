"""pc_extract.py - unpack + DECOMPRESS PC LB DIR/LB DAT archives (ED6_DTxx).
Usage: python pc_extract.py ED6_DT22 outdir     (name WITHOUT extension)
All entries in a .dat are Falcom ed6-framed compressed (verified on DT21: 430/430, DT22: 72/72)."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import falcom_lz as F
from ed6_unpack import read_dir
base, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
dat = open(base + '.dat', 'rb').read(); n = 0
for name, a, flag, b, ts, off in read_dir(base):
    if not a: continue
    out, end = F.ed6_frames(dat[off:off + a])
    open(os.path.join(outdir, name.replace(' ', '')), 'wb').write(out); n += 1
print('extracted', n, 'files to', outdir)
