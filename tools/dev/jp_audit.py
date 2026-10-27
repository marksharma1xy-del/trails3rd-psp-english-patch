"""jp_audit.py PY_DIR  -> per scene / per call-name count of string literals that still contain Japanese"""
import re, os, sys, collections
JP = re.compile(r'[぀-ヿ一-鿿＀-￯]')
d = sys.argv[1]; tot = collections.Counter(); per = {}
for fn in sorted(os.listdir(d)):
    if not fn.endswith('.py'): continue
    cur = None; c = collections.Counter(); inbuild = False
    for ln in open(os.path.join(d, fn), encoding='cp932', newline='').read().split('\n'):
        m = re.match(r'\s*(\w+)\(', ln)
        if m: cur = m.group(1)
        if JP.search(ln) and not ln.strip().startswith('#'):
            n = len([s for s in re.findall(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', ln) if JP.search(s)])
            c[cur] += max(n, 1)
    per[fn[:-3]] = c; tot.update(c)
print('TOTAL by call:', dict(tot.most_common()))
rows = sorted(((sum(c.values()), k, dict(c)) for k, c in per.items() if c), reverse=True)
for n, k, c in rows[:40]: print('%-9s %5d %s' % (k, n, c))
print('scenes with JP:', len(rows))
