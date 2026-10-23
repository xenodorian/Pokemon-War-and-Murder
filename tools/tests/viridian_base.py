"""Viridian base test (run from the repo root): python3 tools/tests/viridian_base.py [ROM.gba]
From saves/ported/new_game_empty_party.raw, a scratch ROM whose bedroom door script sets or clears the Viridian cleared flag 0x4C2 and warps into the base
(map 2,71). Checks: flag set and no Purple Heart (item 59) -> the flag stays set and the Purple Heart is added; flag clear (captain alive) -> no medal;
flag set and the medal already in the bag -> one medal only."""
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
def run(tag, flag, give_medal):
    r = Rom(ROM); tb = SB()
    tb.raw(0x79, 27, 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)                       # a party, as in a real run
    (tb.setflag if flag else tb.clearflag)(0x4C2)
    if give_medal: tb.raw(0x44, 59, 0, 1, 0)
    tb.releaseall(); tb.raw(0x39, 2, 71, 0xff, 14, 0, 18, 0); tb.raw(0x27); tb.end()
    scr = 0x08000000 + put_script(r, tb)
    n = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
    for i in range(n): r.w32(ca + 16 * i + 12, scr)
    t = '%s/%s.gba' % (OUT, tag); r.save(t)
    L = []
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0", 'dump 1700', 'end 1720']
    key = lambda l: int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1])
    L.sort(key=key)
    for f in glob.glob('%s/%s_*' % (OUT, tag)): os.remove(f)
    open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new', t, '%s/%s.txt' % (OUT, tag), '%s/%s' % (OUT, tag)], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=900)
    d = open('%s/%s_01700.sb1' % (OUT, tag), 'rb').read()
    pocket = lambda off, n: [struct.unpack('<HH', d[off + 4 * i:off + 4 * i + 4]) for i in range(n)]
    meds = [i for i, q in pocket(0x310, 42) + pocket(0x3B8, 30) if i == 59]
    return struct.unpack('<bb', d[4:6]), (d[0xEE0 + (0x4C2 >> 3)] >> (0x4C2 & 7)) & 1, len(meds)
loc, fl, m = run('vb_a', True, False)
check('captain defeated, no medal: in the base, flag kept, Purple Heart added', loc == (2, 71) and fl == 1 and m == 1, (loc, fl, m))
loc, fl, m = run('vb_b', False, False)
check('captain alive: no Purple Heart', loc == (2, 71) and fl == 0 and m == 0, (loc, fl, m))
loc, fl, m = run('vb_c', True, True)
check('captain defeated, medal already there: still one', loc == (2, 71) and fl == 1 and m == 1, (loc, fl, m))
sys.exit(1 if bad else 0)
