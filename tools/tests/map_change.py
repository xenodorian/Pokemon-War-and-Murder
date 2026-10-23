"""Map change test (run from the repo root): python3 tools/tests/map_change.py [ROM.gba]
Every map load runs hooks (the Bless Tag key-item hook among them). A hook that returns wrongly crashes EVERY map change (fade out, white flash, soft reset
to the copyright screen); that is what bless_key.py did until bless_key_fix.py. This test starts from saves/ported/new_game_empty_party.raw, warps to
Pallet Town (3,0) and to Viridian City (3,1) through the test door script and checks that the game is still running there: the location in the save block
is the target map and the position is the target tile.."""
import os, subprocess, struct, sys, glob
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True)
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)
def warp(tag, target):
    t = '%s/%s.gba' % (OUT, tag)
    subprocess.run(['sh', 'tools/mk_test_rom.sh', t], check=True, capture_output=True, env=dict(os.environ, TEST_WARP=target, TEST_GIVE='27,12', TEST_SRC_ROM=ROM))
    L = []
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0"]
    L += ['dump 1500', 'end 1520']
    key = lambda l: int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1])
    L.sort(key=key)
    for f in glob.glob('%s/%s_*' % (OUT, tag)): os.remove(f)
    open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new', t, '%s/%s.txt' % (OUT, tag), '%s/%s' % (OUT, tag)], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=900)
    return open('%s/%s_01500.sb1' % (OUT, tag), 'rb').read()
for name, target in (('Pallet Town', '3,0,8,8'), ('Viridian City', '3,1,44,22'), ('Viridian base', '2,71,14,18')):
    d = warp('mc_' + name.split()[0].lower(), target)
    loc = struct.unpack('<bb', d[4:6]); pos = struct.unpack('<hh', d[0:4])
    g, n, x, y = [int(v) for v in target.split(',')]
    check('warp to %s completes (game still running there)' % name, loc == (g, n) and pos == (x, y), (loc, pos))
sys.exit(1 if bad else 0)
