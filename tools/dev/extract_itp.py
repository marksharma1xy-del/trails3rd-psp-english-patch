"""extract_itp.py - pull the image files (.itp) + small packs out of the PSP ISO.
Usage (PowerShell, in the folder with Trails3rd.iso):
    python extract_itp.py Trails3rd.iso
Creates itp_files.zip (about 5-8 MB). Upload that zip to Claude."""
import os, struct, sys, zipfile
SECTOR = 2048
P = "PSP_GAME/USRDIR/data_3rd/"
WANT_DIRS = (P+"battle/", P+"etc/", P+"itp/", P+"system/", P+"minigame/", P+"cooking/")
WANT_FILES = (P+"start.dat", P+"joutyu.dat")
def walk(f, lba, size, prefix, out):
    f.seek(lba*SECTOR); data = f.read(size); pos = 0
    while pos < len(data):
        n = data[pos]
        if n == 0:
            pos = (pos//SECTOR+1)*SECTOR; continue
        rec = data[pos:pos+n]; pos += n
        l = struct.unpack("<I", rec[2:6])[0]; s = struct.unpack("<I", rec[10:14])[0]
        raw = rec[33:33+rec[32]]
        if raw in (b"\x00", b"\x01"): continue
        name = raw.decode("ascii", "replace").split(";")[0]
        if rec[25] & 2: walk(f, l, s, prefix+name+"/", out)
        else: out.append((prefix+name, s, l))
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else input("Path to ISO: ").strip().strip('"')
    with open(path, "rb") as f:
        f.seek(16*SECTOR); pvd = f.read(SECTOR)
        if pvd[1:6] != b"CD001": sys.exit("Not a valid ISO9660 image (is it a .CSO?).")
        ents = []
        walk(f, struct.unpack("<I", pvd[158:162])[0], struct.unpack("<I", pvd[166:170])[0], "", ents)
        n = 0
        with zipfile.ZipFile("itp_files.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for p, s, l in ents:
                low = p.lower()
                if low.endswith((".itp", ".it3", ".pkc", ".da2")) and (p.startswith(WANT_DIRS) or p.startswith(P+"battle")) and s < 3_000_000 \
                   and "/symbol/" not in p and "/monsnote/ca/" not in p and "/effect/texture/" not in p:
                    f.seek(l*SECTOR); z.writestr(p[len(P):], f.read(s)); n += 1
        print("done:", n, "files -> itp_files.zip")
main()
