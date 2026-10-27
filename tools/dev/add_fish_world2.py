"""Append t_world2 map names + t_fish descriptions (JP->EN) to queue/table_en.tsv (idempotent). Fish text from PC T_FISH rec3[220:246], rewrapped to <=4 lines."""
import sys,textwrap,os,glob
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tbl
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
names=open(os.path.join(B,'queue','world2_en.tsv'),encoding='utf-8').read().strip().split('\n')
pairs=[l.split('\t') for l in names]
psp=open(B+'/orig/psp/kit1/data_3rd/text/t_fish._dt','rb').read()
pc=open(B+'/orig/pc_gog_extracted/DT22/T_FISH._DT','rb').read()
pj=[s for s in tbl.parse(psp)[3].strings if s.startswith('　'.encode('cp932'))]
pe=tbl.parse(pc)[3].strings[220:246]
assert len(pj)==len(pe)==26
fish=[]
for j,e in zip(pj,pe):
    t=e.decode('cp932').replace('\\n',' ')
    for w in (38,40,42,44,46,48,50):
        ls=textwrap.wrap(t,w)
        if len(ls)<=4: break
    fish.append((j.decode('cp932'),'\\n'.join(ls)))
f=B+'/queue/table_en.tsv'
have=set(l.split('\t')[0] for l in open(f,encoding='utf-8') if '\t' in l)
with open(f,'a',encoding='utf-8') as o:
    for j,e in pairs+fish:
        if j not in have: o.write(j+'\t'+e+'\n')
print(len(pairs),len(fish))
