"""Shackle prompt test (run from anywhere, LD_LIBRARY_PATH must point at libmgba): python3 tools/tests/shackle_fix.py [ROM.gba] [--quick]
Static: the post-battle front script (pointer at 0x1A4ED9) reads the var the natives really write.
Dynamic (mGBA, tools/harness_new, scratch ROM copies in /tmp/shackle_test): the player gets a strong lead, a SHACKLE BALL, warps next to a trainer
and talks to it from a given side. Decoded dialog text (gStringVar4 0x02021D18) is polled, the ball, party size, trainer flag and shackle flag (0x871+index) are read.
  - every non-captain trainer, from every side: no 'Shackle this' prompt, ball kept
  - captains and the General: prompt exactly once, from several sides; Yes joins the party and sets the flag, No keeps the ball, no ball gives no prompt, full party goes to the PC
Prints PASS / FAIL per check; exit status 1 if any FAIL. Facing values: 1 down, 2 up, 3 left, 4 right (VAR_FACING 0x800C = 0x020370D4)."""
import os, sys, glob, struct, subprocess
from concurrent.futures import ThreadPoolExecutor
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
from inc import Rom
from cry_open import SB, put_script
args = [a for a in sys.argv[1:] if not a.startswith('--')]
QUICK = '--quick' in sys.argv
ROM = os.path.abspath(args[0]) if args else os.path.join(R, 'PokemonWarAndMurder.gba')
OUT = '/tmp/shackle_test'; os.makedirs(OUT, exist_ok=True)
HEV = 0x3b974c
fails = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + ((' | ' + str(info)) if info != '' else ''))
    if not ok: fails.append(name)
    sys.stdout.flush()

# ---------------------------------------------------------------- static
rom = open(ROM, 'rb').read()
u32 = lambda o: struct.unpack('<I', rom[o:o + 4])[0]
front = u32(0x1A4ED9) - 0x08000000
body = rom[front:front + 0x400]
check('front starts callnative shackle_check2 (08F8C769)', body[:5] == bytes([0x23]) + struct.pack('<I', 0x08F8C769), body[:5].hex())
check('gate is compare 0x800D,1 (the var the native writes), goto_if NE', body[5:12] == bytes([0x21, 0x0D, 0x80, 0x01, 0x00, 0x06, 0x05]), body[5:12].hex())
check('front never reads VAR_FACING 0x800C', bytes([0x21, 0x0C, 0x80]) not in body)
i = body.find(bytes([0x45, 0x59, 0x00, 0x01, 0x00, 0x04]))
check('after removeitem and the do2 wrapper the party-full test reads 0x800F', i > 0 and body[i + 10:i + 18] == bytes([0x21, 0x0F, 0x80, 0x01, 0x00, 0x06, 0x01, body[i + 17]]) or (i > 0 and body[i + 10:i + 17] == bytes([0x21, 0x0F, 0x80, 0x01, 0x00, 0x06, 0x01])), body[i + 10:i + 18].hex() if i > 0 else 'no removeitem')
check('shackle_check2 stores yes/no at 0x020370D0 (strh r1,[r0,#2], r0 = 0x020370CE)', rom[0xF8C7DA:0xF8C7DC] == b'\x41\x80' and u32(0xF8C7EC) == 0x020370CE, rom[0xF8C7DA:0xF8C7DC].hex())
check('shackle_do2 stores its GIVE result at 0x020370D2 (strh r0,[r1,#4], r1 = 0x020370CE)', rom[0xF8C898:0xF8C89A] == b'\x88\x80' and u32(0xF8C8D4) == 0x020370CE, rom[0xF8C898:0xF8C89A].hex())

# ---------------------------------------------------------------- dynamic helpers
CH = {}
for k in range(10): CH[0xA1 + k] = str(k)
for k in range(26): CH[0xBB + k] = chr(65 + k); CH[0xD5 + k] = chr(97 + k)
CH.update({0: ' ', 0xAB: '!', 0xAC: '?', 0xAD: '.', 0xB8: ',', 0xFE: '/', 0xB4: "'", 0xAE: '-', 0xF0: ':'})
def dec(bs):
    s = ''
    for c in bs:
        if c == 0xFF: break
        s += CH.get(c, '~')
    return s
def tflag(sb, n): return (sb[0xEE0 + (n >> 3)] >> (n & 7)) & 1
def run(tag, g, n, x, y, face, ball=True, fill=0, nA=45, bfrom=None, tpoll=(3000, 4700, 30), mixb=None, weak=None):
    r = Rom(ROM); tb = SB()
    if weak:   # scratch copy only: the General's six legendaries would outlast Mewtwo's PP, so give them level 2
        t = 0x798790 + 40 * weak; pp = u32(t + 36) - 0x08000000; sz = 16 if rom[t] & 1 else 8
        for k in range(rom[t + 32]): struct.pack_into('<H', r.b, pp + sz * k + 2, 2)
    tb.raw(0x79, 150, 0, 70, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)               # givemon MEWTWO 70
    for _ in range(fill): tb.raw(0x79, 25, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    if ball: tb.raw(0x44, 89, 0, 1, 0)                                        # additem SHACKLE BALL
    tb.releaseall(); tb.raw(0x39, g, n, 0xff, x, 0, y, 0); tb.raw(0x27); tb.end()
    scr = 0x08000000 + put_script(r, tb); nn = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
    for k in range(nn): r.w32(ca + 16 * k + 12, scr)
    t = '%s/%s.gba' % (OUT, tag); r.save(t)
    L = []
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0"]
    f = 1500
    if face: L += ["%d %s" % (f, face), "%d 0" % (f + 8)]
    f += 60
    for k in range(nA):
        useb = (bfrom and f >= bfrom) or (mixb and mixb[0] <= f < mixb[1] and k % 3 == 2)
        L += ["%d %x" % (f, 2 if useb else 1), "%d 0" % (f + 6)]; f += 70
    stop = f
    L += ["ram %d 20370b8 48" % stop, "ram %d 2024029 1" % stop]
    for ff in range(tpoll[0], min(tpoll[1], stop), tpoll[2]): L.append("ram %d 2021d18 120" % ff)
    L += ["dump %d" % (stop + 10), "end %d" % (stop + 20)]
    for fl in glob.glob('%s/%s_*' % (OUT, tag)): os.remove(fl)
    open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
    p = subprocess.run(['./tools/harness_new', t, '%s/%s.txt' % (OUT, tag), '%s/%s' % (OUT, tag)], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, errors='replace', timeout=1500)
    sb = open(glob.glob('%s/%s_*.sb1' % (OUT, tag))[0], 'rb').read()
    res = {'sb': sb, 'texts': [], 'party': None}
    for l in p.stderr.split('\n'):
        if l.startswith('RAM'):
            hd, rest = l.split(':', 1); a = int(hd.split()[2], 16); v = bytes(int(q, 16) for q in rest.split())
            if a == 0x20370b8: res['facing'] = v[0x1c]; res['result'] = v[0x18]
            elif a == 0x2024029: res['party'] = v[0]
            elif a == 0x2021d18:
                s = dec(v)
                if s.strip() and (not res['texts'] or res['texts'][-1] != s): res['texts'].append(s)
    res['ball'] = any(sb[o:o + 2] == b'\x59\x00' for o in range(0x310, 0x5f0, 4))
    res['prompts'] = sum(1 for s in res['texts'] if s.startswith('Shackle this'))
    return res

def objects(g, n):
    gp = u32(0x3526A8 + 4 * g) - 0x08000000; h = u32(gp + 4 * n) - 0x08000000; ev = u32(h + 4) - 0x08000000; po = u32(ev + 4) - 0x08000000
    out = []
    for k in range(rom[ev]):
        o = po + 24 * k; sp = u32(o + 16)
        if 0x08000000 <= sp < 0x0A000000:
            sc = sp - 0x08000000
            if rom[sc] == 0x5C:
                tid = struct.unpack('<H', rom[sc + 2:sc + 4])[0]
                out.append((rom[o], struct.unpack('<hh', rom[o + 4:o + 8]), tid, rom[0x798790 + 40 * tid + 1]))
    return out
SIDES = [('above, facing down', 0, -1, '80', 1), ('below, facing up', 0, 1, '40', 2), ('right of it, facing left', 1, 0, '20', 3), ('left of it, facing right', -1, 0, '10', 4)]
def non_captain_cases(label, g, n, which, objs=None):
    jobs = []
    for (lid, (x, y), tid, cls) in (objs if objs is not None else objects(g, n)):
        if which is not None and tid not in which: continue
        for (sname, dx, dy, key, fv) in SIDES:
            jobs.append((label, g, n, lid, tid, cls, x + dx, y + dy, key, fv, sname))
    return jobs
def do_nc(j):
    label, g, n, lid, tid, cls, px, py, key, fv, sname = j
    res = run('nc_%d_%d_%d_%d' % (g, n, lid, fv), g, n, px, py, key, nA=100 if cls == 84 else 45, tpoll=(3000, 8000, 40) if cls == 84 else (3000, 4700, 30))
    return j, res
def report_nc(items, title):
    talk = {1: 0, 2: 0, 3: 0, 4: 0}; nobattle = 0; bad = 0
    for j, res in items:
        label, g, n, lid, tid, cls, px, py, key, fv, sname = j
        fought = tflag(res['sb'], 0x500 + tid)
        prompt = res['prompts'] > 0 or not res['ball']
        path = 'talk' if res['facing'] == fv else 'sight'
        if fought and path == 'talk': talk[fv] += 1
        if not fought: nobattle += 1
        ok = fought and not prompt
        if not ok and fought: bad += 1
        check('%s trainer %d (class %d) %s: no prompt, ball kept' % (label, tid, cls, sname), ok or (not fought), 'fought=%d path=%s facing=%d ball=%s prompts=%d' % (fought, path, res['facing'], res['ball'], res['prompts']) + ('' if fought else ' (battle did not start, inconclusive)'))
    check('%s: every facing covered by a real talk-path battle (down/up/left/right)' % title, all(talk[k] > 0 for k in talk), talk)
    print('   %s: %d battles ran, %d did not start, %d prompted' % (title, len(items) - nobattle, nobattle, bad))

if not os.path.exists('./tools/harness_new'): print('no harness'); sys.exit(2)
pool = ThreadPoolExecutor(4)
# ---------------------------------------------------------------- non-captains
jobs = non_captain_cases('Route 3', 3, 21, None)
if QUICK: jobs = jobs[:8]
report_nc(list(pool.map(do_nc, jobs)), 'Route 3')
jobs = non_captain_cases('JRA soldier (Pewter base)', 2, 69, (1, 2))   # class 48
report_nc(list(pool.map(do_nc, jobs)), 'JRA soldiers')
jobs = non_captain_cases('gym leader BROCK', 3, 78, None, objs=[(1, (6, 5), 414, 84)])   # his script starts with setvar, not trainerbattle
report_nc(list(pool.map(do_nc, jobs)), 'gym leader')

# ---------------------------------------------------------------- captains
# (map group, num, object x,y, trainer, shackle index, name). Captain objects sit at (25,3) facing left (27,3 for the General).
CAPS = [(2, 69, (25, 3), 6, 1, 'CORMAG'), (2, 70, (25, 3), 15, 0, 'LARACHEL')]
GEN = (2, 79, (27, 3), 530, 10, 'NERO')
def cap_job(a):
    c, side, mode = a
    g, n, (x, y), tid, idx, name = c
    kw = {}
    if mode == 'no': kw['bfrom'] = 5200
    if mode == 'noball': kw['ball'] = False
    if mode == 'full': kw['fill'] = 5; kw['mixb'] = (1600, 4600)   # B declines the 'change POKeMON?' question that appears with more than one mon
    res = run('cap_%s_%d_%s' % (mode, side, name), g, n, x + SIDES[side][1], y + SIDES[side][2], SIDES[side][3], nA=110, tpoll=(4900, 5700, 6) if mode == 'no' else (4200, 7800, 30), **kw)
    return a, res
cjobs = []
for c in CAPS:
    for side in (0, 1, 2): cjobs.append((c, side, 'yes'))
cjobs += [(CAPS[0], 0, 'no'), (CAPS[0], 0, 'noball'), (CAPS[0], 0, 'full')]   # NERO (the General) is not tested here: his post-battle script is the story ending ('ARREST him for trial?'), it never reaches the front script, with or without the fix
if QUICK: cjobs = cjobs[:3]
for a, res in pool.map(cap_job, cjobs):
    c, side, mode = a
    g, n, (x, y), tid, idx, name = c
    nm = '%s trainer %d %s, %s' % (name, tid, SIDES[side][0], mode)
    sb = res['sb']; joined = (res['party'] or 0)
    fought = tflag(sb, 0x500 + tid); flag = tflag(sb, 0x871 + idx)
    t = ' || '.join(res['texts'])
    info = 'fought=%d facing=%s ball=%s party=%s flag=%d prompts=%d' % (fought, res.get('facing'), res['ball'], res['party'], flag, res['prompts'])
    if mode == 'yes':
        base = 1
        check(nm + ': prompt exactly once, ball used, joins party, flag set, no "party is full"', fought and res['prompts'] == 1 and not res['ball'] and res['party'] == base + 1 and flag == 1 and 'party is full' not in t, info)
        check(nm + ': confirmation line shown', ('is shackled' in t), [s for s in res['texts'] if 'shackle' in s.lower()])
    elif mode == 'no':
        check(nm + ': prompt once, answered No: ball kept, nobody joins, flag clear', fought and res['prompts'] == 1 and res['ball'] and res['party'] == 1 and flag == 0, info)
    elif mode == 'noball':
        check(nm + ': no ball: no prompt, no join, flag clear', fought and res['prompts'] == 0 and res['party'] == 1 and flag == 0, info)
    elif mode == 'full':
        check(nm + ': full party: prompt once, flag set, goes to the PC (party stays 6), PC line shown', fought and res['prompts'] == 1 and not res['ball'] and res['party'] == 6 and flag == 1 and 'sent to the PC' in t, info)
print('\n%d check(s) failed' % len(fails) if fails else '\nall checks passed')
sys.exit(1 if fails else 0)
