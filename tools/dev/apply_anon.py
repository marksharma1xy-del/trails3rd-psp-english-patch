"""apply_anon.py ALIGNED_PY_DIR - replace exact JP string literals using queue/anon_en.tsv (JP<TAB>EN, literal \\x01 etc as typed in .py source).
Files are CP932. Run after apply_hand/apply_misc."""
import re, os, sys
Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'queue')
m = {}
for l in open(Q + '/anon_en.tsv', encoding='utf-8'):
    l = l.rstrip('\n')
    if '\t' not in l: continue
    a, b = l.split('\t', 1)
    m[a] = b
L = re.compile(r'"((?:[^"\\]|\\.)*)"')
d = sys.argv[1]; n = 0; used = set()
for fn in sorted(os.listdir(d)):
    if not fn.endswith('.py'): continue
    p = os.path.join(d, fn)
    t = open(p, encoding='cp932', newline='').read()
    def f(mo):
        global n
        k = mo.group(1)
        if k in m:
            used.add(k); n += 1
            return '"' + m[k].replace('"', '\\"') + '"'
        return mo.group(0)
    t2 = L.sub(f, t)
    if t2 != t: open(p, 'w', encoding='cp932', newline='').write(t2.encode('cp932', 'replace').decode('cp932'))
print('anon literals replaced:', n, 'distinct keys used:', len(used), 'of', len(m))
for k in m:
    if k not in used: print('UNUSED', k[:60])
