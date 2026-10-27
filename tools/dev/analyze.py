import json,sys,os,struct
O='/home/claude/ex/9a47cb8a-Trails3rd_handoff_21_partA_1/work/orig/psp/scripts_SN_orig/'; E='/home/claude/ex/7ca4838b-test_kit22/scenes/'
do=json.load(open('/home/claude/s/dump_orig.json')); de=json.load(open('/home/claude/s/dump_en.json'))
tot=0; bad=[]; stats=[]
for k in sorted(do):
    a,b=do[k],de[k]
    if isinstance(a,str) or isinstance(b,str): bad.append((k,'ERR',a if isinstance(a,str) else b)); continue
    if len(a)!=len(b) or any(x[2]!=y[2] for x,y in zip(a,b)): bad.append((k,'MISMATCH',len(a),len(b))); continue
    ob=open(O+k,'rb').read(); eb=open(E+k,'rb').read()
    f2o={y[0]:x[0] for x,y in zip(a,b)}
    nrel=0; relbytes=0; short=0; withbr=0; offonly=0
    for x,y in zip(a,b):
        o=ob[x[0]:x[0]+x[1]]; e=eb[y[0]:y[0]+y[1]]
        if o==e: continue
        if len(o)==len(e):
            d=[i for i in range(len(o)) if o[i]!=e[i]]
            # explained as u16 offset substitution?
            ok=True; i=0
            ex=set()
            for p in range(len(o)-1):
                v=struct.unpack_from('<H',o,p)[0]; w=struct.unpack_from('<H',e,p)[0]
                if v!=w and w in f2o and f2o[w]==v: ex.add(p); ex.add(p+1)
            if all(i in ex for i in d): offonly+=1; continue
        nrel+=1; relbytes+=len(e)+3
        if len(o)<3: short+=1
        if x[3] or y[3]: withbr+=1
    newsize=len(ob)+relbytes
    stats.append((k,len(ob),len(eb),nrel,offonly,short,withbr,newsize))
print('bad',bad[:10],len(bad))
print('scenes',len(stats),'relocated total',sum(s[3] for s in stats),'offonly',sum(s[4] for s in stats))
print('short(<3B) text instrs',sum(s[5] for s in stats),'text instr with branch targets',sum(s[6] for s in stats))
over=[s for s in stats if s[7]>65535]; print('over 65535:',len(over)); 
for s in over: print(s)
print('max newsize',max(s[7] for s in stats))
