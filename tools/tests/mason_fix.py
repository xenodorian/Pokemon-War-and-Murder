"""Static check (run from the repo root): python3 tools/tests/mason_fix.py [ROM.gba]
No script pointer may reach the old Outlaw rival strings any more, and the Pokemon Tower 2F rival script must fight MASON record 429.
The Tower scene was also run in the emulator (warp to map 2,61, step on the coord event): MASON's Tower lines, then RIVAL MASON with KADABRA lv 20."""
import os, re, struct, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R)
d = open(sys.argv[1] if len(sys.argv) > 1 else 'PokemonWarAndMurder.gba', 'rb').read()
OLD = {0xeb27d0: 'Tower intro', 0xeb2844: 'Tower talk', 0xeb2930: 'Tower defeat', 0x188a3c: 'Route 22 gate intro', 0x188b29: 'Route 22 gate talk',
       0x18d60a: 'Gramps old fool', 0x18def3: 'homeless dirtbag', 0x18da73: 'Daisy learn', 0x1748ee: 'douchebag', 0x174927: 'He sucks', 0x71c4a1: 'What a jerk', 0x199543: 'Blaine bribe'}
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)
for a, n in OLD.items():
    refs = [hex(m.start()) for m in re.finditer(re.escape(struct.pack('<I', 0x08000000 + a)), d[:0x1100000])]
    check('no live reference to the old line: ' + n, not refs, refs)
for o in (0xeb1c43, 0xeb1c4e, 0xeb1c59):
    check('Tower trainerbattle %x fights 429' % o, d[o] == 0x5c and struct.unpack('<H', d[o + 2:o + 4])[0] == 429)
sys.exit(1 if bad else 0)
