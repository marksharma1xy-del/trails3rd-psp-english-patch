"""
list_iso.py - list files in a PSP ISO and extract the small files Claude needs.
No 7-Zip, no pip installs. Needs only Python 3.

Usage (PowerShell):
    python list_iso.py "C:\\path\\to\\TheThird.iso"

Creates (next to the script):
    filelist.txt        full file list (path, size, sector)
    upload_me\\         PARAM.SFO, EBOOT.BIN (if found) - upload these to Claude
"""
import os
import struct
import sys

SECTOR = 2048
EXTRACT = ("PSP_GAME/PARAM.SFO", "PSP_GAME/SYSDIR/EBOOT.BIN")


def read_sector_range(f, lba, size):
    f.seek(lba * SECTOR)
    return f.read(size)


def walk(f, lba, size, prefix, out):
    data = read_sector_range(f, lba, size)
    pos = 0
    while pos < len(data):
        rec_len = data[pos]
        if rec_len == 0:  # padding to next sector
            pos = (pos // SECTOR + 1) * SECTOR
            continue
        rec = data[pos:pos + rec_len]
        pos += rec_len
        ext_lba = struct.unpack("<I", rec[2:6])[0]
        ext_size = struct.unpack("<I", rec[10:14])[0]
        flags = rec[25]
        name_len = rec[32]
        raw = rec[33:33 + name_len]
        if raw in (b"\x00", b"\x01"):  # "." and ".."
            continue
        name = raw.decode("ascii", "replace").split(";")[0]
        full = prefix + name
        if flags & 2:
            out.append((full + "/", 0, ext_lba))
            walk(f, ext_lba, ext_size, full + "/", out)
        else:
            out.append((full, ext_size, ext_lba))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else input("Path to ISO: ").strip().strip('"')
    if not os.path.isfile(path):
        sys.exit("File not found: " + path)

    with open(path, "rb") as f:
        magic = f.read(4)
        if magic == b"CISO":
            sys.exit("This is a .CSO (compressed) file. Please use a plain .ISO "
                     "(convert with maxcso or PSP tools, or dump it as ISO).")
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        if pvd[1:6] != b"CD001":
            sys.exit("Not a valid ISO9660 image.")
        root = pvd[156:190]
        root_lba = struct.unpack("<I", root[2:6])[0]
        root_size = struct.unpack("<I", root[10:14])[0]

        entries = []
        walk(f, root_lba, root_size, "", entries)

        with open("filelist.txt", "w", encoding="utf-8") as fl:
            fl.write("%-70s %12s %10s\n" % ("PATH", "SIZE", "SECTOR"))
            for p, s, l in entries:
                fl.write("%-70s %12d %10d\n" % (p, s, l))
        print("Wrote filelist.txt (%d entries)" % len(entries))

        os.makedirs("upload_me", exist_ok=True)
        lookup = {p.upper(): (s, l) for p, s, l in entries}
        for target in EXTRACT:
            hit = lookup.get(target.upper())
            if not hit:
                print("Not found:", target)
                continue
            size, lba = hit
            dest = os.path.join("upload_me", os.path.basename(target))
            f.seek(lba * SECTOR)
            with open(dest, "wb") as o:
                remaining = size
                while remaining > 0:
                    chunk = f.read(min(remaining, 1 << 20))
                    if not chunk:
                        break
                    o.write(chunk)
                    remaining -= len(chunk)
            print("Extracted %s (%.1f MB)" % (dest, size / 1048576))

    print("\nDone. Upload filelist.txt and the files in the upload_me folder.")


if __name__ == "__main__":
    main()
