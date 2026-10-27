"""shrink_scene.py PSP_PY ALIGNED_PY OUT_PY TARGET_BYTES_TO_CUT  - revert the talk calls with the largest English growth back to JP
until ~TARGET bytes are saved (for scenes that exceed the 65535-byte limit).  Prints how many calls were reverted."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import align_scripts as A
psp, al, out, cut = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
pt = open(psp, encoding='cp932', newline='').read(); at = open(al, encoding='cp932', newline='').read()
pc = A.calls(pt); ac = A.calls(at)
assert len(pc) == len(ac), (len(pc), len(ac))
g = []
for i, (p, a) in enumerate(zip(pc, ac)):
    ps = pt[p['args'][-1][0]:p['args'][-1][1]]; as_ = at[a['args'][-1][0]:a['args'][-1][1]]
    g.append((len(as_.encode('cp932', 'replace')) - len(ps.encode('cp932', 'replace')), i))
g.sort(reverse=True); sel = []; tot = 0
for d, i in g:
    if tot >= cut or d <= 0: break
    sel.append(i); tot += d
res = at
for i in sorted(sel, reverse=True):
    p, a = pc[i], ac[i]
    res = res[:a['args'][-1][0]] + pt[p['args'][-1][0]:p['args'][-1][1]] + res[a['args'][-1][1]:]
open(out, 'w', encoding='cp932', newline='').write(res)
print(os.path.basename(al), 'reverted', len(sel), 'of', len(pc), 'saved~', tot)
