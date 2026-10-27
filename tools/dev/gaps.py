import json
O='/home/claude/ex/9a47cb8a-Trails3rd_handoff_21_partA_1/work/orig/psp/scripts_SN_orig/'; E='/home/claude/ex/7ca4838b-test_kit22/scenes/'
do=json.load(open('/home/claude/s/dump_orig.json')); de=json.load(open('/home/claude/s/dump_en.json'))
def gaps(ins,b):
    g=[]; pos=min(i[0] for i in ins)
    hdr=b[:pos]
    for i in ins:
        if i[0]>pos: g.append(b[pos:i[0]])
        pos=max(pos,i[0]+i[1])
    if pos<len(b): g.append(b[pos:])
    return hdr,g
nh=0; ng=0; samples=[]
for k in sorted(do):
    ob=open(O+k,'rb').read(); eb=open(E+k,'rb').read()
    ho,go=gaps(do[k],ob); he,ge=gaps(de[k],eb)
    if len(ho)!=len(he) and False: pass
    if go!=ge:
        ng+=1; samples.append((k,len(go),len(ge),[len(x) for x in go][:5],[len(x) for x in ge][:5]))
    if ho!=he: nh+=1
print('scenes with header diff',nh,'gaps diff',ng); print(samples[:8])
