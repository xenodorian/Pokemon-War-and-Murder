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
python3 tools/priest_text.py $T/5.gba $T/6.gba            # CONFESSION quest text
python3 tools/slums_text.py $T/6.gba $T/7.gba             # three lines that mentioned PALLET SLUMS
python3 tools/story_species.py $T/7.gba $T/8.gba          # YVELTAL (254) and MAX (255) species
python3 tools/story_base1.py $T/8.gba $T/9.gba            # Shinigami captive in base 1, crime scenes gated until he is freed
python3 tools/story_anne.py $T/9.gba $T/10.gba            # Anne outside base 1 + scroll choice, FATHER team (native), quest menu entry
python3 tools/story_native.py $T/10.gba $T/10b.gba        # reputation (shop prices, refusal), MAX fights as herself (C code in story/)
python3 tools/story_yveltal.py $T/10b.gba $T/11.gba       # YVELTAL grave in the tower, outcomes, Bloody ending on blackout
python3 tools/moves_extend.py $T/11.gba $T/11m.gba       # three new move slots (355 BITCH SLAP, 356 BALL THROW, 357 HYPERPUNCH), Hitmonchan and LEAF learnsets
python3 tools/anim_throw.py $T/11m.gba $T/11a.gba       # battle animations for the Leaf throw moves (Ball Throw first)
python3 tools/anim_hyperpunch.py $T/11a.gba $T/11a2.gba    # HYPERPUNCH own animation (Mega Punch + Dynamic Punch bodies)
python3 tools/mtmoon_fix.py $T/11a2.gba $T/11b.gba         # Mt. Moon B2F grunt with a lost script pointer
python3 tools/story_viri_native.py $T/11b.gba $T/11c.gba     # native helpers for the Viridian arrest (Max's Pikachu)
python3 tools/story_viridian.py $T/11c.gba $T/11d.gba        # Max, the Viridian arrest, the double battle
python3 tools/story_ambush.py $T/11d.gba $T/11e.gba        # MAX's later RAICHU double battles (Cerulean, Vermilion)
python3 tools/story_nero.py $T/11e.gba "$OUT"              # NERO replaces the General: arrest / execute / crown, father reaction, titles, epilogue cards
python3 - "$OUT" <<'PY'
import sys,zlib
d=open(sys.argv[1],'rb').read(); print('rebuilt CRC32',hex(zlib.crc32(d)))
PY
rm -rf $T
