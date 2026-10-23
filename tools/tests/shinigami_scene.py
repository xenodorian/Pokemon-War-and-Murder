"""Shinigami cell scene test (run from the repo root): python3 tools/tests/shinigami_scene.py [ROM.gba]
From saves/ported/new_game_empty_party.raw, a scratch ROM warps to (2,69) beside the open cell with the Captain flag 0x4C0 set and a level 60 SANDSHREW,
walks Up twice (the second Up is blocked: facing Shinigami), then presses A through the cell talk, the battle and the win lines.
Checks: SCROLL (item 90) in the key items pocket, F_FREED 0x4F7, HIDE_CELL 0x4F9, VAR_STORY 2. Contact sheet: /tmp/emu_out/sn_sheet.png."""
import os, subprocess, struct, sys, glob
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
from inc import Rom
from cry_open import SB, put_script
OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True)
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
HEV = 0x3b974c
r = Rom(ROM); tb = SB()
tb.raw(0x79, 27, 0, 60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
tb.setflag(0x4C0); tb.setflag(0x880); tb.clearflag(0x4F9); tb.clearflag(0x4F7)
tb.releaseall(); tb.raw(0x39, 2, 69, 0xff, 21, 0, 5, 0); tb.raw(0x27); tb.end()
scr = 0x08000000 + put_script(r, tb)
n = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
for i in range(n): r.w32(ca + 16 * i + 12, scr)
t = OUT + '/sn.gba'; r.save(t)
L = []
for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
L += ["700 80", "760 0", "1500 40", "1530 0", "1560 40", "1590 0"]
for f in range(1700, 11000, 30): L += ["%d 1" % f, "%d 0" % (f + 6)]
L += ['dump 11200', 'end 11220']
for s in range(5000, 11200, 300): L.append('shot %d' % s)
key = lambda l: int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1])
L.sort(key=key)
for f in glob.glob(OUT + '/sn_*'): os.remove(f)
open(OUT + '/sn.txt', 'w').write('\n'.join(L))
subprocess.run(['./tools/harness_new', t, OUT + '/sn.txt', OUT + '/sn'], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=1800)
d = open(OUT + '/sn_11200.sb1', 'rb').read()
fl = lambda f: (d[0xEE0 + (f >> 3)] >> (f & 7)) & 1
keyitems = [struct.unpack('<HH', d[0x3B8 + 4 * i:0x3B8 + 4 * i + 4]) for i in range(30)]
var = struct.unpack('<H', d[0x1000 + 2 * (0x40E6 - 0x4000):0x1000 + 2 * (0x40E6 - 0x4000) + 2])[0]
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)
check('SCROLL in key items', any(i == 90 for i, q in keyitems), keyitems[:6])
check('F_FREED and HIDE_CELL set', fl(0x4F7) == 1 and fl(0x4F9) == 1, (fl(0x4F7), fl(0x4F9)))
check('VAR_STORY is 2', var == 2, var)
sys.exit(1 if bad else 0)
