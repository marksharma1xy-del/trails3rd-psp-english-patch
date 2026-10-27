import json,struct,sys
O='/home/claude/ex/9a47cb8a-Trails3rd_handoff_21_partA_1/work/orig/psp/scripts_SN_orig/'; E='/home/claude/ex/7ca4838b-test_kit22/scenes/'
do=json.load(open('/home/claude/s/dump_orig.json')); de=json.load(open('/home/claude/s/dump_en.json'))
def classify(k):
    a,b=do[k],de[k]; ob=open(O+k,'rb').read(); eb=open(E+k,'rb').read()
    f2o={y[0]:x[0] for x,y in zip(a,b)}
    items=[]
    for idx,(x,y) in enumerate(zip(a,b)):
        o=ob[x[0]:x[0]+x[1]]; e=eb[y[0]:y[0]+y[1]]
        if o==e: continue
        if len(o)==len(e):
            ex=set()
            for p in range(len(o)-1):
                v=struct.unpack_from('<H',o,p)[0]; w=struct.unpack_from('<H',e,p)[0]
                if v!=w and w in f2o and f2o[w]==v: ex.add(p); ex.add(p+1)
            if all(i in ex for i in range(len(o)) if o[i]!=e[i]): continue
        items.append((idx,x[0],len(o),e))
    return ob,items
def size_estimate(k):
    ob,items=classify(k)
    inplace=0; blocks=[]  # runs of class C
    holes=[]
    run=[]; 
    for idx,off,lo,e in items:
        le=len(e)
        if le==lo: continue
        if le+3<=lo:
            holes.append(lo-le-3) if lo-le-3>0 else None; continue
        # class C
        holes.append(lo-3) if lo-3>0 else None
        if run and run[-1][1]+run[-1][2]==off and run[-1][0]+1==idx: run.append((idx,off,lo,e))
        else:
            if run: blocks.append(run)
            run=[(idx,off,lo,e)]
    if run: blocks.append(run)
    bsizes=sorted([sum(len(r[3]) for r in b)+3 for b in blocks],reverse=True)
    holes.sort(reverse=True)
    tail=0; hs=holes[:]
    for s in bsizes:
        placed=False
        for i,h in enumerate(hs):
            if h>=s: hs[i]=h-s; placed=True; break
        if not placed: tail+=s
    return len(ob)+tail, len(items), len(blocks), sum(bsizes)
res=[]
for k in sorted(do):
    ns,n,nb,bs=size_estimate(k); res.append((k,ns,n,nb,bs))
over=[r for r in res if r[1]>65535]
print('over',len(over)); 
for r in over: print(r)
print('max',max(r[1] for r in res))

import collections
h=collections.Counter()
for k in sorted(do):
    if k.startswith(('U7000_','U7002_5','U7003_5')): pass
    ob,items=classify(k)
    a=do[k]
    for idx,off,lo,e in items: h[a[idx][2]]+=1
print({hex(k):v for k,v in h.most_common()})
