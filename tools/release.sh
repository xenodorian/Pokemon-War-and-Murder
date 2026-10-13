#!/bin/sh
# usage: tools/release.sh   (repo root) rebuilds the ROM with apply_all.sh, writes roms/ and the IPS patch (needs /home/claude/work/orig_for_patch.gba = the original hack ROM CRC 5e460b23)
set -e
sh tools/apply_all.sh /tmp/war_release.gba > /tmp/war_release.log 2>&1 || { tail -20 /tmp/war_release.log; exit 1; }
tail -1 /tmp/war_release.log
cp /tmp/war_release.gba "roms/Pokemon War and Murder.gba"
python3 tools/mkips.py /home/claude/work/orig_for_patch.gba "roms/Pokemon War and Murder.gba" "Pokemon War and Murder.ips"
md5sum "roms/Pokemon War and Murder.gba"
