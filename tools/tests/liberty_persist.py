"""Liberty persistence test (run from the repo root): python3 tools/tests/liberty_persist.py [ROM.gba]
The vanilla quest-log routines used to write vars 0x40AA..0x40AE on every map load, which zeroed LIBERTY (0x40AC), the police deal state (0x40AB),
Hall of Justice species slot 0 (0x40AD) and the REMAP mask (0x40AE). This test sets those vars, warps to Pallet Town and Viridian City and checks they survive.
Needs a harness built from tools/harness.c (the 'wr' command): HARNESS=/path/to/harness (default tools/harness_new)."""
import os, subprocess, struct, sys, glob
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True)
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
H = os.environ.get('HARNESS', './tools/harness_new')
SB1 = 0x02025530
VARS = {0x40AB: 7, 0x40AC: 55, 0x40AD: 25, 0x40AE: 0x20}
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)
def run(tag, target):
    t = '%s/%s.gba' % (OUT, tag)
    subprocess.run(['sh', 'tools/mk_test_rom.sh', t], check=True, capture_output=True, env=dict(os.environ, TEST_WARP=target, TEST_GIVE='27,12', TEST_SRC_ROM=ROM))
    L = ["650 wr"] if False else []
    L += ['wr 650 %x %x 2' % (SB1 + 0x1000 + 2 * (v - 0x4000), val) for v, val in VARS.items()]
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0", 'dump 1500', 'end 1520']
    key = lambda l: int(l.split()[1]) if l.startswith('wr') else (int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1]))
    L.sort(key=key)
    for f in glob.glob('%s/%s_*' % (OUT, tag)): os.remove(f)
    open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
    subprocess.run([H, t, '%s/%s.txt' % (OUT, tag), '%s/%s' % (OUT, tag)], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=900)
    return open('%s/%s_01500.sb1' % (OUT, tag), 'rb').read()
for name, target in (('Pallet Town', '3,0,8,8'), ('Viridian City', '3,1,44,22')):
    d = run('lp_' + name.split()[0].lower(), target)
    loc = struct.unpack('<bb', d[4:6])
    check('warp to %s completed' % name, loc == tuple(int(v) for v in target.split(',')[:2]), loc)
    for v, val in VARS.items():
        got = struct.unpack('<H', d[0x1000 + 2 * (v - 0x4000):][:2])[0]
        check('var 0x%X survives the map load in %s' % (v, name), got == val, hex(got))
sys.exit(1 if bad else 0)
