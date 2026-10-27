"""
extract_kit.py - pull the SMALL files Claude needs out of the PSP ISO (no 7-Zip).

Usage (PowerShell):
    python extract_kit.py Trails3rd.iso

Creates folder  kit1\  and a zip  kit1.zip  (about 3-4 MB) - upload kit1.zip.
Contents: data.lst, data_3rd/text/*, data_3rd/system/*, data_3rd/chr/*.txt,
          data_3rd/minigame/*.txt, data_3rd/bgm/bgmtbl.txt,
          data_3rd/battle/dat/* (small battle tables),
          plus 6 sample scenario files from map4 (names are listed in log).
"""
import os
import shutil
import struct
import sys

SECTOR = 2048

WANT_PREFIX = (
    "PSP_GAME/USRDIR/data.lst",
    "PSP_GAME/USRDIR/data_3rd/text/",
    "PSP_GAME/USRDIR/data_3rd/system/",
    "PSP_GAME/USRDIR/data_3rd/battle/dat/",
)
WANT_EXT_IN = {
    "PSP_GAME/USRDIR/data_3rd/chr/": (".txt",),
    "PSP_GAME/USRDIR/data_3rd/minigame/": (".txt",),
    "PSP_GAME/USRDIR/data_3rd/bgm/": (".txt",),
}
# system/pspfont.dat is 650 KB - fine. Skip anything above this size:
MAX_SIZE = 1_500_000
# map4 samples (scenario candidates): first N of each extension type, small only
MAP4 = "PSP_GAME/USRDIR/data_3rd/map4/"
MAP4_SAMPLE_PER_EXT = 2
MAP4_MAX = 300_000


def walk(f, lba, size, prefix, out):
    f.seek(lba * SECTOR)
    data = f.read(size)
    pos = 0
    while pos < len(data):
        n = data[pos]
        if n == 0:
            pos = (pos // SECTOR + 1) * SECTOR
            continue
        rec = data[pos:pos + n]
        pos += n
        l = struct.unpack("<I", rec[2:6])[0]
        s = struct.unpack("<I", rec[10:14])[0]
        raw = rec[33:33 + rec[32]]
        if raw in (b"\x00", b"\x01"):
            continue
        name = raw.decode("ascii", "replace").split(";")[0]
        if rec[25] & 2:
            walk(f, l, s, prefix + name + "/", out)
        else:
            out.append((prefix + name, s, l))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else input("Path to ISO: ").strip().strip('"')
    out_dir = "kit1"
    with open(path, "rb") as f:
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        if pvd[1:6] != b"CD001":
            sys.exit("Not a valid ISO9660 image (is it a .CSO?).")
        rl = struct.unpack("<I", pvd[158:162])[0]
        rs = struct.unpack("<I", pvd[166:170])[0]
        entries = []
        walk(f, rl, rs, "", entries)

        picked = []
        seen_ext = {}
        for p, s, l in entries:
            ok = False
            if s <= MAX_SIZE:
                if any(p.startswith(w) for w in WANT_PREFIX):
                    ok = True
                for d, exts in WANT_EXT_IN.items():
                    if p.startswith(d) and p.lower().endswith(exts):
                        ok = True
            if p.startswith(MAP4) and s <= MAP4_MAX:
                ext = p.rsplit(".", 1)[-1].lower()
                if seen_ext.get(ext, 0) < MAP4_SAMPLE_PER_EXT:
                    seen_ext[ext] = seen_ext.get(ext, 0) + 1
                    ok = True
            if ok:
                picked.append((p, s, l))

        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        total = 0
        for p, s, l in picked:
            dest = os.path.join(out_dir, p.replace("PSP_GAME/USRDIR/", ""))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            f.seek(l * SECTOR)
            with open(dest, "wb") as o:
                o.write(f.read(s))
            total += s
        print("Extracted %d files, %.1f MB" % (len(picked), total / 1048576))

    shutil.make_archive("kit1", "zip", out_dir)
    print("Created kit1.zip (%.1f MB) - upload it." %
          (os.path.getsize("kit1.zip") / 1048576))


if __name__ == "__main__":
    main()
