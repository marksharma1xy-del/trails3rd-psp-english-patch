"""monsnote_probe.py ORIG_dt2 PATCHED_dt2 : list every name/desc string pair (JP => EN) with offsets, and flag records whose NUL layout differs from JP.
Also prints, per bestiary record, the byte shrink of strings between the previous desc and this name (non-zero shrink + NUL padding = broken name, kit35 finding)."""
import re, sys
a = open(sys.argv[1], 'rb').read(); b = open(sys.argv[2], 'rb').read()
nz = lambda x: [i for i, c in enumerate(x) if c == 0]
print('NUL layout identical to JP:', nz(a) == nz(b))
starts = []
for m in re.finditer(rb'\\n', a):
    s = a.rfind(b'\0', 0, m.start()) + 1
    if not starts or starts[-1] != s: starts.append(s)
for k, s in enumerate(starts):
    ns = a.rfind(b'\0', 0, s - 1) + 1
    print(k, ns, a[ns:s - 1].decode('cp932', 'replace'), '=>', b[ns:s - 1].decode('cp932', 'replace').rstrip('\0 '))
