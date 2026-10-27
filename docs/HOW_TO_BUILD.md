# How to build the patched ISO (Windows)

The patch is applied to a **copy** of your ISO. Your original ISO is never modified. Your old PPSSPP saves keep working.

## Before you start
1. Install **Python 3** from <https://www.python.org/> — tick **"Add python.exe to PATH"** on the first installer screen.
2. Have these ready:
   - `Trails3rd.iso` — your own Japanese PSP dump (`ULJM05353`)
   - `ULJM05353_EBOOT.BIN` — decrypted EBOOT from that ISO (optional; without it the main-menu text stays Japanese)
   - GOG PC version of *Trails in the Sky the 3rd*: you need `ED6_DT22.dat` and `ED6_DT22.dir` from its install folder

## Easiest way: use the build kit
If a build kit zip (`Trails3rd_V0.7_kit.zip`) is available on the **Releases** page:
1. Unzip it to a folder.
2. Copy into that same folder: `Trails3rd.iso`, `ULJM05353_EBOOT.BIN`, `ED6_DT22.dat`, `ED6_DT22.dir`.
3. Double-click **`RUN_ME.bat`**.
4. When it finishes you get **`Trails3rd_EN.iso`**. Open it in PPSSPP.

If the window says it cannot find something, the message tells you which file is missing and where to put it.

## From this repository (advanced)
This repository has the tools and the hand-translated text, but not the pre-compiled scripts or patched game data (see [LEGAL_NOTICE.md](../LEGAL_NOTICE.md)). The main command is:

```
python tools/build_patch.py Trails3rd.iso ED6_DT22 --out Trails3rd_EN.iso --eboot ULJM05353_EBOOT.BIN --battle <battle folder> --scenes <scenes folder>
```

(`ED6_DT22` = path to the GOG file, with or without `.dat`; `ED6_DT22.dir` must be next to it.)
Run `python tools/build_patch.py` with no arguments to see all options. More details on each tool: [TOOLS.md](TOOLS.md).

## Texture pack (optional)
`texture_pack_battle_wheel_v5.zip` replaces the battle command wheel image. Unzip into PPSSPP's memory-stick folder so you get `PSP/TEXTURES/ULJM05353/`, then in PPSSPP: Settings → Tools → Developer tools → enable **Replace textures**.
If characters turn **blue/flicker**, disable it and report it as an Issue.

## Checking results
After building, load the ISO in PPSSPP and look for leftover Japanese. When reporting: map/scene name + screenshot.
