"""apply_names.py ALIGNED_PY_DIR - translate remaining JP entries inside BuildStringList(...) using queue/names_en.tsv (JP<TAB>EN). CP932 files. Run after port_names."""
import re, os, sys
Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'queue')
m = dict(l.rstrip('\n').split('\t', 1) for l in open(Q + '/names_en.tsv', encoding='utf-8') if '\t' in l)
P = re.compile(r'(BuildStringList\(\r?\n)(.*?)(\r?\n    \))', re.S)
I = re.compile(r"^(\s*)'((?:[^'\\]|\\.)*)'(\s*,)", re.M)
d = sys.argv[1]; n = 0; miss = set()
for fn in sorted(os.listdir(d)):
    if not fn.endswith('.py'): continue
    p = os.path.join(d, fn); t = open(p, encoding='cp932', newline='').read()
    mo = P.search(t)
    if not mo: continue
    def f(x):
        global n
        s = x.group(2)
        if s in m: n += 1; return x.group(1) + "'" + m[s].replace("'", "\\'") + "'" + x.group(3)
        if re.search(r'[぀-ヿ一-鿿＀-￯]', s): miss.add(s)
        return x.group(0)
    body = I.sub(f, mo.group(2))
    t2 = t[:mo.start(2)] + body + t[mo.end(2):]
    if t2 != t: open(p, 'w', encoding='cp932', newline='').write(t2.encode('cp932', 'replace').decode('cp932'))
print('names replaced:', n, 'missing:', sorted(miss))
