"""fix_monsnote_spaces.py JP_monsnote.dt2 NULpadded_monsnote.dt2 OUT : re-pad every shortened string with spaces so strlen == JP strlen."""
import sys
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); out=bytearray(b); pos=0
for part in a.split(b'\0'):
    L=len(part)
    if L and a[pos:pos+L]!=b[pos:pos+L]:
        en=b[pos:pos+L].split(b'\0')[0]; out[pos:pos+L]=en+b' '*(L-len(en))
    pos+=L+1
assert [i for i,c in enumerate(out) if c==0]==[i for i,c in enumerate(a) if c==0]
open(sys.argv[3],'wb').write(out)
