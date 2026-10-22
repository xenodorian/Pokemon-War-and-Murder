#!/bin/sh
# THE way to change the game. usage: tools/patch.sh tools/STAGE.py [stage args]
# Reads PokemonWarAndMurder.gba (the one ROM), runs STAGE.py IN OUT on a scratch copy, and only if that succeeds
# replaces the root ROM, rebuilds PokemonWarAndMurder.ips from the Outlaw original, and logs the new CRC in ROM_LOG.txt.
# Never start from an older ROM. There is no other ROM to start from.
set -e
cd "$(dirname "$0")/.."
sh tools/check_single_rom.sh
STAGE=$1; shift
test -f "$STAGE"
TMP=$(mktemp /tmp/patch_XXXXXX.gba)
python3 "$STAGE" PokemonWarAndMurder.gba "$TMP" "$@"
CRC=$(python3 -c "import sys,zlib; print('0x%08x' % (zlib.crc32(open(sys.argv[1],'rb').read()) & 0xffffffff))" "$TMP")
cp "$TMP" PokemonWarAndMurder.gba; rm -f "$TMP"
python3 tools/mkips.py "roms/outlaw-2015-09-05 (original hack ROM, from user upload 3ad0b9f8).gba" PokemonWarAndMurder.gba PokemonWarAndMurder.ips
echo "$CRC $(basename "$STAGE") $(date -u +%Y-%m-%d)" >> ROM_LOG.txt
sh tools/check_single_rom.sh
