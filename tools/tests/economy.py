"""Money and reputation test (run from the repo root, LD_LIBRARY_PATH to libmgba): python3 tools/tests/economy.py [ROM.gba]
Runs the bystander natives directly (callnative by_note, then by_threat or by_bless) from the empty-party state and reads SaveBlock1 and the money key from the emulator.
THREATEN: money must rise by 50..200 (the game's AddMoney, money is XOR the encryption key), VAR_REPADJ drops by 1, VAR_REP becomes 99.
BLESS: the bless count 0x40F4 rises by 1 and VAR_REP becomes 101.
Before tools/money_fix.py the THREATEN reward was added to the encrypted word and money became about 3.9 billion."""
import os, subprocess, sys, glob, re, struct
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
from inc import Rom
from cry_open import SB, put_script
OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True); HEV = 0x3b974c
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
d0 = open(ROM, 'rb').read()
def native(label_after):                       # address of the 3 natives, read from the live bystander menu script (0xff0138)
    return None
def run(tag, which):
    r = Rom(ROM); tb = SB()
    tb.raw(0x79, 27, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    tb.raw(0x90, 0xE8, 0x03, 0, 0, 0)                          # addmoney 1000
    tb.raw(0x16, 0, 0x80, 3, 0); tb.raw(0x16, 1, 0x80, 1, 3)    # the person: object 3 of map (3,1), as the wrapper sets it
    tb.raw(0x23); tb.ptr(0x08fefadd)                           # by_note
    tb.raw(0x23); tb.ptr(which)                                # by_threat 0x08fefc61 or by_bless
    tb.releaseall(); tb.end()
    scr = 0x08000000 + put_script(r, tb); n = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
    for i in range(n): r.w32(ca + 16 * i + 12, scr)
    t = '%s/%s.gba' % (OUT, tag); r.save(t)
    def go(extra):
        L = []
        for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
        L += ["700 80", "760 0", 'dump 1500', 'end 1520'] + extra
        L.sort(key=lambda l: int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1]))
        for g in glob.glob('%s/%s_*' % (OUT, tag)): os.remove(g)
        open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
        return subprocess.run(['./tools/harness_new', t, '%s/%s.txt' % (OUT, tag), '%s/%s' % (OUT, tag)], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=900).stderr
    err = go(['ram 1500 300500c 4'])
    sb2 = int(''.join(re.search(r'RAM f1500 0300500c: (\w\w) (\w\w) (\w\w) (\w\w)', err).groups()[::-1]), 16)
    err = go(['ram 1500 %x 4' % (sb2 + 0xF20)])
    key = int(''.join(re.search(r'RAM f1500 %08x: (\w\w) (\w\w) (\w\w) (\w\w)' % (sb2 + 0xF20), err).groups()[::-1]), 16)
    d = open('%s/%s_01500.sb1' % (OUT, tag), 'rb').read()
    var = lambda v: struct.unpack('<H', d[0x1000 + 2 * (v - 0x4000):0x1000 + 2 * (v - 0x4000) + 2])[0]
    return struct.unpack('<I', d[0x290:0x294])[0] ^ key, var
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)
money, var = run('eco_t', 0x08fefc61)
check('THREATEN pays 50..200 through AddMoney', 1050 <= money <= 1200, money)
check('THREATEN lowers VAR_REPADJ by one and sets VAR_REP 99', var(0x40E9) == 999 and var(0x40E7) == 99, (var(0x40E9), var(0x40E7)))
money, var = run('eco_b', 0x08fefbfd)
check('BLESS raises the bless count and VAR_REP to 101, money untouched', var(0x40F4) == 1 and var(0x40E7) == 101 and money == 1000, (var(0x40F4), var(0x40E7), money))
sys.exit(1 if bad else 0)
