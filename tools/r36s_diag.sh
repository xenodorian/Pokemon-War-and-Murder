#!/bin/sh
# Read-only diagnostic for the R36S (ArkOS / RetroArch). Run it on the console (SSH or a terminal) and send back the output file.
# usage: sh r36s_diag.sh   -> writes r36s_diag.txt in the current directory
# It changes nothing. It looks for every file whose name mentions the game, the RetroArch per-game remaps, overrides and core
# options for those names, the EmulationStation entries, and which core the last run used.
OUT=r36s_diag.txt
: > "$OUT"
say() { printf '%s\n' "$*" >> "$OUT"; }
say "== r36s_diag $(date) =="
say "uname: $(uname -a)"
say "== games and files whose names mention War or Murder (name, size, modified)"
find / -xdev \( -path /proc -o -path /sys \) -prune -o \( -iname '*war*murder*' -o -iname '*pokemonwar*' -o -iname 'pokemon war*' \) -print 2>/dev/null | while read -r f; do
  [ -e "$f" ] && say "$(ls -ld --time-style=long-iso "$f" 2>/dev/null)"
done
say "== RetroArch remaps, overrides and core options that mention the game"
for base in /home/ark/.config/retroarch /root/.config/retroarch /opt/retroarch /storage/.config/retroarch; do
  [ -d "$base" ] || continue
  say "-- base $base"
  find "$base" \( -iname '*.rmp' -o -iname '*.cfg' -o -iname '*.opt' \) 2>/dev/null | grep -i -E 'war|murder' | while read -r f; do
    say "FILE $f ($(ls -l --time-style=long-iso "$f" 2>/dev/null | cut -d' ' -f6-7))"
    say "$(head -c 1500 "$f" 2>/dev/null)"
    say "--"
  done
  say "-- remap folders (names only)"
  ls -R "$base/config/remaps" 2>/dev/null | head -40 >> "$OUT"
done
say "== folders that hold a copy of the game (content-directory remaps and overrides are named after these)"
find / -xdev \( -path /proc -o -path /sys \) -prune -o \( -iname '*war*murder*.gba' -o -iname 'pokemonwar*.gba' -o -iname 'pokemon war*.gba' \) -print 2>/dev/null | while read -r f; do d=$(dirname "$f"); say "$f -> folder name: $(basename "$d")"; done
say "== ALL remap and override files for the GBA cores (any name), with contents"
for base in /home/ark/.config/retroarch /root/.config/retroarch /opt/retroarch /storage/.config/retroarch; do
  for sub in config/remaps config; do
    [ -d "$base/$sub" ] || continue
    find "$base/$sub" -maxdepth 2 \( -iname '*.rmp' -o -iname '*.cfg' -o -iname '*.opt' \) 2>/dev/null | grep -i -E 'gpsp|mgba|gba' | while read -r f; do
      say "FILE $f ($(ls -l --time-style=long-iso "$f" 2>/dev/null | cut -d' ' -f6-7))"; head -c 1500 "$f" >> "$OUT" 2>/dev/null; say "--"
    done
  done
done
say "== EmulationStation game list entries (alternative emulator lines)"
find / -xdev \( -path /proc -o -path /sys \) -prune -o -name 'gamelist.xml' -print 2>/dev/null | while read -r g; do
  if grep -qi -E 'war|murder' "$g" 2>/dev/null; then
    say "-- $g ($(ls -l --time-style=long-iso "$g" | cut -d' ' -f6-7))"
    grep -i -B3 -A12 -E 'war|murder' "$g" 2>/dev/null | head -60 >> "$OUT"
  fi
done
say "== system default emulator for GBA (es_systems / es_settings)"
grep -i -A8 -E '<name>gba</name>|alt' /etc/emulationstation/es_systems.cfg 2>/dev/null | head -30 >> "$OUT"
find / -xdev -name 'es_settings.cfg' 2>/dev/null | while read -r s; do say "-- $s"; grep -i -E 'gba|emu' "$s" 2>/dev/null | head -10 >> "$OUT"; done
say "== last RetroArch log lines naming the core and the content"
find / -xdev -name 'retroarch*.log' 2>/dev/null | head -3 | while read -r l; do
  say "-- $l ($(ls -l --time-style=long-iso "$l" | cut -d' ' -f6-7))"
  grep -i -E 'libretro|core|content|loading|remap|override|input' "$l" 2>/dev/null | tail -25 >> "$OUT"
done
say "== done"
echo "Wrote $OUT. Send it back."
