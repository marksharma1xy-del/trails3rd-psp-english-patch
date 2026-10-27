"""battle_chk.py : check queue/battle_en*.tsv (idx<TAB>EN, later files/lines override) vs byte budget of notes/battle_dat_jp_strings.tsv"""
import sys, glob, os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
rows = [l.rstrip('\n').split('\t') for l in open(R + '/notes/battle_dat_jp_strings.tsv', encoding='utf-8')][1:]
en = {}
for f in sorted(glob.glob(R + '/queue/battle_en*.tsv')):
    for l in open(f, encoding='utf-8'):
        l = l.rstrip('\n')
        if '\t' in l:
            i, e = l.split('\t', 1)
            if i.isdigit(): en[int(i)] = e
bad = 0
for i, e in sorted(en.items()):
    b = len(e.encode('cp932', 'replace')); jb = len(rows[i][2].encode('cp932'))
    if b > jb: print('OVER', i, b, jb, e.replace('\\n', '|')); bad += 1
print('translated', len(en), 'of', len(rows), 'over', bad)
