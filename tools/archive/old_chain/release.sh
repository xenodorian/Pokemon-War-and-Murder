#!/bin/sh
# usage: tools/release.sh   (repo root) rebuilds the ROM with apply_all.sh, then tools/publish_rom.sh
# publish_rom.sh writes PokemonWarAndMurder.gba at the repo root, the only release ROM. GitROMs updates it by name.
# The Outlaw base for the IPS is orig_for_patch.gba (CRC 5e460b23) or the copy in roms/.
set -e
sh tools/apply_all.sh /tmp/war_release.gba > /tmp/war_release.log 2>&1 || { tail -20 /tmp/war_release.log; exit 1; }
tail -1 /tmp/war_release.log
sh tools/publish_rom.sh /tmp/war_release.gba
