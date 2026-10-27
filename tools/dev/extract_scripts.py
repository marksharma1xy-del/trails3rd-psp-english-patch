"""
extract_scripts.py - pull ALL story-script archives (map4/*.mc1, ~18.5 MB) out of the PSP ISO.
No 7-Zip needed.

Usage (PowerShell, in the folder that has Trails3rd.iso):
    python extract_scripts.py Trails3rd.iso

Creates scripts1.zip  -> upload it to Claude.
"""
import os, shutil, struct, sys

SECTOR = 2048
PREFIX = "PSP_GAME/USRDIR/data_3rd/map4/"
EXTS = (".mc1",)

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
    out_dir = "scripts1"
    with open(path, "rb") as f:
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        if pvd[1:6] != b"CD001":
            sys.exit("Not a valid ISO9660 image (is it a .CSO?).")
        rl = struct.unpack("<I", pvd[158:162])[0]
        rs = struct.unpack("<I", pvd[166:170])[0]
        entries = []
        walk(f, rl, rs, "", entries)
        picked = [(p, s, l) for p, s, l in entries
                  if p.startswith(PREFIX) and p.lower().endswith(EXTS)]
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        total = 0
        for p, s, l in picked:
            dest = os.path.join(out_dir, os.path.basename(p))
            os.makedirs(out_dir, exist_ok=True)
            f.seek(l * SECTOR)
            with open(dest, "wb") as o:
                o.write(f.read(s))
            total += s
        print("Extracted %d files, %.1f MB" % (len(picked), total / 1048576))
    shutil.make_archive("scripts1", "zip", out_dir)
    print("Created scripts1.zip (%.1f MB) - upload it." % (os.path.getsize("scripts1.zip") / 1048576))

if __name__ == "__main__":
    main()
