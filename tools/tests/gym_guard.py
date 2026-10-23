"""Gym leader guard test (run from the repo root, LD_LIBRARY_PATH to libmgba): python3 tools/tests/gym_guard.py [ROM.gba]
Static: each of the 8 leader scripts starts its battle through a guard (goto, checkflag badge, clearflag trainer flag, copied trainerbattle, goto old next opcode).
Dynamic: from saves/ported/new_game_empty_party.raw, the door script sets Brock's trainer flag 0x69E (a stray write) and warps into the Pewter gym; the player walks up and talks
to Brock. Unguarded, the stray flag skips the fight and he hands out the TM (reward path). Guarded, the flag is cleared and no badge or TM is given before the battle."""
import os, subprocess, struct, sys, glob
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
from inc import Rom
from cry_open import SB, put_script
d = open(ROM, 'rb').read(); OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True); HEV = 0x3b974c
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)
for a, tid, badge, nm in ((0x16a5a0, 414, 0x820, 'Brock'), (0x16aaae, 415, 0x821, 'Misty'), (0x16b957, 416, 0x822, 'Surge'), (0x16d06e, 417, 0x823, 'Erika'),
                          (0x16d55b, 418, 0x824, 'Koga'), (0x16ede5, 420, 0x825, 'Sabrina'), (0x16d9e1, 419, 0x826, 'Blaine'), (0x169ed7, 350, 0x827, 'May')):
    ok = d[a] == 0x05
    if ok:
        g = struct.unpack('<I', d[a + 1:a + 5])[0] - 0x08000000
        ok = d[g] == 0x2b and struct.unpack('<H', d[g + 1:g + 3])[0] == badge and d[g + 3:g + 5] == bytes([0x06, 1]) and d[g + 9] == 0x2a and struct.unpack('<H', d[g + 10:g + 12])[0] == 0x500 + tid
        ok = ok and d[g + 12] == 0x5c and struct.unpack('<H', d[g + 14:g + 16])[0] == tid
    check('%s is guarded (clears a stray trainer flag when the badge is not owned)' % nm, ok)
def run(setf):
    r = Rom(ROM); tb = SB(); tb.raw(0x79, 27, 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    tb.setflag(setf); tb.releaseall(); tb.raw(0x39, 6, 2, 0xff, 6, 0, 9, 0); tb.raw(0x27); tb.end()
    scr = 0x08000000 + put_script(r, tb); n = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
    for i in range(n): r.w32(ca + 16 * i + 12, scr)
    t = OUT + '/gg.gba'; r.save(t)
    L = []
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0"]; f = 1500
    for k in "40 40 40 40 1 1 1 1".split(): L += ["%d %s" % (f, k), "%d 0" % (f + 8)]; f += 60
    L += ["dump %d" % (f + 60), "end %d" % (f + 80)]
    for x in glob.glob(OUT + '/gg_*'): os.remove(x)
    open(OUT + '/gg.txt', 'w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new', t, OUT + '/gg.txt', OUT + '/gg'], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, timeout=600)
    s = open(glob.glob(OUT + '/gg_*.sb1')[0], 'rb').read()
    return lambda n: (s[0xEE0 + (n >> 3)] >> (n & 7)) & 1
fl = run(0x500 + 414)
check('stray Brock trainer flag is cleared when he is talked to without the badge', fl(0x500 + 414) == 0)
check('no badge or DEFEATED flag appears from the stray flag', not fl(0x820) and not fl(0x4B0))
sys.exit(1 if bad else 0)
