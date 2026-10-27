"""extract_queue.py PSP_PY_DIR PC_PY_DIR OUT_TSV - list PSP talk calls that have NO PC English pair (need hand translation).
Columns: scene<TAB>idx<TAB>kind<TAB>chr<TAB>speaker<TAB>ntok<TAB>JP text (pages separated by ' ||| ', line breaks by ' / ', codes kept).
idx = index in A.calls(psp .py)  (same index in the aligned .py, because alignment never adds/removes calls)."""
import os, sys, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_scripts as A
psp_d, pc_d, out = sys.argv[1:4]
rows = []; tot = 0
for fn in sorted(os.listdir(psp_d)):
    if not fn.endswith('.py'): continue
    pcp = os.path.join(pc_d, fn)
    if not os.path.exists(pcp): continue
    pt = open(os.path.join(psp_d, fn), encoding='cp932').read(); ct = open(pcp, encoding='cp932', errors='replace').read()
    pcs = A.calls(pt); ccs = A.calls(ct)
    ka = [(c['kind'], c['chr'], c['ntok']) for c in pcs]; kb = [(c['kind'], c['chr'], c['ntok']) for c in ccs]
    sm = difflib.SequenceMatcher(None, ka, kb, autojunk=False); paired = set()
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == 'equal': paired.update(range(a0, a1))
    for i, c in enumerate(pcs):
        tot += 1
        if i in paired: continue
        txt = c['text']
        if not any(ord(ch) > 127 for ch in txt): continue
        spk = c['name'] or ''
        if c['cname']:
            try: spk = eval(pt[c['cname'][0]:c['cname'][1]])
            except Exception: pass
        t = txt.replace('\x03', ' ||| ').replace('\x01', ' / ').replace('\x02', '').replace('\t', ' ').replace('\x07\x00', '')
        rows.append('\t'.join([fn[:-3], str(i), c['kind'], c['chr'], spk, str(c['ntok']), t]))
open(out, 'w', encoding='utf-8').write('\n'.join(rows) + '\n')
print('total calls', tot, 'unpaired JP', len(rows))
