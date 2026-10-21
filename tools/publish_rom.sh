#!/bin/sh
# GitROMs looks each release name up on its own (accents ignored, spaces not).
# Only PokemonWarAndMurder.gba is published (the "Pokemon War.gba" copy was removed 2026-10-21).
# Do not also write roms/Pokemon War and Murder.gba.
# A second copy of that older name went stale, got the next patch, and was then copied back over the real game.
# usage: tools/publish_rom.sh built.gba
set -e
cd "$(dirname "$0")/.."
SRC=$1
test -n "$SRC" && test -f "$SRC"
cp "$SRC" PokemonWarAndMurder.gba
rm -f "roms/Pokemon War and Murder.gba"
BASE=""
for c in /home/claude/work/orig_for_patch.gba "roms/outlaw-2015-09-05 (original hack ROM, from user upload 3ad0b9f8).gba"; do
  if [ -f "$c" ]; then BASE=$c; break; fi
done
if [ -n "$BASE" ]; then
  python3 tools/mkips.py "$BASE" PokemonWarAndMurder.gba "Pokemon War and Murder.ips"
  cp "Pokemon War and Murder.ips" PokemonWarAndMurder.ips
fi
python3 - "PokemonWarAndMurder.gba" <<'PY'
import sys, zlib
for name in sys.argv[1:]:
    d = open(name, 'rb').read()
    print('updater ROM', name, len(d), hex(zlib.crc32(d) & 0xffffffff))
PY
