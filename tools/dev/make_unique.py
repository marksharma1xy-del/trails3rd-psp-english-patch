"""make_unique.py - queue/unpaired.tsv -> queue/unique.tsv (id<TAB>scene(first)<TAB>speaker/chr<TAB>JP without codes, pages ' ||| ').
Also writes queue/unique_map.tsv (scene<TAB>idx<TAB>id) used by apply_hand.py. Order: early-game scenes first, big epilogue scenes last. IDs stable once
created: if unique.tsv exists, new texts are only APPENDED."""
import re, os
Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'queue')
LATE = {'U7002_5', 'U7003_4', 'U7003_5', 'U7000_1', 'U7000_3', 'M7001', 'M7408', 'E1000', 'U7000_2', 'U7002_4'}
rows = [l.rstrip('\n').split('\t') for l in open(Q + '/unpaired.tsv', encoding='utf-8')]
rows = [r for r in rows if r[5] == '0']
rows.sort(key=lambda r: (r[0] in LATE, r[0], int(r[1])))
ids = {}; info = {}
up = Q + '/unique.tsv'
if os.path.exists(up):
    for l in open(up, encoding='utf-8'):
        p = l.rstrip('\n').split('\t'); ids[p[3]] = int(p[0]); info[p[3]] = p
n = max(ids.values(), default=0)
mp = []
for r in rows:
    k = re.sub(r'#\d*[A-Za-z]', '', r[6]).strip()
    if k not in ids:
        n += 1; ids[k] = n; info[k] = [str(n), r[0], r[4] or r[3], k]
    mp.append('\t'.join([r[0], r[1], str(ids[k])]))
open(up, 'w', encoding='utf-8').write('\n'.join('\t'.join(v) for v in sorted(info.values(), key=lambda x: int(x[0]))) + '\n')
open(Q + '/unique_map.tsv', 'w', encoding='utf-8').write('\n'.join(mp) + '\n')
print('unique', n, 'calls', len(mp))
