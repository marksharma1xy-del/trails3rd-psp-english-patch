# Trails in the Sky the 3rd — PSP English Patch (work in progress)

An unofficial fan English patch for **Trails in the Sky the 3rd** on **PSP** (game ID `ULJM05353`, Japanese release).

> **Status: V0.7 (test build).** All story text, menus, battle text, bestiary, shops and tables are in English.
> **Menu/battle graphics (textures) are still Japanese.** Some parts are not yet confirmed in-game — see [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md).
> Tested in **PPSSPP** only (v1.20.x, Windows 11). Not tested on real PSP hardware.

## What this repository contains

| Folder | What is in it |
|---|---|
| `tools/` | Python tools that build the patched ISO (`build_patch.py` is the main one) |
| `tools/dev/` | Development/research scripts used while making the patch (unpacking, decompiling, auditing). Not needed to use the patch |
| `translation/` | Hand-translated text (Japanese source → English): names, battle text, bestiary, menus, map names, etc. |
| `docs/` | Build guide, known issues, tool overview, full development log |

**This repository does NOT contain** the game, any game files, or the official XSEED English script. See [LEGAL_NOTICE.md](LEGAL_NOTICE.md).

## What you need to use it

You must supply all of these yourself:

1. Your own **Japanese PSP ISO** of the game (`Trails3rd.iso`, ID `ULJM05353`), dumped from a disc you own.
2. The **decrypted `EBOOT.BIN`** from that ISO (optional, but needed for the main-menu text).
3. Your own copy of the **PC version from GOG** (*The Legend of Heroes: Trails in the Sky the 3rd*), specifically `ED6_DT22.dat` and `ED6_DT22.dir`. The builder reads the official English tables from **your** install at build time.
4. **Windows** + **Python 3** (tick "Add python.exe to PATH" when installing).
5. **PPSSPP** to play.

Step-by-step: [docs/HOW_TO_BUILD.md](docs/HOW_TO_BUILD.md)

## Playable build

The compiled English story scripts are **not** stored in this repository. See the *Releases* page for the packaged build kit (if one is published) — see [LEGAL_NOTICE.md](LEGAL_NOTICE.md) for why they are kept separate.

## Credits & licenses

- Code in `tools/`: MIT License — see [LICENSE](LICENSE)
- Hand-translated text in `translation/`: CC BY-NC-SA 4.0 — see [LICENSE-TRANSLATION.md](LICENSE-TRANSLATION.md)
- Everything else, thanks and third-party tools: [CREDITS.md](CREDITS.md)

## Reporting problems

Open an **Issue** on this repository. Please include: the map/scene name, a screenshot, and what you expected to see.
Untranslated Japanese text, garbled lines, text overflowing its box, and crashes are all useful reports.
