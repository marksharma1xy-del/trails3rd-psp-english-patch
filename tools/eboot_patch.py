"""eboot_patch.py - apply eboot_dict.txt to YOUR decrypted EBOOT (same-length, in place). Ships no game data.
Usage: python eboot_patch.py ULJM05353_EBOOT.BIN OUT_EBOOT.BIN [eboot_dict.txt] [--report]
Rule: each JP string (cp932, NUL-terminated, exact match after strip) is overwritten by ASCII English
      no longer than the JP byte length; the rest is NUL-padded -> all pointers stay valid."""
import sys, os, re
def load_dict(p):
    d = {}
    for ln in open(p, encoding='utf8'):
        ln = ln.rstrip('\r\n')
        if ' => ' not in ln: continue
        jp, en = ln.split(' => ', 1); cv = lambda x: x.replace(chr(92)*2 + 'n', chr(0) + 'LIT').replace(chr(92) + 'n', chr(10)).replace(chr(92) + 't', chr(9)).replace(chr(0) + 'LIT', chr(92) + 'n'); d[cv(jp).strip()] = cv(en)
    return d
def patch(data, d, lo=0x258000, hi=0x26c000, log=print):
    b = bytearray(data); used = set(); n = 0; over = []
    i = lo
    while i < hi:
        j = b.find(b'\0', i)
        if j < 0: break
        s = bytes(b[i:j])
        if len(s) >= 2:
            try: t = s.decode('cp932')
            except Exception: t = None
            if t is not None and t.strip() in d:
                k = t.strip(); en = d[k]
                try: eb = en.encode('cp932')       # allows box-drawing glyphs like the button symbols
                except Exception: eb = en.encode('ascii', 'replace')
                if len(eb) <= len(s):
                    lead = len(s) - len(s.lstrip(b' ')) if s[:1] == b' ' else 0
                    b[i:j] = eb.ljust(len(s), b'\0'); used.add(k); n += 1
                else: over.append((hex(i), len(s), len(eb), en))
        i = j + 1
    return bytes(b), n, used, over
if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    src, dst = a[0], a[1]
    dp = a[2] if len(a) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'eboot_dict.txt')
    data = open(src, 'rb').read()
    if data[:4] != b'\x7fELF': sys.exit('not a decrypted EBOOT (needs ELF header)')
    d = load_dict(dp); out, n, used, over = patch(data, d)
    open(dst, 'wb').write(out); assert len(out) == len(data)
    print('EBOOT strings patched: %d  (dictionary %d, unused %d, too long %d)' % (n, len(d), len(set(d) - used), len(over)))
    if '--report' in sys.argv:
        for o in over: print('TOO LONG', o)
        for k in sorted(set(d) - used): print('UNUSED', k[:50])
