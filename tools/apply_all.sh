#!/bin/sh
# Rebuilds roms/Pokemon War and Murder.gba from the ROM as it was before the 2026-10-13 opening work (git commit 16adfb2).
# usage: tools/apply_all.sh [OUT.gba]     (run from the repo root; needs python3 with keystone, capstone, Pillow, numpy; the harness is not needed)
set -e
OUT=${1:-/tmp/war_and_murder_rebuilt.gba}
T=$(mktemp -d)
git show 16adfb2:"roms/Pokemon War and Murder.gba" > $T/0.gba
python3 tools/cry_open.py $T/0.gba $T/1.gba            # new opening: house, MAX/MASON, no naming screens, Pallet Mason/Anne, Oak robbed, quest text
python3 tools/splat_order.py $T/1.gba $T/2.gba          # blood splatter always under the player
python3 tools/base1_paintings.py $T/2.gba $T/3.gba      # base 1: pictures clipped by plants
python3 tools/base_paintings_clipped.py $T/3.gba $T/4.gba   # bases 2,70..2,77
python3 tools/door_anim.py $T/4.gba $T/5.gba            # base door animation (frees tile slots 1008..1023)
python3 tools/priest_text.py $T/5.gba "$OUT"            # CONFESSION quest text
python3 - "$OUT" <<'PY'
import sys,zlib
d=open(sys.argv[1],'rb').read(); print('rebuilt CRC32',hex(zlib.crc32(d)))
PY
rm -rf $T
