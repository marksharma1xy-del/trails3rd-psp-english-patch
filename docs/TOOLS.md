# Tools overview

## `tools/` (used to build)
| File | Purpose |
|---|---|
| `build_patch.py` | Main builder: reads text tables from the ISO and your GOG `ED6_DT22`, writes a patched COPY of the ISO |
| `tbl.py`, `tbl_verify.py` | Rebuild and verify the PSP text tables with English strings |
| `mcpack.py` | Read/replace entries in the game's map archives |
| `eboot_patch.py` | Patch menu text inside the decrypted EBOOT (uses `translation/eboot_dict.txt`) |
| `battle_patch.py`, `monsnote_patch.py` | Same-size in-place patching of battle text and bestiary |
| `fix_monsnote_spaces.py` | Re-pads bestiary entries with spaces (the engine reads them by string length) |
| `ed6_unpack.py` | Unpacks Falcom `LB DIR/LB DAT` archives (e.g. `ED6_DT22`) |
| `falcom_lz.py` | Falcom LZ compression/decompression |
| `port_names.py` | Copies official English character names into aligned scene sources |

## `tools/dev/`
Research and pipeline scripts (script alignment, decompile/compile helpers, texture/ITP extraction, audits). Many have paths from the original working environment and will need editing to run. They are kept for transparency and for continuing development.

## `translation/`
- `table_en.tsv` — Japanese → English overrides for tables (tab-separated)
- `eboot_dict.txt` — `Japanese => English` for the main-menu EBOOT strings
- `hand_translated/` — lines with no official English counterpart (dialogue, names, map names, etc.)
- `battle/` — battle text translations (enemy names, skills, shouts)

Tip for translators: same-size patches matter. For in-place text patches, check whether the engine reads strings by length; if so, pad with spaces rather than NUL bytes (see `DEVELOPMENT_LOG.txt`, sections 52.2–52.4).
