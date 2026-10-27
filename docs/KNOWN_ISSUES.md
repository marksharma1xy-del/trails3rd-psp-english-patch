# Known issues (V0.7)

## Still Japanese
- **Textures/images:** shop category tabs (weapons / armor / food), the "exchange" label, the battle "Move" banner, the intro caption, and the Monolith sub-menu plate.
- **Door prompts / chest messages in 298 map archives** that have no own `sub000.bin` library: they use some other shared library that has not been found. If you see Japanese there, report the map name.
- **Fishing log descriptions** (26 fish): the English text comes from the official PC version and is not stored in this repository. `tools/dev/add_fish_world2.py` can regenerate those lines from your own GOG files (developer use).

## Not confirmed in-game yet
- The V0.7 changes (door prompt / chest line library, newspapers) were verified offline only.
- Star Door "Episode" line may show a truncated `en...` on some entries.
- Bestiary names/stats: fixed offline after a layout bug; in-game confirmation pending.
- Town shop names, world-map area names and fishing-log text: built offline, in-game confirmation pending.
- Battle shouts / skill banners: possible garbled or clipped text — report any.
- Texture pack v5 (battle wheel): result not yet reported. The earlier versions turned characters blue in PPSSPP.

## Not covered
- 29 original battle files that contain Japanese were not shipped and are unverified.
- Real PSP hardware and PPSSPP versions other than 1.20.x are untested.

The complete history and technical detail is in [DEVELOPMENT_LOG.txt](DEVELOPMENT_LOG.txt).
