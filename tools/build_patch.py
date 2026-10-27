"""build_patch.py - make a TEST ISO with English text tables (runs on the USER'S PC; ships no XSEED text, it reads YOUR GOG install).

Usage (PowerShell, in the folder with Trails3rd.iso and these .py files):
    python build_patch.py Trails3rd.iso "C:\\path\\to\\GOG\\ED6_DT22" [--only t_ittxt,t_magic] [--out Trails3rd_EN.iso]
 (the 2nd argument = the GOG file ED6_DT22.dat with or without extension; ED6_DT22.dir must sit next to it)

What it does: reads the PSP text tables from the ISO, reads the matching English tables from your GOG DT22,
rebuilds every PSP table with English strings (PSP binary fields kept, pointers rewritten), APPENDS the new files to the end of a
COPY of the ISO and updates (a) the ISO9660 directory entries, (b) data.lst (sector+size index), (c) the volume size.
The original ISO is never modified.
"""
import os, struct, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import falcom_lz as F
from ed6_unpack import read_dir
import tbl, tbl_verify, mcpack

SECTOR = 2048
TEXT = 'PSP_GAME/USRDIR/data_3rd/text/'
LST = 'PSP_GAME/USRDIR/data.lst'
# tables verified (pointers resolve to PC strings) in sandbox:
DEFAULT = ['t_ittxt', 't_ittxt2', 't_magic', 't_quest', 't_town', 't_quiz01', 't_quiz02', 't_quiz03', 't_quiz04', 't_cook2',
           't_title', 't_name', 't_memo', 't_chain', 't_mg0500', 't_shop', 't_fish', 't_world2'] + ['t_book%02d' % i for i in range(1, 17)]


def walk(f, lba, size, prefix, out):
    f.seek(lba * SECTOR); data = f.read(size); pos = 0
    while pos < len(data):
        n = data[pos]
        if n == 0:
            pos = (pos // SECTOR + 1) * SECTOR; continue
        rec = data[pos:pos + n]; rpos = lba * SECTOR + pos; pos += n
        elba = struct.unpack('<I', rec[2:6])[0]; esize = struct.unpack('<I', rec[10:14])[0]
        nl = rec[32]; raw = rec[33:33 + nl]
        if raw in (b'\x00', b'\x01'): continue
        name = raw.decode('ascii', 'replace').split(';')[0]
        full = prefix + name
        if rec[25] & 2:
            walk(f, elba, esize, full + '/', out)
        else:
            out[full] = (esize, elba, rpos)


def both(v): return struct.pack('<I', v) + struct.pack('>I', v)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    opts = {}
    for x in sys.argv[1:]:
        if x.startswith('--') and '=' in x: opts[x[2:].split('=')[0]] = x.split('=', 1)[1]
    args = sys.argv[1:]
    if '--only' in args: opts['only'] = args[args.index('--only') + 1]
    if '--out' in args: opts['out'] = args[args.index('--out') + 1]
    if '--scenes' in args: opts['scenes'] = args[args.index('--scenes') + 1]
    if '--scene-only' in args: opts['scene_only'] = args[args.index('--scene-only') + 1]
    if '--no-scenes' in args: opts['noscenes'] = '1'
    if '--pre' in args: opts['pre'] = args[args.index('--pre') + 1]
    if '--eboot' in args: opts['eboot'] = args[args.index('--eboot') + 1]
    if '--battle' in args: opts['battle'] = args[args.index('--battle') + 1]
    if '--exclude-file' in args: opts['exclude_file'] = args[args.index('--exclude-file') + 1]
    skip = {opts.get('only'), opts.get('out'), opts.get('scenes'), opts.get('scene_only'), opts.get('exclude_file'), opts.get('pre'), opts.get('eboot'), opts.get('battle')}
    a = [x for x in a if x not in skip]
    if len(a) < 2: sys.exit(__doc__)
    iso, gog = a[0], a[1]
    gog = gog[:-4] if gog.lower().endswith(('.dat', '.dir')) else gog
    out_iso = opts.get('out') or os.path.splitext(iso)[0] + '_EN.iso'
    only = opts['only'].split(',') if opts.get('only') else DEFAULT
    if opts.get('only') == 'none': only = []

    # --- PC English tables
    dat = open(gog + '.dat', 'rb').read(); pc = {}
    for name, sa, flag, sb, ts, off in read_dir(gog):
        if sa:
            pc[name.replace(' ', '').lower()] = F.ed6_frames(dat[off:off + sa])[0]
    print('GOG tables found:', len(pc))

    # --- ISO
    with open(iso, 'rb') as f:
        if f.read(4) == b'CISO': sys.exit('CSO not supported; use plain ISO')
        f.seek(16 * SECTOR); pvd = f.read(SECTOR)
        if pvd[1:6] != b'CD001': sys.exit('not an ISO9660 image')
        rl = struct.unpack('<I', pvd[158:162])[0]; rs = struct.unpack('<I', pvd[166:170])[0]
        files = {}; walk(f, rl, rs, '', files)
        isosize = f.seek(0, 2)
        for k in (LST,):
            if k not in files: sys.exit('missing ' + k)
        shutil.copyfile(iso, out_iso)
    print('copying done ->', out_iso)
    o = open(out_iso, 'r+b')
    # read data.lst
    lsize, llba, _ = files[LST]
    o.seek(llba * SECTOR); lst = bytearray(o.read(lsize))
    nsec = (isosize + SECTOR - 1) // SECTOR
    o.seek(nsec * SECTOR)
    done = []; newtabs = {}
    for t in only:
        key = TEXT + t + '._dt'
        pckey = t + '._dt'
        if key not in files or (pckey not in pc and t != 't_world2'):
            print('skip', t, '(missing in ISO or GOG)'); continue
        osize, olba, rpos = files[key]
        o.seek(olba * SECTOR); psp = o.read(osize)
        try:
            if t == 't_world2':   # PSP-only table: header 8 bytes + name, exact-name replacement
                new = tbl.rebuild_world2(psp); rep = {'replaced': 65, 'kept': 0}
            else:
                if t in ('t_book01', 't_book02'):   # kit41: article 1 of each book had its first 224 bytes mis-detected as a record header -> force plain string records
                    new, rep = tbl.rebuild(psp, pc[pckey], hp=[0] * 10, hc=[0] * 10)
                else:
                    new, rep = tbl.rebuild(psp, pc[pckey], inline=(t == 't_shop'))
            if t == 't_shop':  # last record holds two end-of-file pointers (len, len-2) that must follow the new size
                nb = bytearray(new); ra = tbl.bounds(bytes(nb))[51][0]
                struct.pack_into('<H', nb, ra + 14, len(nb)); struct.pack_into('<H', nb, ra + 16, len(nb) - 2); new = bytes(nb)
                ok, bad = 1, 0
            elif t in ('t_world2', 't_fish'):
                ok, bad = 1, 0
            else:
                ok, bad = tbl_verify.verify(psp, pc[pckey], new)
                if t == 't_town' and not bad: new = tbl.fix_town(new)   # kit38: JP shop-name chunks -> English, pointers remapped
        except Exception as e:
            print('skip', t, 'ERR', e); continue
        if bad:
            print('skip', t, 'verify failed', ok, bad); continue
        # append
        o.seek(nsec * SECTOR); o.write(new)
        pad = (-len(new)) % SECTOR; o.write(b'\0' * pad)
        newlba = nsec; nsec += (len(new) + pad) // SECTOR
        # iso dir record
        o.seek(rpos + 2); o.write(both(newlba)); o.write(both(len(new)))
        # data.lst entry: name8 + size + sector24|ext8
        pat = t.encode().ljust(8, b'\0') + struct.pack('<I', osize)
        i = lst.find(pat)
        if i < 0 or struct.unpack_from('<I', lst, i + 12)[0] & 0xFFFFFF != olba:
            print('WARNING: data.lst entry not found for', t); continue
        ext = lst[i + 15]
        struct.pack_into('<I', lst, i + 8, len(new)); struct.pack_into('<I', lst, i + 12, newlba | (ext << 24))
        done.append((t, osize, len(new))); newtabs[t + '._dt'] = (psp, new)
        print('patched %-10s %6d -> %6d bytes, sector %d (strings ported %d, kept JP %d)' % (t, osize, len(new), newlba, rep['replaced'], rep['kept']))
    # ---- start.dat (kit28): the engine keeps a SECOND, compressed copy of the text tables inside data_3rd/start.dat
    #      (name plates, battle menu use these). Replace those entries with the same English tables.
    for ARC in ('start', 'joutyu'):   # kit31: joutyu.dat also holds a resident copy of t_shop (shop names such as the base/monolith name)
      SD = 'PSP_GAME/USRDIR/data_3rd/' + ARC + '.dat'
      if newtabs and not opts.get('nostart') and SD in files:
        try:
            ssz, slba, srpos = files[SD]
            o.seek(slba * SECTOR); sd = o.read(ssz); new_sd = sd; nrep = 0
            for nm, (oldpsp, newt) in newtabs.items():
                try: cur = mcpack.get_entry(new_sd, nm)
                except KeyError: continue
                if cur != oldpsp:
                    print(ARC + '.dat: %s differs from text/ copy (%d vs %d bytes) - replaced anyway' % (nm, len(cur), len(oldpsp)))
                new_sd = mcpack.replace_entry(new_sd, nm, newt); assert mcpack.get_entry(new_sd, nm) == newt; nrep += 1
            if ARC == 'joutyu' and opts.get('battle'):   # kit35: bestiary text lives in joutyu.dat too (the game reads THIS copy, not the loose monsnote files)
                for mn in ('monsnote.dt1', 'monsnote.dt2'):
                    mp = os.path.join(opts['battle'], mn)
                    if os.path.exists(mp):
                        nd_ = open(mp, 'rb').read()
                        new_sd = mcpack.replace_entry(new_sd, mn, nd_); assert mcpack.get_entry(new_sd, mn) == nd_; nrep += 1
                        print('joutyu.dat: bestiary entry replaced:', mn)
            if nrep == 0: raise Exception('no table copies in this archive (nothing to do)')
            # untouched entries must read back identical
            n0 = struct.unpack_from('<I', sd, 0)[0]
            for i in range(n0):
                nm_ = struct.unpack_from('<16s', sd, 16 + 32 * i)[0].split(b'\0')[0].decode('latin1')
                if nm_.lower() in newtabs or (ARC == 'joutyu' and opts.get('battle') and nm_.lower().startswith('monsnote')): continue
                assert mcpack.get_entry(new_sd, nm_) == mcpack.get_entry(sd, nm_), nm_
            o.seek(nsec * SECTOR); o.write(new_sd); pad = (-len(new_sd)) % SECTOR; o.write(b'\0' * pad)
            newlba = nsec; nsec += (len(new_sd) + pad) // SECTOR
            o.seek(srpos + 2); o.write(both(newlba)); o.write(both(len(new_sd)))
            pat = ARC.encode().ljust(8, b'\0') + struct.pack('<I', ssz)
            i = lst.find(pat)
            while i >= 0 and struct.unpack_from('<I', lst, i + 12)[0] & 0xFFFFFF != slba: i = lst.find(pat, i + 1)
            if i < 0: raise Exception('data.lst entry for ' + ARC + ' not found')
            ext = lst[i + 15]
            struct.pack_into('<I', lst, i + 8, len(new_sd)); struct.pack_into('<I', lst, i + 12, newlba | (ext << 24))
            print('%s.dat patched: %d table copies replaced, %d -> %d bytes, sector %d' % (ARC, nrep, ssz, len(new_sd), newlba))
        except Exception as e:
            print(ARC + '.dat patch SKIPPED:', repr(e))
    # ---- scenes: folder of compiled English ._SN scripts (--scenes DIR, default ./scenes)
    sdir = opts.get('scenes') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scenes')
    low = {k.lower(): (k, v) for k, v in files.items()}
    nscene = 0; npre = 0
    pdir = opts.get('pre') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pre')  # remapped <scene>.pre (code pointers into the new .bin)
    excl = set()
    if opts.get('exclude_file'):  # bisect helper: scene names (one per line / spaces) that stay ORIGINAL Japanese
        excl = set(x.lower() for x in open(opts['exclude_file']).read().replace(',', ' ').split())
        print('excluding', len(excl), 'scenes (kept original)')
    PARENT = {'u7000_1': 'u7000', 'u7000_2': 'u7000', 'u7000_3': 'u7000', 'u7000_4': 'u7000', 'u7000_5': 'u7000', 'u7001_5': 'u7001',
              'u7002_4': 'u7002', 'u7002_5': 'u7002', 'u7003_4': 'u7003', 'u7003_5': 'u7003'}
    if os.path.isdir(sdir) and not opts.get('noscenes'):
        arch = {}   # archive base -> list of scene bases
        for fn in sorted(os.listdir(sdir)):
            if not fn.upper().endswith('._SN'): continue
            base = fn[:-4].lower()
            if base == 'sub000': continue
            if opts.get('scene_only') and base not in opts['scene_only'].lower().split(','): continue
            if base in excl: continue
            arch.setdefault(PARENT.get(base, base), []).append((base, fn))
        xdir = os.path.join(sdir, '..', 'extra') if os.path.isdir(os.path.join(sdir, '..', 'extra')) else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra')
        for ab, scs in sorted(arch.items()):
            key = 'psp_game/usrdir/data_3rd/map4/' + ab + '.mc1'
            if key not in low: continue
            real, (osize, olba, rpos) = low[key]
            o.seek(olba * SECTOR); mc = o.read(osize)
            try:
                new = mc
                for base, fn in scs:
                    d = open(os.path.join(sdir, fn), 'rb').read()
                    new = mcpack.replace_entry(new, base + '.bin', d)
                    assert mcpack.get_entry(new, base + '.bin') == d
                xf = os.path.join(xdir, ab + '__sub000.bin')
                if os.path.isfile(xf):
                    xd = open(xf, 'rb').read()
                    try: mcpack.get_entry(new, 'sub000.bin'); new = mcpack.replace_entry(new, 'sub000.bin', xd)
                    except KeyError: new = mcpack.add_entry(new, 'sub000.bin', xd)
                    assert mcpack.get_entry(new, 'sub000.bin') == xd
                    print('extra script:', ab, len(xd), 'bytes')
                else:   # v0.7: shared SUB000 library (door prompt, Yes/No box, '... was obtained.') English, same size, for archives that carry their own sub000.bin
                    sf = os.path.join(xdir, 'SUB000_EN.bin')
                    if os.path.isfile(sf):
                        try:
                            cur = mcpack.get_entry(new, 'sub000.bin'); sd = open(sf, 'rb').read()
                            if len(cur) == len(sd):
                                new = mcpack.replace_entry(new, 'sub000.bin', sd); assert mcpack.get_entry(new, 'sub000.bin') == sd
                                nsub = globals().get('NSUB', 0) + 1; globals()['NSUB'] = nsub
                        except KeyError: pass
                pf = os.path.join(pdir, ab + '.pre')
                if os.path.isfile(pf):
                    pd = open(pf, 'rb').read(); new = mcpack.replace_entry(new, ab + '.pre', pd); npre += 1
                # readback of every untouched entry
                n0 = struct.unpack_from('<I', mc, 0)[0]
                for i in range(n0):
                    nm_ = struct.unpack_from('<16s', mc, 16 + 32 * i)[0].split(b'\0')[0].decode('latin1')
                    if nm_.lower() in [b + '.bin' for b, _ in scs] + ['sub000.bin']: continue
                    assert mcpack.get_entry(new, nm_) == mcpack.get_entry(mc, nm_), nm_
            except Exception as e:
                print('skip archive', ab, 'ERR', repr(e)); continue
            o.seek(nsec * SECTOR); o.write(new); pad = (-len(new)) % SECTOR; o.write(b'\0' * pad)
            newlba = nsec; nsec += (len(new) + pad) // SECTOR
            o.seek(rpos + 2); o.write(both(newlba)); o.write(both(len(new)))
            pat = ab.encode().ljust(8, b'\0') + struct.pack('<I', osize)
            i = lst.find(pat)
            while i >= 0 and struct.unpack_from('<I', lst, i + 12)[0] & 0xFFFFFF != olba:
                i = lst.find(pat, i + 1)
            if i < 0:
                print('WARNING: data.lst entry not found for', ab); continue
            ext = lst[i + 15]
            struct.pack_into('<I', lst, i + 8, len(new)); struct.pack_into('<I', lst, i + 12, newlba | (ext << 24))
            nscene += len(scs)
        print('SUB000 English library installed in', globals().get('NSUB', 0), 'archives')
        print('scenes patched:', nscene, ' .pre side-files remapped:', npre)
    # ---- EBOOT: same-length English patch of the user's DECRYPTED EBOOT, written in place over SYSDIR/EBOOT.BIN (kit26)
    if opts.get('eboot'):
        try:
            import eboot_patch
            ek = 'PSP_GAME/SYSDIR/EBOOT.BIN'
            eb = open(opts['eboot'], 'rb').read()
            if eb[:4] != b'\x7fELF': raise Exception('EBOOT file is not decrypted (no ELF header)')
            esz, elba, _ = files[ek]
            if len(eb) != esz: raise Exception('size %d != ISO EBOOT size %d' % (len(eb), esz))
            neb, cnt, used, over = eboot_patch.patch(eb, eboot_patch.load_dict(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'eboot_dict.txt')))
            assert len(neb) == len(eb)
            o.seek(elba * SECTOR); o.write(neb)
            print('EBOOT strings patched in place:', cnt, ' (too long, kept JP: %d)' % len(over))
        except Exception as e:
            print('EBOOT patch SKIPPED:', repr(e))
    # ---- BATTLE/DAT enemy text: same-size patched files (tools/battle_patch.py output dir) written in place at their LBA
    if opts.get('battle'):
        nb = 0
        for fn in sorted(os.listdir(opts['battle'])):
            k = 'PSP_GAME/USRDIR/data_3rd/' + ('monsnote/' if fn.startswith('monsnote') else 'text/' if fn.endswith('.txt') else 'battle/dat/') + fn
            if k not in files: print('battle: not in ISO', fn); continue
            nd = open(os.path.join(opts['battle'], fn), 'rb').read()
            bsz, blba, _ = files[k]
            if len(nd) != bsz: print('battle: size mismatch', fn); continue
            o.seek(blba * SECTOR); o.write(nd); nb += 1
        print('battle/dat files patched in place:', nb)
    o.seek(llba * SECTOR); o.write(lst)
    # volume size (PVD offset 80)
    o.seek(16 * SECTOR + 80); o.write(both(nsec))
    o.close()
    print('\nDONE: %s  (%d tables patched). Load it in PPSSPP and open the Items / Orbment / Quest menus.' % (out_iso, len(done)))


if __name__ == '__main__':
    main()
