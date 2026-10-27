"""mcpack.py - replace one entry of a PSP .mc* archive with new (uncompressed-stored) data."""
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import falcom_lz as F


def replace_entry(mc, name, newdata):
    n = struct.unpack_from('<I', mc, 0)[0]
    ents = [list(struct.unpack_from('<16sIIII', mc, 16 + 32 * i)) for i in range(n)]
    blobs = []; found = False
    for e in ents:
        raw = mc[e[1]:e[1] + e[2]]
        if e[0].split(b'\0')[0].decode('latin1').lower() == name.lower():
            raw = F.psp_pack(newdata); e[2] = len(raw); e[3] = len(newdata); found = True
        blobs.append(raw)
    if not found: raise KeyError(name)
    out = bytearray(struct.pack('<4I', n, n, n, n)); off = 16 + 32 * n
    for e, b in zip(ents, blobs):
        e[1] = off; off += len(b)
        out += struct.pack('<16sIIII', *e)
    for b in blobs: out += b
    return bytes(out)


def get_entry(mc, name):
    n = struct.unpack_from('<I', mc, 0)[0]
    for i in range(n):
        nm, off, ps, us, z = struct.unpack_from('<16sIIII', mc, 16 + 32 * i)
        if nm.split(b'\0')[0].decode('latin1').lower() == name.lower():
            return F.psp_entry(mc[off:off + ps])[0] if us else mc[off:off + ps]
    raise KeyError(name)


def add_entry(mc, name, newdata):
    """append a NEW entry (stored through psp_pack) at the end of the archive"""
    n = struct.unpack_from('<I', mc, 0)[0]
    ents = [list(struct.unpack_from('<16sIIII', mc, 16 + 32 * i)) for i in range(n)]
    blobs = [mc[e[1]:e[1] + e[2]] for e in ents]
    raw = F.psp_pack(newdata)
    ents.append([name.encode('latin1').ljust(16, b'\0'), 0, len(raw), len(newdata), 0]); blobs.append(raw)
    n += 1
    out = bytearray(struct.pack('<4I', n, n, n, n)); off = 16 + 32 * n
    for e, b in zip(ents, blobs):
        e[1] = off; off += len(b)
        out += struct.pack('<16sIIII', *e)
    for b in blobs: out += b
    return bytes(out)
