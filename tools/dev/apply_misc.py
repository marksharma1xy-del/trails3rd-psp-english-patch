"""apply_misc.py ALIGNED_PY_DIR - replace JP Menu / SetChrName / OP_CC / NpcTalk-name string literals using queue/misc.tsv (id,ctx,scene,JP) + queue/misc_en.tsv (id,English).
Matching is by (context call name, JP text without trailing \\x01/\\x02). Run after apply_hand.py."""
import re, os, sys
Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'queue')
JP = re.compile(r'[぀-ヿ一-鿿＀-￯]')
en = {l.split('\t')[0]: l.rstrip('\n').split('\t', 1)[1] for l in open(Q + '/misc_en.tsv', encoding='utf-8') if '\t' in l}
mp = {}
for l in open(Q + '/misc.tsv', encoding='utf-8'):
    p = l.rstrip('\n').split('\t')
    if p[0] in en: mp[(p[1], p[3])] = en[p[0]]
d = sys.argv[1]; n = 0
for fn in sorted(os.listdir(d)):
    if not fn.endswith('.py'): continue
    fp = os.path.join(d, fn); L = open(fp, encoding='cp932', newline='').read().split('\n'); cur = None; ch = False
    for i, ln in enumerate(L):
        m = re.match(r'(\s*)(\w+)\(', ln)
        if m: cur = m.group(2)
        if cur in ('Menu', 'SetChrName', 'OP_CC', 'NpcTalk') and JP.search(ln):
            def rep(mm):
                global n
                s = mm.group(1); core = re.sub(r'(\\x0[12])+$', '', s); tail = s[len(core):]
                v = mp.get((cur, core))
                if v is None: return mm.group(0)
                n += 1; return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + tail + '"'
            new = re.sub(r'"((?:[^"\\]|\\.)*)"', lambda mm: rep(mm) if JP.search(mm.group(1)) else mm.group(0), ln)
            if new != ln: L[i] = new; ch = True
    if ch: open(fp, 'w', encoding='cp932', newline='').write('\n'.join(L))
print('misc strings replaced:', n)
