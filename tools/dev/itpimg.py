import struct, itp
from PIL import Image
def load(d):
    t=struct.unpack_from('<I',d,0)[0]; w,h=struct.unpack_from('<II',d,4)
    pos=16 if t>=0x3ec else 12
    pal,p,_=itp.block(d,pos)
    o=None
    for q in (p,p+4):
        try:
            hdr=struct.unpack_from('<III',d,q)
            if 2<=hdr[2]<=32 and hdr[1]<=0x400000 and hdr[0]<len(d):
                o,p2,_=itp.block(d,q); break
        except Exception: pass
    return t,w,h,pal,o
def unswizzle(buf,rowbytes,h):
    out=bytearray(rowbytes*h)
    bw=rowbytes//16; src=0
    for by in range(0,h,8):
        for bx in range(bw):
            for r in range(8):
                dst=(by+r)*rowbytes+bx*16
                out[dst:dst+16]=buf[src:src+16]; src+=16
    return bytes(out)
def to_img(d,swz=True):
    t,w,h,pal,o=load(d)
    bpp8=len(o)>=w*h
    rb=w if bpp8 else w//2
    need=rb*h
    buf=o[:need]
    if swz: buf=unswizzle(buf,rb,h)
    if bpp8: idx=list(buf)
    else:
        idx=[]
        for b in buf: idx+=[b&15,b>>4]
    n=len(pal)//4
    im=Image.new('RGBA',(w,h))
    px=[tuple(pal[i*4:i*4+4]) if i<n else (0,0,0,0) for i in range(256)]
    im.putdata([px[i] for i in idx])
    return im
