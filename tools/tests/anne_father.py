"""Anne scene and father choice test (run from the repo root): python3 tools/tests/anne_father.py [ROM.gba]
From saves/ported/new_game_empty_party.raw, a scratch ROM sets VAR_STORY 2, hides Anne (as at new game), gives a SANDSHREW and the SCROLL (item 90) and warps to Pewter (3,2).
The frame script runs Anne's news, warps the player to Father's bedside in the house (4,0), asks the choice; A answers YES (wake Father).
Checks: player is in the house (4,0) at (3,4), VAR_STORY 3, VAR_CHOICE 1, F_FATHER_ALIVE set, SCROLL gone from the key items, and PC box 14 holds six POKeMON named FATHER."""
import os, subprocess, struct, sys, glob, re
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
from inc import Rom
from cry_open import SB, put_script
OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True)
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
HEV = 0x3b974c
r = Rom(ROM); tb = SB()
tb.raw(0x79, 27, 0, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
tb.raw(0x44, 90, 0, 1, 0); tb.setflag(0x4FA); tb.setflag(0x4FB); tb.raw(0x16, 0xE6, 0x40, 2, 0)
tb.releaseall(); tb.raw(0x39, 3, 2, 0xff, 24, 0, 36, 0); tb.raw(0x27); tb.end()
scr = 0x08000000 + put_script(r, tb)
n = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
for i in range(n): r.w32(ca + 16 * i + 12, scr)
t = OUT + '/af.gba'; r.save(t)
def run(extra, sheet=False):
    L = []
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0"]
    for f in range(1500, 4500, 40): L += ["%d 1" % f, "%d 0" % (f + 6)]
    L += ['dump 4600', 'end 4620'] + extra
    if sheet: L += ['shot %d' % s for s in range(1500, 4500, 150)]
    key = lambda l: int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1])
    L.sort(key=key)
    for f in glob.glob(OUT + '/af_*'): os.remove(f)
    open(OUT + '/af.txt', 'w').write('\n'.join(L))
    p = subprocess.run(['./tools/harness_new', t, OUT + '/af.txt', OUT + '/af'], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=1800)
    return p.stderr
err = run(['ram 4500 3005010 4'], True)
ptr = int(re.search(r'RAM f4500 03005010: (\w\w) (\w\w) (\w\w) (\w\w)', err).group(0).split(':')[1].split()[::-1].__str__().replace("'", '').replace(', ', '').strip('[]'), 16)
BOX14 = 4 + 13 * 30 * 80
err = run(['ram 4500 %x 480' % (ptr + BOX14), 'ram 4500 %x 9' % (ptr + 0x8344 + 13 * 9)], True)
d = open(OUT + '/af_04600.sb1', 'rb').read()
fl = lambda f: (d[0xEE0 + (f >> 3)] >> (f & 7)) & 1
var = lambda v: struct.unpack('<H', d[0x1000 + 2 * (v - 0x4000):0x1000 + 2 * (v - 0x4000) + 2])[0]
keyitems = [struct.unpack('<HH', d[0x3B8 + 4 * i:0x3B8 + 4 * i + 4]) for i in range(30)]
box = [bytes.fromhex(''.join(re.findall(r'RAM f4500 %08x:((?: \w\w)+)' % (ptr + BOX14), err)[0].split()))] if re.findall(r'RAM f4500 %08x:' % (ptr + BOX14), err) else [b'']
box = box[0]
mons = [box[80 * i:80 * i + 80] for i in range(6)]
nm = re.findall(r'RAM f4500 %08x:((?: \w\w)+)' % (ptr + 0x8344 + 13 * 9), err)
name = bytes.fromhex(''.join(nm[0].split())) if nm else b''
bad = []
def check(name_, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name_ + (' ' + str(info) if info else ''))
    if not ok: bad.append(name_)
check('in the house at the bedside', struct.unpack('<bb', d[4:6]) == (4, 0) and struct.unpack('<hh', d[0:4]) == (3, 4), (struct.unpack('<bb', d[4:6]), struct.unpack('<hh', d[0:4])))
check('VAR_STORY 3, VAR_CHOICE 1, F_FATHER_ALIVE', var(0x40E6) == 3 and var(0x40F0) == 1 and fl(0x4FC) == 1, (var(0x40E6), var(0x40F0), fl(0x4FC)))
check('SCROLL removed', not any(i == 90 for i, q in keyitems), keyitems[:4])
check('box 14 has six POKeMON', all(any(m[0:4]) for m in mons) and len(box) == 480, [m[:4].hex() for m in mons])
from g3 import ENC
check('box 14 is named FATHER', name[:6] == bytes(ENC[c] for c in 'FATHER'), name.hex())
sys.exit(1 if bad else 0)
