"""Falcom 'bzip' decompressor (port of Aureole-Suite/falcompress, ed6 framing)."""
import struct

class _Bits:
    def __init__(s, d, pos=0):
        s.d = d; s.p = pos; s.bits = 0; s.nb = 0
    def u8(s):
        v = s.d[s.p]; s.p += 1; return v
    def u16(s):
        v = s.d[s.p] | (s.d[s.p+1] << 8); s.p += 2; return v
    def renew(s):
        s.bits = s.u16(); s.nb = 1
    def bit(s):
        if s.nb == 0: s.renew()
        v = (s.bits & s.nb) != 0
        s.nb = (s.nb << 1) & 0xFFFF
        return v
    def nbits(s, n):
        x = 0
        for _ in range(n % 8): x = (x << 1) | int(s.bit())
        for _ in range(n // 8): x = (x << 8) | s.u8()
        return x
    def count(s):
        if s.bit(): return 2
        if s.bit(): return 3
        if s.bit(): return 4
        if s.bit(): return 5
        if s.bit(): return 6 + s.nbits(3)
        return 14 + s.nbits(8)

def _rep(out, n, o):
    if not (1 <= o <= len(out)): raise ValueError("bad repeat o=%d len=%d" % (o, len(out)))
    for _ in range(n): out.append(out[-o])

def mode2(chunk, out):
    # chunk starts with first byte 0 (part of the 16-bit flag word)
    b = _Bits(chunk); b.renew(); b.nb <<= 8
    base = len(out)
    while True:
        if not b.bit():
            out.append(b.u8())
        elif not b.bit():
            o = b.nbits(8); n = b.count(); _rep2(out, base, n, o)
        else:
            o = b.nbits(13)
            if o == 0: break
            if o == 1:
                n = b.nbits(12) if b.bit() else b.nbits(4)
                v = b.u8(); out.extend([v] * (14 + n))
            else:
                n = b.count(); _rep2(out, base, n, o)

def _rep2(out, base, n, o):
    if not (1 <= o <= len(out) - base): raise ValueError("bad repeat")
    for _ in range(n): out.append(out[-o])

def mode1(chunk, out):
    p = 0; last_o = 0; base = len(out)
    while p < len(chunk):
        c = chunk[p]; p += 1
        if c >> 6 == 0:
            n = c & 31
            if c & 32: n = (n << 8) | chunk[p]; p += 1
            out.extend(chunk[p:p+n]); p += n
        elif c >> 5 == 2:
            n = c & 15
            if c & 16: n = (n << 8) | chunk[p]; p += 1
            v = chunk[p]; p += 1; out.extend([v] * (4 + n))
        elif c >> 5 == 3:
            _rep2(out, base, c & 31, last_o)
        else:
            nn = (c >> 5) & 3; last_o = ((c & 31) << 8) | chunk[p]; p += 1
            _rep2(out, base, 4 + nn, last_o)

def decompress_chunk(chunk, out):
    (mode2 if chunk[0] == 0 else mode1)(chunk, out)

def ed6_frames(data, pos=0, limit=None):
    """ed6 framing: repeat [u16 len(incl itself)][chunk][u8 more]. Returns (bytes, endpos)."""
    out = bytearray()
    while True:
        ln = struct.unpack_from('<H', data, pos)[0]
        chunk = data[pos+2:pos+ln]; pos += ln
        decompress_chunk(chunk, out)
        more = data[pos]; pos += 1
        if more == 0: break
    return bytes(out), pos

def psp_entry(data):
    """PSP .mc* entry: [u32 in][u32 out][u32 mode] + ed6 frames. Returns bytes of length out."""
    inn, outsz, mode = struct.unpack_from('<III', data, 0)
    out = bytearray(); pos = 12
    while len(out) < outsz:
        ln = struct.unpack_from('<H', data, pos)[0]
        decompress_chunk(data[pos+2:pos+ln], out); pos += ln
        more = data[pos]; pos += 1
        if more == 0: break
    return bytes(out[:outsz]), len(out)


def _mode2_literals(part):
    """Encode `part` as ONE mode-2 (bit-stream) chunk made only of literals (no compression). PSP entries only use mode 2."""
    out = bytearray(b'\0\0'); st = {'f': 0, 'bits': 0, 'nb': 0x100}
    def bit(v):
        if st['nb'] == 0:
            st['f'] = len(out); out.extend(b'\0\0'); st['bits'] = 0; st['nb'] = 1
        if v: st['bits'] |= st['nb']
        out[st['f']] = st['bits'] & 255; out[st['f'] + 1] = st['bits'] >> 8
        st['nb'] = (st['nb'] << 1) & 0xFFFF
    for b in part:
        bit(0); out.append(b)
    bit(1); bit(1)
    for _ in range(5): bit(0)
    out.append(0)
    return bytes(out)


def psp_store(data):
    """PSP entry holding `data` UNCOMPRESSED but in mode-2 literal chunks (the only mode PSP originals use).
    [u32 in][u32 out][u32 2] + frames + the 8-byte end frame the originals carry."""
    frames = bytearray(); pos = 0
    while pos < len(data):
        part = data[pos:pos + 30000]; pos += len(part)
        chunk = _mode2_literals(part)
        frames += struct.pack('<H', len(chunk) + 2) + chunk + b'\x01'
    frames += struct.pack('<H', 6) + bytes([0, 6, data[0] if data else 0, 0]) + b'\x00'
    body = struct.pack('<II', len(data), 2) + frames
    return struct.pack('<I', len(body)) + body


# ---------------------------------------------------------------- real (greedy LZ77) mode-2 compressor
def _mode2_compress(part):
    """Encode `part` as ONE mode-2 chunk with LZ matches (inverse of mode2())."""
    out = bytearray(b'\0\0'); st = {'f': 0, 'bits': 0, 'nb': 0x100}
    def bit(v):
        if st['nb'] == 0:
            st['f'] = len(out); out.extend(b'\0\0'); st['bits'] = 0; st['nb'] = 1
        if v: st['bits'] |= st['nb']
        out[st['f']] = st['bits'] & 255; out[st['f'] + 1] = st['bits'] >> 8
        st['nb'] = (st['nb'] << 1) & 0xFFFF
    def nbits(x, n):
        for i in range(n % 8 - 1, -1, -1): bit((x >> (n // 8 * 8 + i)) & 1)
        for i in range(n // 8 - 1, -1, -1): out.append((x >> (8 * i)) & 255)
    def count(n):
        if n == 2: bit(1)
        elif n == 3: bit(0); bit(1)
        elif n == 4: bit(0); bit(0); bit(1)
        elif n == 5: bit(0); bit(0); bit(0); bit(1)
        elif n <= 13: bit(0); bit(0); bit(0); bit(0); bit(1); nbits(n - 6, 3)
        else: bit(0); bit(0); bit(0); bit(0); bit(0); nbits(n - 14, 8)
    N = len(part); i = 0; head = {}
    def key(p): return part[p:p + 3]
    MAXL = 14 + 255
    while i < N:
        bl = 0; bo = 0
        if i + 3 <= N:
            cands = head.get(key(i), ())
            for p in reversed(cands[-24:]):
                o = i - p
                if o > 8191: break
                l = 0
                while i + l < N and l < MAXL and part[p + l] == part[i + l]: l += 1   # overlap allowed
                if l > bl or (l == bl and o < bo): bl, bo = l, o
                if bl == MAXL: break
        short = bo <= 255
        need = 3 if short else 4
        if bl >= need and not (bo < 2 and not short):
            bit(1)
            if short: bit(0); nbits(bo, 8)
            else: bit(1); nbits(bo, 13)
            count(bl)
            adv = bl
        else:
            bit(0); out.append(part[i]); adv = 1
        for j in range(i, min(i + adv, N - 2)):
            head.setdefault(key(j), []).append(j)
        i += adv
    bit(1); bit(1)
    for _ in range(5): bit(0)
    out.append(0)
    return bytes(out)


def psp_pack(data, part_size=40000):
    """Like psp_store but really compresses (mode 2)."""
    frames = bytearray(); pos = 0
    while pos < len(data):
        part = data[pos:pos + part_size]; pos += len(part)
        chunk = _mode2_compress(part)
        frames += struct.pack('<H', len(chunk) + 2) + chunk + b'\x01'
    frames += struct.pack('<H', 6) + bytes([0, 6, data[0] if data else 0, 0]) + b'\x00'
    body = struct.pack('<II', len(data), 2) + frames
    return struct.pack('<I', len(body)) + body
