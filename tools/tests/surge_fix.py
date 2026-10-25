"""Gym leader talk test (run from the repo root): python3 tools/tests/surge_fix.py [ROM.gba]
Lt. Surge's script lost its `release; end` after the post-battle msgbox, so talking to him after he gave TM34 (FLAG_GOT_TM34_FROM_SURGE 0x231 set, so every talk after the fight) ran into `call 0x800416a0` and crashed (pc 0x00000008). tools/surge_fix.py writes 6c 02 at 0x16B97A.
For each of the 8 gym leaders: (win) fresh fight with a single Lv100 Mewtwo (a party of 3 starts double battles): the trainer flag 0x500+id and the badge flag must be set;
(again) trainer, badge and defeated flags set (and 0x231 for Surge), with and without the bless/gun/shackle items, talk many times.
Crash detection: the pc sampled every 5 frames must never be 0x00000008 or outside ROM/RAM/BIOS (>= 0x0e000000), and the game must still be on the gym map."""
import os, subprocess, sys, glob
from concurrent.futures import ThreadPoolExecutor
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
from inc import Rom
from cry_open import SB, put_script
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
OUT = '/tmp/emu_out/surge_%d' % os.getpid(); os.makedirs(OUT, exist_ok=True); HEV = 0x3b974c
# name, map group, num, stand tile (in front of the leader), trainer id, badge flag, defeated flag (0x4B0 + n)
LEADERS = [('Brock', 6, 2, 6, 6, 414, 0x820, 0x4B0), ('Misty', 7, 5, 8, 7, 415, 0x821, 0x4B1), ('Surge', 9, 6, 5, 3, 416, 0x822, 0x4B2),
           ('Erika', 10, 16, 6, 5, 417, 0x823, 0x4B3), ('Koga', 11, 3, 7, 14, 418, 0x824, 0x4B4), ('Blaine', 12, 0, 5, 5, 419, 0x826, 0x4B6),
           ('Sabrina', 14, 3, 14, 12, 420, 0x825, 0x4B5), ('Giovanni', 5, 1, 2, 3, 350, 0x827, 0x4B7)]
def run(tag, g, n, x, y, flags, items, nA, give=True):
    r = Rom(ROM); tb = SB()
    if give:
        tb.raw(0x79, 150, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    for f in flags: tb.setflag(f)
    for it in items: tb.raw(0x44, it, 0, 1, 0)
    tb.releaseall(); tb.raw(0x39, g, n, 0xff, x, 0, y, 0); tb.raw(0x27); tb.end()
    scr = 0x08000000 + put_script(r, tb); k = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
    for i in range(k): r.w32(ca + 16 * i + 12, scr)
    t = '%s/%s.gba' % (OUT, tag); r.save(t)
    L = []
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0"]; f = 1500
    L += ["%d 40" % f, "%d 0" % (f + 6)]; f += 60
    for _ in range(nA): L += ["%d 1" % f, "%d 0" % (f + 6)]; f += 60
    L += ["dump %d" % f, "end %d" % (f + 10)]
    open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
    for fl in glob.glob('%s/%s_*' % (OUT, tag)): os.remove(fl)
    env = dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw', PCS='1500', PCE='5', LD_LIBRARY_PATH=os.environ.get('LD_LIBRARY_PATH', '/home/user/build_mgba/b'))
    p = subprocess.run(['./tools/harness_new', t, '%s/%s.txt' % (OUT, tag), '%s/%s' % (OUT, tag)], env=env, capture_output=True, text=True, timeout=1500)
    pcs = [int(l.split('pc=')[1][:8], 16) for l in p.stderr.split('\n') if ' pc=' in l]
    crashed = [hex(v) for v in pcs if v == 8 or v >= 0x0e000000]
    d = open(glob.glob('%s/%s_*.sb1' % (OUT, tag))[0], 'rb').read()
    fl = lambda q: (d[0xEE0 + (q >> 3)] >> (q & 7)) & 1
    return crashed, fl, (d[4], d[5])
def job(L):
    name, g, n, x, y, tid, badge, dfl = L; res = []
    c, fl, loc = run(name + '_win', g, n, x, y, [], [], 230)
    res.append((name + ' win: no crash, still in gym', not c and loc == (g, n), c[:2] or loc))
    res.append((name + ' win: trainer flag and badge set', fl(0x500 + tid) == 1 and fl(badge) == 1, (fl(0x500 + tid), fl(badge))))
    for items, tag in (([], 'bare'), ([89, 52, 53, 56], 'items')):
        c, fl, loc = run('%s_again_%s' % (name, tag), g, n, x, y, [0x500 + tid, badge, dfl] + ([0x231] if tid == 416 else []), items, 30)
        res.append((name + ' again (' + tag + '): no crash', not c and loc == (g, n), c[:2] or loc))
    return res
bad = []
with ThreadPoolExecutor(4) as ex:
    for res in ex.map(job, LEADERS):
        for name, ok, info in res:
            print(('PASS ' if ok else 'FAIL ') + name, info)
            if not ok: bad.append(name)
sys.exit(1 if bad else 0)
