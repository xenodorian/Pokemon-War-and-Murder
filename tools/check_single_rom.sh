#!/bin/sh
# Guard: exactly one game ROM. Fails if any .gba other than the root release and the Outlaw original exists,
# if the root ROM CRC does not match the last line of ROM_LOG.txt, or if the IPS does not rebuild it.
cd "$(dirname "$0")/.."
OUTLAW="roms/outlaw-2015-09-05 (original hack ROM, from user upload 3ad0b9f8).gba"
bad=$(find . -name '*.gba' -not -path './.git/*' -not -path './PokemonWarAndMurder.gba' -not -path "./$OUTLAW")
if [ -n "$bad" ]; then echo "REFUSED: extra ROM files (only PokemonWarAndMurder.gba and the Outlaw original may exist):"; echo "$bad"; exit 1; fi
python3 - "$OUTLAW" <<'PY' || exit 1
import sys, zlib
d = open('PokemonWarAndMurder.gba', 'rb').read()
crc = '0x%08x' % (zlib.crc32(d) & 0xffffffff)
last = [l for l in open('ROM_LOG.txt') if l.strip() and not l.startswith('#')][-1].split()[0]
if crc != last: print('REFUSED: root ROM CRC %s does not match the last ROM_LOG.txt entry %s' % (crc, last)); sys.exit(1)
b = bytearray(open(sys.argv[1], 'rb').read()); p = open('PokemonWarAndMurder.ips', 'rb').read(); i = 5
while p[i:i + 3] != b'EOF':
    o = int.from_bytes(p[i:i + 3], 'big'); n = int.from_bytes(p[i + 3:i + 5], 'big'); i += 5
    if n == 0: r = int.from_bytes(p[i:i + 2], 'big'); b[o:o + r] = p[i + 2:i + 3] * r; i += 3
    else: b[o:o + n] = p[i:i + n]; i += n
if bytes(b) != d: print('REFUSED: PokemonWarAndMurder.ips does not rebuild PokemonWarAndMurder.gba'); sys.exit(1)
print('single ROM ok', crc)
PY
