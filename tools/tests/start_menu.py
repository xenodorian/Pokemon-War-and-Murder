"""Start menu test (run from the repo root): python3 tools/tests/start_menu.py [ROM.gba]   (default: the one ROM)
Starts from saves/ported/new_game_empty_party.raw and checks, with the mGBA harness:
 1 menu    every row is reachable by scrolling (POKEMON .. EXIT, REPORT, REMAP), also with the POKEDEX row (12 rows)
 2 report  REPORT writes a PWAMRPT text into flash sector 31 of the save file and touches nothing else
 3 remap   REMAP stores the chosen keys in saved vars 0x40AE/0x40B5 and the game then sees those keys as A and B (read from gMain)
 4 hook    with no remap the key hook changes nothing: a browse of bag, quests and walking gives the same frames with the hook removed
Pictures go to /tmp/emu_out/startmenu_*.png (contact sheets). Exit code 1 if anything fails."""
import os, subprocess, struct, sys, glob, shutil
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R)
OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True)
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
STATE = os.path.join(R, 'saves/ported/new_game_empty_party.raw')
bad = []


def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)


def run(tag, keys, end, step, rom=ROM, sav=None, extra=(), rams=(), dumps=(), cold=False):
    L = []
    for k in keys.split(';'):
        if k.strip():
            t = k.split(); hold = int(t[2]) if len(t) > 2 else 6
            L += ['%s %s' % (t[0], t[1]), '%d 0' % (int(t[0]) + hold)]
    L += ['shot %d' % f for f in range(step, end, step)] + list(extra)
    L += ['ram %s' % r for r in rams] + ['dump %d' % d for d in dumps] + ['end %d' % end]
    key = lambda l: int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1])
    L.sort(key=key)
    for f in glob.glob('%s/%s_*' % (OUT, tag)): os.remove(f)
    open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
    env = dict(os.environ)
    if not cold: env['LOADSTATE'] = STATE
    r = subprocess.run(['./tools/harness_new', rom, '%s/%s.txt' % (OUT, tag), '%s/%s' % (OUT, tag)] + ([sav] if sav else []), env=env, capture_output=True, text=True, timeout=900)
    ram = {}
    for l in r.stderr.split('\n'):
        if l.startswith('RAM'):
            p = l.split(); ram[(int(p[1][1:]), int(p[2][:-1], 16))] = bytes(int(x, 16) for x in p[3:])
    return ram


def sheet(tag, cols=6):
    ims = [Image.open(f) for f in sorted(glob.glob('%s/%s_*.ppm' % (OUT, tag)))]
    w, h = ims[0].size; o = Image.new('RGB', (w * cols, h * ((len(ims) + cols - 1) // cols)))
    for i, m in enumerate(ims): o.paste(m, ((i % cols) * w, (i // cols) * h))
    o.save('%s/startmenu_%s.png' % (OUT, tag))


def downs(n, first=130, gap=25): return ';'.join('%d 80' % (first + i * gap) for i in range(n))
def var(sb1, v): return struct.unpack('<H', sb1[0x1000 + 2 * (v - 0x4000):0x1002 + 2 * (v - 0x4000)])[0]
def sav_text(path):
    d = open(path, 'rb').read(); i = d.find(b'PWAMRPT'); return d, (d[i:i + 900].split(b'\0')[0].decode() if i >= 0 else '')


# 1 menu: rows seen while scrolling, with and without the POKEDEX row (flag 0x829)
for tag, extra, rows, n in (('menu11', (), ['POKEMON', 'REPORT', 'REMAP'], 12), ('menu12', ('setbit 40 fe5 2',), ['POKEDEX', 'POKEMON', 'REPORT', 'REMAP'], 13)):
    ram = run(tag, '60 8;' + downs(n), 500, 25, extra=extra, rams=['470 20370f0 24'])
    sheet(tag)
    b = ram[(470, 0x20370f0)]; num = b[5]; acts = list(b[6:6 + num])
    check('%s: %d rows, last two actions 12 and 13' % (tag, num), num == (12 if 'setbit 40 fe5 2' in extra else 11) and acts[-2:] == [12, 13], acts)

# 2 report: sequential, A then B, flash sector 31 only
for f in glob.glob(OUT + '/sm.sav'): os.remove(f)
keys = '60 8;' + downs(9) + ';400 1;800 1 40;1100 2 30'
run('report', keys, 1700, 200, sav=OUT + '/sm.sav'); sheet('report')
d, txt = sav_text(OUT + '/sm.sav'); print(txt)
check('report: file is 128 KB flash (plus a 16 byte clock footer when mGBA adds one)', len(d) in (131072, 131088), len(d))
check('report: A line shows raw 0001*40', 'A press: first=0001(A)' in txt and '0001*40' in txt)
check('report: B line shows raw 0002*30', 'B press: first=0002(B)' in txt and '0002*30' in txt)
check('report: written in sector 31 only', d.find(b'PWAMRPT') >= 0x1F000 and set(d[:0x1F000]) == {0xFF})

# 3 remap: Left as A, Right as B, then game keys read from gMain while Left and Right are held
for f in glob.glob(OUT + '/sr*.sav'): os.remove(f)
keys = '60 8;' + downs(10) + ';420 1;700 20 20;900 10 20;1150 20 8;1400 20 30;1500 10 30'
ram = run('remap', keys, 1800, 100, sav=OUT + '/sr.sav', rams=['1410 3003118 4', '1510 3003118 4'], dumps=[1300]); sheet('remap', 6)
sb1 = open('%s/remap_01300.sb1' % OUT, 'rb').read()
check('remap: saved vars hold LEFT and RIGHT', (var(sb1, 0x40AE), var(sb1, 0x40B5)) == (0x20, 0x10), (hex(var(sb1, 0x40AE)), hex(var(sb1, 0x40B5))))
check('remap: Left is seen as A', struct.unpack('<H', ram[(1410, 0x3003118)][:2])[0] == 1)
check('remap: Right is seen as B', struct.unpack('<H', ram[(1510, 0x3003118)][:2])[0] == 2)

# 3b remap with no key pressed: nothing changes, the key mask flag is cleared, the game gets its keys back
ram = run('remapto', '60 8;' + downs(10) + ';420 1', 4300, 500, sav=OUT + '/sr2.sav', rams=['4200 20370ca 2'], dumps=[4200]); sheet('remapto', 6)
sb1 = open('%s/remapto_04200.sb1' % OUT, 'rb').read()
check('remap timeout: vars unchanged', (var(sb1, 0x40AE), var(sb1, 0x40B5)) == (0, 0))
check('remap timeout: key mask flag 0x8009 cleared', ram[(4200, 0x20370ca)] == b'\x00\x00', ram[(4200, 0x20370ca)])

# 4 hook: no remap, same frames with the hook stub restored (bytes of the key hook entry before start_menu_fix)
orig = bytes.fromhex('01b54b4009480068')
r2 = bytearray(open(ROM, 'rb').read()); r2[0x175228:0x175230] = orig; open(OUT + '/nohook.gba', 'wb').write(r2)
keys = '60 8;130 80 6;200 1;300 80;380 2;450 2;520 40 40;640 80 30;760 20 30;860 10 30;960 8;1030 80;1100 1;1200 2;1300 2'
run('hook1', keys, 1500, 100); run('hook2', keys, 1500, 100, rom=OUT + '/nohook.gba')
same = all(Image.open(a).tobytes() == Image.open(b).tobytes() for a, b in zip(sorted(glob.glob(OUT + '/hook1_*.ppm')), sorted(glob.glob(OUT + '/hook2_*.ppm'))))
check('hook: frames identical with and without the hook when nothing is remapped', same)
sys.exit(1 if bad else 0)
