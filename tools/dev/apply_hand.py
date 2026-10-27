"""apply_hand.py ALIGNED_PY_DIR [--wrap 50] [--rows 3] - apply hand translations (queue/en_*.tsv: id<TAB>English, pages ' ||| ') to the
still-Japanese talk calls of the aligned scene .py files (in place). Mapping from queue/unique_map.tsv (scene, call idx -> id)."""
import os, sys, glob, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_scripts as A
Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'queue')
args = sys.argv[1:]; wrap, rows = 50, 3
if '--wrap' in args: i = args.index('--wrap'); wrap = int(args[i + 1]); del args[i:i + 2]
if '--rows' in args: i = args.index('--rows'); rows = int(args[i + 1]); del args[i:i + 2]
d = args[0]
en = {}
for f in sorted(glob.glob(Q + '/en_*.tsv')):
    for l in open(f, encoding='utf-8'):
        p = l.rstrip('\n').split('\t')
        if len(p) >= 2 and p[0].isdigit() and p[1].strip(): en[int(p[0])] = p[1].strip()
bys = {}
for l in open(Q + '/unique_map.tsv', encoding='utf-8'):
    s, i, u = l.split()
    if int(u) in en: bys.setdefault(s, []).append((int(i), int(u)))
done = 0
for sc, lst in bys.items():
    fp = os.path.join(d, sc + '.py')
    if not os.path.exists(fp): continue
    t = open(fp, encoding='cp932', newline='').read(); cs = A.calls(t); edits = []
    for i, u in lst:
        if i >= len(cs): continue
        c = cs[i]
        if c['ntok'] or not any(ord(ch) > 127 for ch in c['text']): continue  # colour-only tokens are dropped (text replaced as plain)
        pages = [x.strip() for x in en[u].split('|||')]
        pc = '\x03'.join(p.replace(' / ', ' ') + '\x02' for p in pages)
        ln = t.rfind('\n', 0, c['start']) + 1; ind = len(t[ln:c['start']]) - len(t[ln:c['start']].lstrip())
        a, b = c['args'][-1]
        new = A.emit(A.build_text(c['text'], pc, wrap, rows), ind + 4)
        edits.append((a, b, new))
    for a, b, new in sorted(edits, reverse=True):
        lead = t[a:b][:len(t[a:b]) - len(t[a:b].lstrip())]
        t = t[:a] + lead + new + t[b:]; done += 1
    open(fp, 'w', encoding='cp932', newline='').write(t.encode('cp932', 'replace').decode('cp932'))
print('hand-translated calls applied:', done)
