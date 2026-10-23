"""Shinigami cage test (run from the repo root): python3 tools/tests/shinigami_cage.py [ROM.gba]
From saves/ported/new_game_empty_party.raw, a scratch ROM whose bedroom door script sets or clears the Pewter base cleared flag 0x4C0 and warps to (2,69) at (21,5).
Then the player walks Up into the gate, presses A through the text, and walks Up again.
Captain alive: the gate stays shut (player y stays 5, HIDE_GATE 0x880 clear). Captain beaten: the gate opens (flag 0x880 set) and the player can step to y 4."""
import os, subprocess, struct, sys, glob
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
from inc import Rom
from cry_open import SB, put_script
OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True)
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
HEV = 0x3b974c
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)
def run(tag, captain_down, shots=False):
    r = Rom(ROM); tb = SB()
    tb.raw(0x79, 27, 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    (tb.setflag if captain_down else tb.clearflag)(0x4C0)
    tb.clearflag(0x880); tb.clearflag(0x4F9)
    tb.releaseall(); tb.raw(0x39, 2, 69, 0xff, 21, 0, 5, 0); tb.raw(0x27); tb.end()
    scr = 0x08000000 + put_script(r, tb)
    n = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
    for i in range(n): r.w32(ca + 16 * i + 12, scr)
    t = '%s/%s.gba' % (OUT, tag); r.save(t)
    L = []
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0"]
    L += ["1500 40", "1530 0"]                       # Up into the gate (blocked, now facing it)
    for f in range(1560, 2100, 40): L += ["%d 1" % f, "%d 0" % (f + 6)]   # A, text, A ...
    L += ["2200 40", "2240 0", 'dump 2400', 'end 2420']
    if shots: L += ['shot 1700', 'shot 1900', 'shot 2300']
    key = lambda l: int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1])
    L.sort(key=key)
    for f in glob.glob('%s/%s_*' % (OUT, tag)): os.remove(f)
    open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new', t, '%s/%s.txt' % (OUT, tag), '%s/%s' % (OUT, tag)], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=900)
    d = open('%s/%s_02400.sb1' % (OUT, tag), 'rb').read()
    pos = struct.unpack('<hh', d[0:4]); loc = struct.unpack('<bb', d[4:6])
    return loc, pos, (d[0xEE0 + (0x880 >> 3)] >> (0x880 & 7)) & 1
loc, pos, gate = run('sc_a', False, True)
check('captain alive: gate shut', loc == (2, 69) and gate == 0 and pos[1] >= 5, (loc, pos, gate))
loc, pos, gate = run('sc_b', True, True)
check('captain beaten: gate opens and the player steps in', loc == (2, 69) and gate == 1 and pos[1] <= 4, (loc, pos, gate))
sys.exit(1 if bad else 0)
