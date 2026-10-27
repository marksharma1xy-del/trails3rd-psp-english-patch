import struct, sys, itpimg, itp, falcom_lz as L
from PIL import Image
F={'A':'010101111101101','R':'110101110101101','M':'101111111101101','S':'011100010001110','O':'010101101101010','I':'111010010010111',
'T':'111010010010010','E':'111100110100111','C':'011100100100011','V':'101101101101010','N':'110101101101101','F':'111100110100100',
'D':'110101101101110','B':'110101110101110','K':'101101110101101','H':'101101111101101','L':'100100100100111','U':'101101101101111',
'W':'101101111111101','P':'110101110100100','G':'011100101101011','Y':'101101010010010','X':'101101010101101','Z':'111001010100111',
'J':'001001001101010','Q':'010101101111011',' ':'000000000000000','.':'000000000000010','!':'010010010000010'}
def tw(s): return len(s)*4-1
def swz(buf,rb,h):
    out=bytearray(len(buf)); bw=rb//16; dst=0
    for by in range(0,h,8):
        for bx in range(bw):
            for r in range(8):
                s=(by+r)*rb+bx*16; out[dst:dst+16]=buf[s:s+16]; dst+=16
    return bytes(out)
def lum(c): return c[0]*3+c[1]*6+c[2]
def edit(d,tabs_y,labels,x0=1,pitch=32,ya=100,yb=108,xa=4,xb=26,col=None):
    t,w,h,pal,o=itpimg.load(d)
    b=bytearray(itpimg.unswizzle(o,w,h)); P=[tuple(pal[i*4:i*4+4]) for i in range(256)]
    for k,lab in enumerate(labels):
        if lab is None: continue
        bx=x0+pitch*k
        area=[b[y*w+x] for y in range(ya+tabs_y,yb+tabs_y+1) for x in range(bx+xa,bx+xb+1)]
        from collections import Counter
        bg=Counter([b[(ya+tabs_y)*w+x] for x in range(bx+xa,bx+xb+1)]).most_common(1)[0][0]
        fg=max(set(area),key=lambda i:abs(lum(P[i])-lum(P[bg])))
        if col: fg=col
        for y in range(ya+tabs_y,yb+tabs_y+1):
            for x in range(bx+xa,bx+xb+1): b[y*w+x]=bg
        sx=bx+xa+((xb-xa+1)-tw(lab))//2; sy=ya+tabs_y+2
        for ci,ch in enumerate(lab):
            g=F[ch]
            for r in range(5):
                for c in range(3):
                    if g[r*3+c]=='1': b[(sy+r)*w+sx+ci*4+c]=fg
    return bytes(b),(t,w,h,pal)
def rebuild(d,newb,w,h):
    # header 16 + palette block, then pixel block header at p or p+4
    t=struct.unpack_from('<I',d,0)[0]
    pal,p,_=itp.block(d,16)
    q=p
    hdr=struct.unpack_from('<III',d,q)
    if not (2<=hdr[2]<=32 and hdr[0]<len(d)): q=p+4
    pre=d[:q]
    if q!=p: pre=pre[:p]+struct.pack('<I',w*h)
    return pre+L.psp_pack(swz(newb,w,h))
if __name__=='__main__':
    src,dst=sys.argv[1:3]
    d=open(src,'rb').read()
    L1=['ARMS','ARMOR','ITEMS','CASE','EVENT','FOOD','BOOKS','FISH']
    b,(t,w,h,pal)=edit(d,0,L1)
    d1=rebuild(d,b,w,h)
    b,(t,w,h,pal)=edit(d1,16,L1)
    d2=rebuild(d1,b,w,h)
    for ty,lab in ((96,[None]*5+['HEAL','FISH','ITEMS']),(112,[None]*5+['HEAL','FISH','ITEMS']),(128,[None]*7+['BATTLE']),(144,[None]*7+['BATTLE'])):
        b,(t,w,h,pal)=edit(d2,ty,lab); d2=rebuild(d2,b,w,h)
    # second row (blue) at y+16
    open(dst,'wb').write(d2)
    # check
    t2,w2,h2,pal2,o2=itpimg.load(d2)
    assert itpimg.unswizzle(o2,w,h)==b
    open('/tmp/icon1_new.png','wb')
    itpimg.to_img(d2).save('/tmp/icon1_new.png'); print('ok',len(d),len(d2))
