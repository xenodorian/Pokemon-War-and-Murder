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
# GUARD: 0xabba66b6 is the bedroom release (commit e7f2901). tools/apply_all.sh starts from the older commit 16adfb2, so a
# release built by it drops the bedroom, opening and CONTROLS work. Refuse to replace the bedroom release unless
# ALLOW_RELEASE_OVERWRITE=1 is set on purpose (only after the release base in CURRENT_WORK.md has been switched).
PROTECTED_CRC=0xabba66b6
CUR_CRC=$(python3 -c "import sys,zlib; print(hex(zlib.crc32(open(sys.argv[1],'rb').read()) & 0xffffffff))" PokemonWarAndMurder.gba)
if [ "$CUR_CRC" = "$PROTECTED_CRC" ] && [ -z "$ALLOW_RELEASE_OVERWRITE" ]; then
  echo "REFUSED: the root ROM is the bedroom release ($PROTECTED_CRC). Not replaced. See CURRENT_WORK.md (release lineage)."
  exit 1
fi
echo "publishing $(python3 -c "import sys,zlib; print(hex(zlib.crc32(open(sys.argv[1],'rb').read()) & 0xffffffff))" "$SRC") over $CUR_CRC"
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
