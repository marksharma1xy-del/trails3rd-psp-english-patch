"""make_fakegp.py DIR - build a fake 'game folder' of ED6_DT00..7F.dir so EDDecompiler can run without the PC game
(it only needs the .dir name tables for chip/portrait names; real DT21/DT22 .dir are used if present in orig/pc_gog)."""
import os, shutil, struct, sys
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__)); real = os.path.join(here, '..', 'orig', 'pc_gog')
for i in range(0x80):
    n = 'ED6_DT%02X' % i
    if i in (0x21, 0x22) and os.path.exists(os.path.join(real, n + '.dir')):
        shutil.copy(os.path.join(real, n + '.dir'), os.path.join(out, n + '.dir')); continue
    b = b'LB DIR\x1a\x00' + struct.pack('<II', 4000, 0)
    for k in range(4000): b += ('x%04d._CH' % k).encode().ljust(16, b'\0') + b'\0' * 20
    open(os.path.join(out, n + '.dir'), 'wb').write(b)
