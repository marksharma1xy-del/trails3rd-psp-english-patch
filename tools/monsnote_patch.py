"""monsnote_patch.py IN_DIR OUT_DIR : battle_patch dictionary + queue/monsnote_extra.tsv (JP<TAB>EN, literal \\n kept) applied in place to monsnote.dt2 (same size).
kit36 FIX: the bestiary walks each record by STRLEN, so a shortened English string must keep the JP byte length. After patching, every changed
string is re-padded with SPACES (0x20) instead of NULs; NUL positions end up identical to the JP original (asserted). NUL padding (kit35) gave
blank names / garbage names ('Mines', 'sile Dmg+Faint') / wrong detail pages."""
import sys, os, subprocess
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
subprocess.check_call([sys.executable, R + '/tools/battle_patch.py', sys.argv[1], sys.argv[2]], stdout=subprocess.DEVNULL)
for fn in os.listdir(sys.argv[2]):
    p = os.path.join(sys.argv[2], fn); d = bytearray(open(p, 'rb').read()); n = 0
    for l in open(R + '/queue/monsnote_extra.tsv', encoding='utf-8'):
        j, e = l.rstrip('\n').split('\t'); j = j.encode('cp932'); e = e.encode('cp932'); assert len(e) <= len(j), (j, e)
        i = d.find(j + b'\0')
        while i >= 0:
            d[i:i + len(j)] = e + b'\0' * (len(j) - len(e)); n += 1; i = d.find(j + b'\0', i + 1)
    # re-pad with spaces so every string keeps its JP strlen
    a = open(os.path.join(sys.argv[1], fn), 'rb').read(); pos = 0; m = 0
    for part in a.split(b'\0'):
        L = len(part)
        if L and a[pos:pos + L] != bytes(d[pos:pos + L]):
            en = bytes(d[pos:pos + L]).split(b'\0')[0]; d[pos:pos + L] = en + b' ' * (L - len(en)); m += 1
        pos += L + 1
    assert [i for i, c in enumerate(d) if c == 0] == [i for i, c in enumerate(a) if c == 0], 'NUL layout differs from JP'
    open(p, 'wb').write(d); print(fn, 'extra replaced', n, 'space-padded', m)
