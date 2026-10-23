"""Static check (run from the repo root): python3 tools/tests/gvars_pool.py [ROM.gba]
The 9 compiled copies of g_vars (shot/killed/blessed bit store, 64 vars) must be identical, hold 64 distinct vars and none of the vars other code owns
(story 0x4090..0x409C, quest-log 0x40A2..0x40A6, TRACK 0x40A0, deal/liberty/JH 0x40AA..0x40B5, army 0x40E0..0x40E3, rob.c 0x40E4..0x40E9, story 0x40EA..0x40F8, army 0x40F9..0x40FF).
Also checks the signed liberty compare in deal_info (ldrsh + blt)."""
import os, struct, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R)
d = open(sys.argv[1] if len(sys.argv) > 1 else 'PokemonWarAndMurder.gba', 'rb').read()
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)
sys.path.insert(0, 'tools')
import gvars_fix2 as G
pool = G.final_pool(); pat = b''.join(struct.pack('<H', v) for v in pool)
offs = []; i = 0
while True:
    i = d.find(pat, i)
    if i < 0: break
    offs.append(i); i += 1
check('9 copies of the final g_vars pool in the ROM', len(offs) == 9, len(offs))
owned = set(range(0x4090, 0x409D)) | set(range(0x40A2, 0x40A7)) | {0x40A0} | set(range(0x40AA, 0x40B6)) | set(range(0x40E0, 0x40EA)) | set(range(0x40EA, 0x4100))
check('64 distinct vars', len(set(pool)) == 64)
check('no pool var is owned by other code', not (set(pool) & owned), sorted(hex(v) for v in set(pool) & owned))
check('deal_info compares liberty signed (ldrsh, blt)', d[0xf22d12:0xf22d18] == bytes.fromhex('c05e0b283bdb'))
sys.exit(1 if bad else 0)
