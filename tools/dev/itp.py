import struct, falcom_lz as L
def block(d,pos):
    inn,out,mode=struct.unpack_from('<III',d,pos)
    p=pos+12; o=bytearray()
    while True:
        ln=struct.unpack_from('<H',d,p)[0]
        L.decompress_chunk(d[p+2:p+ln],o); p+=ln
        more=d[p]; p+=1
        if more==0: break
    return bytes(o[:out]),p,(inn,out,mode)
def parse(d):
    t,w,h=struct.unpack_from('<III',d,0)
    ex=struct.unpack_from('<I',d,12)[0] if t>=0x3ec else None
    blocks=[];p=12+(4 if t>=0x3ec else 0)
    while p+12<=len(d):
        try:
            o,p2,hd=block(d,p)
        except Exception as e:
            blocks.append(('ERR',p,str(e)));break
        blocks.append((hd,p,p2,o)); p=p2
    return t,w,h,ex,blocks,len(d)
if __name__=='__main__':
    import sys
    for f in sys.argv[1:]:
        d=open(f,'rb').read()
        t,w,h,ex,b,n=parse(d)
        print(f,hex(t),w,h,'extra',ex,'len',n)
        for x in b:
            print('  ',x[:3] if x[0]!='ERR' else x, (len(x[3]) if x[0]!='ERR' else ''))

def decode(d):
    """returns (w,h,palette[list of RGBA],indices bytes (w*h), bpp, extra_tail)"""
    t,w,h,ex,b,n=parse(d)
    return t,w,h,ex,b
