"""port_names.py PSP_PY_DIR PC_PY_DIR ALIGNED_PY_DIR - copy PC English names into BuildStringList of the aligned scene .py
(only entries that are Japanese in PSP and plain ASCII in PC, only when both lists have the same length)."""
import re, ast, sys, os
P = re.compile(r'(BuildStringList\(\r?\n)(.*?)(\r?\n    \))', re.S)
I = re.compile(r"^(\s*)('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")(\s*,)", re.M)
def items(t):
    m = P.search(t)
    return m, [ast.literal_eval(x.group(2)) for x in I.finditer(m.group(2))] if m else []
psp, pc, out = sys.argv[1:4]; changed = 0
for fn in sorted(os.listdir(out)):
    if not fn.endswith('.py'): continue
    n = fn[:-3]
    try:
        a = open(os.path.join(out, fn), encoding='cp932', newline='').read()
        b = open(os.path.join(pc, fn), encoding='cp932', newline='').read()
    except Exception: continue
    ma, x = items(a); mb, y = items(b)
    if not ma or not mb or len(x) != len(y): continue
    k = [0]
    def rep(m):
        i = k[0]; k[0] += 1
        if any(ord(c) > 127 for c in x[i]) and all(ord(c) < 128 for c in y[i]) and "'" not in y[i] and '"' not in y[i] and '\\' not in y[i]:
            return m.group(1) + repr(y[i]) + m.group(3)
        return m.group(0)
    body = I.sub(rep, ma.group(2))
    a2 = a[:ma.start(2)] + body + a[ma.end(2):]
    if a2 != a: open(os.path.join(out, fn), 'w', encoding='cp932', newline='').write(a2); changed += 1
print('scenes with names ported:', changed)
