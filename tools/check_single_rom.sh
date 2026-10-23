#!/bin/sh
# Guard: exactly one game ROM. Fails if any .gba other than the root release and the Outlaw original exists,
# if the root ROM CRC does not match the last line of ROM_LOG.txt, or if the IPS does not rebuild it.
cd "$(dirname "$0")/.."
OUTLAW="roms/outlaw-2015-09-05 (original hack ROM, from user upload 3ad0b9f8).gba"
bad=$(find . -name '*.gba' -not -path './.git/*' -not -path './PokemonWarAndMurder.gba' -not -path "./$OUTLAW")
if [ -n "$bad" ]; then echo "REFUSED: extra ROM files (only PokemonWarAndMurder.gba and the Outlaw original may exist):"; echo "$bad"; exit 1; fi
SAVES=$(find . \( -name '*.state*' -o -name '*.srm' -o -name '*.sgm' -o -name '*.sav' -o -name '*.raw' \) -not -path './.git/*' -not -path './saves/ported/new_game_empty_party.raw' -not -path './stage2/shot.raw')
if [ -n "$SAVES" ]; then echo "REFUSED: old save states are banned (the only allowed one is saves/ported/new_game_empty_party.raw, made from the current ROM):"; echo "$SAVES"; exit 1; fi
python3 - "$OUTLAW" <<'PY' || exit 1
import sys, zlib
d = open('PokemonWarAndMurder.gba', 'rb').read()
crc = '0x%08x' % (zlib.crc32(d) & 0xffffffff)
last = [l for l in open('ROM_LOG.txt') if l.strip() and not l.startswith('#')][-1].split()[0]
if crc != last: print('REFUSED: root ROM CRC %s does not match the last ROM_LOG.txt entry %s' % (crc, last)); sys.exit(1)
b = bytearray(open(sys.argv[1], 'rb').read()); p = open('PokemonWarAndMurder.ips', 'rb').read()
W, E = (4, b'EEOF') if p[:5] == b'IPS32' else (3, b'EOF'); i = 5      # IPS32 for the ROM grown past 16 MB (see mkips.py)
while p[i:i + len(E)] != E:
    o = int.from_bytes(p[i:i + W], 'big'); n = int.from_bytes(p[i + W:i + W + 2], 'big'); i += W + 2
    if n == 0: r = int.from_bytes(p[i:i + 2], 'big'); data = p[i + 2:i + 3] * r; i += 3
    else: data = p[i:i + n]; i += n
    if o + len(data) > len(b): b.extend(b'\xff' * (o + len(data) - len(b)))
    b[o:o + len(data)] = data
if bytes(b) != d: print('REFUSED: PokemonWarAndMurder.ips does not rebuild PokemonWarAndMurder.gba'); sys.exit(1)
print('single ROM ok', crc)
PY
