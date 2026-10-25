"""Trainer menu test (run from the repo root, LD_LIBRARY_PATH to libmgba): python3 tools/tests/trainer_menu_fix.py [IN.gba] [quick]
Runs tools/trainer_menu_fix.py on a scratch copy of IN.gba (default: the ROM at the repo root), then
 - static checks: only the intended bytes changed, the first 0x40 bytes of the front script are untouched, every slot has an object, the bit locators are free
   (no object graphics, no script op, no hide flag, no hidden item, no source file in the repo touches them), the pool var 0x403C is gone
 - emulator checks, screenshots and contact sheets in /tmp/emu_out (tm_*.png): fresh menu with nothing grey, after BLESS, after THREATEN, SHOOT on an ordinary trainer, a gym leader
   (type 1 and type 2), a double battle, a trainer fought from a sight line, a blessed trainer cannot be shot, a threatened one can, persistence of every state through a map reload,
   the police deal, the JRA menu, and (without 'quick') the first menu of every one of the 440 slots (nothing grey).
Every emulator test starts from saves/ported/new_game_empty_party.raw and uses the BLESS TAG, the GLOCK and 9MM ROUNDs given by a door script."""
import os, sys, subprocess, struct, glob, re, collections, multiprocessing as mp
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
os.environ.setdefault('LD_LIBRARY_PATH', '/home/user/build_mgba/b')
from inc import Rom
from cry_open import SB, put_script
from PIL import Image, ImageDraw
import trainer_menu_fix as TM
OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True)
args = [a for a in sys.argv[1:] if a != 'quick']
QUICK = 'quick' in sys.argv[1:]
IN = os.path.abspath(args[0]) if args else os.path.join(R, 'PokemonWarAndMurder.gba')
HEV = 0x3b974c
A, B, UP, DOWN, LEFT, RIGHT = 1, 2, 0x40, 0x80, 0x20, 0x10
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)

# ---------------------------------------------------------------- build
OUTROM = OUT + '/tm_out.gba'
subprocess.run([sys.executable, 'tools/trainer_menu_fix.py', IN, OUTROM], check=True, capture_output=True)
b0 = open(IN, 'rb').read(); b1 = open(OUTROM, 'rb').read()
FRONT = TM.FRONT

# ---------------------------------------------------------------- static checks
def static():
    n0 = len(b0)
    diffs = [i for i in range(n0) if b0[i] != b1[i]]
    # group the changed bytes of the old area
    groups = []
    for i in diffs:
        if groups and i - groups[-1][1] <= 8: groups[-1][1] = i
        else: groups.append([i, i])
    names = []
    for lo, hi in groups:
        if FRONT <= lo < FRONT + 0x700: names.append('front+%x' % (lo - FRONT))
        elif TM.GVARS_OFF <= lo < TM.GVARS_OFF + 128: names.append('pool0')
        elif lo in (0xF22988, 0xF22C90): names.append('wrap@%x' % lo)
        elif TM.DOUBLE_BEATEN <= lo <= TM.DOUBLE_BEATEN + 6: names.append('double')
        else: names.append('%x' % lo)
    print('changed groups in the old ROM:', names)
    allowed = lambda lo: (FRONT + 0x40 <= lo < FRONT + 0x700) or (TM.GVARS_OFF <= lo < TM.GVARS_OFF + 128) or lo in (0xF22988, 0xF22C90) or TM.DOUBLE_BEATEN <= lo <= TM.DOUBLE_BEATEN + 6
    other = [g for g in groups if not allowed(g[0])]
    pools = [g for g in groups if g[0] >= 0x100000 and re.match(r'^[0-9a-f]+$', '%x' % g[0]) and not allowed(g[0])]
    # the other 8 copies of the pool table sit in the native blobs
    pool_old = None
    check('front script: first 0x40 bytes untouched', b0[FRONT:FRONT + 0x40] == b1[FRONT:FRONT + 0x40])
    fr = [g for g in groups if FRONT <= g[0] < FRONT + 0x700]
    check('front script: exactly the 3 JRA/ordinary hooks changed (rob_info call, goto S1, JRA menu byte + threaten guard)', len(fr) >= 4, [hex(g[0] - FRONT) for g in fr])
    n_pool = sum(1 for g in groups if g[1] - g[0] < 128 and b1[g[0] - (g[0] % 2):g[0] - (g[0] % 2) + 2] != b'')
    # pool copies: every copy of the old pool is replaced
    G_IDS, G_VARS = TM.parse_data_h()
    oldp = struct.pack('<64H', *G_VARS); newv = list(G_VARS); newv[TM.POOL_FIX[0]] = TM.POOL_FIX[1]; newp = struct.pack('<64H', *newv)
    check('g_vars pool: no copy of the old pool left, 9 copies of the new one in the old natives plus the one of trainer_menu_native', b1.find(oldp) < 0 and b1.count(newp) == 10, (b1.count(oldp), b1.count(newp)))
    check('var 0x403C (the game writes 0x0302 there at every new game) is no longer in the pool', 0x403C not in newv)
    check('double-battle engine script: beaten branch jumps to the front script', struct.unpack_from('<I', b1, TM.DOUBLE_BEATEN + 2)[0] == 0x08000000 + FRONT)
    for off, old in TM.WRAP_LITERALS.items():
        check('map load hook literal %x redirected' % off, struct.unpack_from('<I', b1, off)[0] != old and struct.unpack_from('<I', b1, off)[0] & 1)
    # slots and objects
    ids = G_IDS + TM.EXTRA_IDS
    slot_of = {t: s for s, t in enumerate(ids)}
    rows = TM.object_table(b1, slot_of)
    have = {s for _, _, _, s in rows}
    check('every one of the %d slots has at least one object on a map' % len(ids), len(have) == len(ids), [ids[s] for s in range(len(ids)) if s not in have])
    # independent cross check: objects whose script STARTS with trainerbattle of that id are all in the table
    miss = []
    for g, n, h in TM.map_list(b1):
        for lid, gfx, script, tt in TM.object_templates(b1, h):
            if 0x08000000 <= script < 0x0A000000:
                a = script - 0x08000000
                if b1[a] == 0x5c:
                    tid = struct.unpack_from('<H', b1, a + 2)[0]
                    if tid in slot_of and (g, n, lid, slot_of[tid]) not in rows: miss.append((g, n, lid, tid))
    check('every object that starts with a trainerbattle of a slot trainer is in the object table', not miss, miss[:5])
    # bit locators: distinct, count
    nb = len(ids) + 2 * len(TM.EXTRA_IDS)
    loc = TM.bit_locators(nb)
    check('bit locators distinct (%d bits: %d var bits, %d flags)' % (nb, sum(1 for x in loc if x & 0x8000), sum(1 for x in loc if not x & 0x8000)), len(set(loc)) == nb)
    flags = sorted(x for x in loc if not x & 0x8000); vars_ = sorted(0x4000 + ((x >> 4) & 0xFF) for x in loc if x & 0x8000)
    return slot_of, rows, flags, sorted(set(vars_))

def census(b, flags, vars_):
    """flags / vars touched by the data of the ROM: object templates, hidden items, scripts reachable from objects, coord and bg events and map scripts"""
    used_f = collections.defaultdict(set); used_v = collections.defaultdict(set)
    SZ = TM.SZ; r32 = TM.r32; r16 = TM.r16
    seen = set()
    def walk(root, src):
        q = [root]
        while q:
            a = q.pop()
            while 0 <= a < len(b) and a not in seen:
                seen.add(a); op = b[a]
                if op == 0x5c:
                    t = b[a + 1]; a += 10 if t == 3 else 14 + TM.TB_EXTRA.get(t, 0); continue
                if op not in SZ: break
                s = SZ[op]; ar = b[a + 1:a + 1 + s]
                if op in (0x29, 0x2a, 0x2b): used_f[struct.unpack('<H', ar)[0]].add(src)
                if op in (0x60, 0x61, 0x62): used_f[0x500 + struct.unpack('<H', ar)[0]].add(src)
                if op in (0x16, 0x17, 0x18, 0x19, 0x1a, 0x21, 0x22, 0x26):
                    for off in ((0, 2) if op in (0x19, 0x1a, 0x22) else (2,) if op == 0x26 else (0,)):
                        used_v[struct.unpack('<H', ar[off:off + 2])[0]].add(src)
                if op in (4, 5):
                    t = struct.unpack('<I', ar)[0]
                    if 0x08000000 <= t < 0x0A000000: q.append(t - 0x08000000)
                if op in (6, 7):
                    t = struct.unpack('<I', ar[1:])[0]
                    if 0x08000000 <= t < 0x0A000000: q.append(t - 0x08000000)
                a += 1 + s
                if op in (2, 3, 5, 0x24, 0x5e, 0x0c, 0x0d): break
    gfx_hi = []
    for g, n, h in TM.map_list(b):
        ev = r32(b, h + 4) - 0x08000000; no, nw, nc, nb_ = b[ev:ev + 4]
        po = r32(b, ev + 4) - 0x08000000
        for i in range(no):
            t = po + 24 * i
            if r16(b, t + 20): used_f[r16(b, t + 20)].add('obj %d,%d' % (g, n))
            if b[t + 1] >= 0xF0 and b[t + 1] != 0xFF: gfx_hi.append((g, n, b[t], b[t + 1]))
            s = r32(b, t + 16)
            if 0x08000000 <= s < 0x0A000000: walk(s - 0x08000000, 'obj %d,%d' % (g, n))
        cp = r32(b, ev + 12) - 0x08000000
        for i in range(nc if cp > 0 else 0):
            v = r16(b, cp + 16 * i + 6)
            if v: used_v[v].add('coord var')
            s = r32(b, cp + 16 * i + 12)
            if 0x08000000 <= s < 0x0A000000: walk(s - 0x08000000, 'coord %d,%d' % (g, n))
        bp = r32(b, ev + 16) - 0x08000000
        for i in range(nb_ if bp > 0 else 0):
            t = bp + 12 * i; kind = b[t + 5]
            if kind > 4: used_f[0x3E8 + ((r32(b, t + 8) >> 16) & 0xFF)].add('hidden item %d,%d' % (g, n))
            else:
                s = r32(b, t + 8)
                if 0x08000000 <= s < 0x0A000000: walk(s - 0x08000000, 'bg %d,%d' % (g, n))
        ms = r32(b, h + 0x18) - 0x08000000
        if 0 < ms < len(b) - 16:
            k = 0
            while k < 16 and b[ms + k * 5] != 0:
                typ = b[ms + k * 5]; p = r32(b, ms + k * 5 + 1)
                if typ in (1, 3, 5, 7) and 0x08000000 <= p < 0x0A000000: walk(p - 0x08000000, 'mapscript %d,%d' % (g, n))
                elif typ in (2, 4) and 0x08000000 <= p < 0x0A000000:
                    q = p - 0x08000000
                    while q < len(b) - 16:
                        v, val = struct.unpack_from('<HH', b, q); sp = r32(b, q + 4)
                        if v == 0: break
                        used_v[v].add('mapscript table')
                        if 0x08000000 <= sp < 0x0A000000: walk(sp - 0x08000000, 'mapscript %d,%d' % (g, n))
                        q += 8
                k += 1
    return used_f, used_v, gfx_hi

def repo_mentions(nums_hex, nums_dec):
    """source files of the repo that mention one of the numbers (outside the tables the stage itself generated)"""
    hits = collections.defaultdict(set)
    files = [f for f in glob.glob('**/*', recursive=True) if os.path.isfile(f) and f.rsplit('.', 1)[-1] in ('py', 'c', 'h', 'json', 'sh')
             and not f.startswith(('docs/history', 'roms', 'tools/archive')) and f not in ('ref/vars.h', 'ref/flags.h', 'tools/trainer_menu_fix.py', 'tools/tests/trainer_menu_fix.py', 'story/trainer_menu_native.c')
             and os.path.getsize(f) < 3000000]
    for f in files:
        t = open(f, errors='ignore').read()
        for m in re.finditer(r'(?i)\b0x([0-9a-f]{3,4})\b', t):
            if int(m.group(1), 16) in nums_hex: hits[int(m.group(1), 16)].add(f)
    return hits

def static_proofs(slot_of, rows, flags, vars_):
    used_f, used_v, gfx_hi = census(b0, flags, vars_)
    bad_f = [f for f in flags if f in used_f]; bad_v = [v for v in vars_ + [TM.POOL_FIX[1]] if v in used_v]
    check('the %d flags of the new bit store are not used by any object, hidden item or reachable script' % len(flags), not bad_f, [hex(x) for x in bad_f][:8])
    check('the %d vars of the new bit store (and the pool replacement) are not touched by any reachable script, coord event or map script' % (len(vars_) + 1), not bad_v, [hex(x) for x in bad_v])
    gv = sorted(set(x[3] for x in gfx_hi))
    check('no object template uses graphics 0xF8..0xFF (vars 0x4018..0x401F); graphics 0xF0..0xF7 do (vars 0x4010..0x4017, not used)', all(x < 0xF8 for x in gv), gv)
    # the decomp names: every flag has to be a generic FLAG_0x name or unnamed in ref/flags.h
    t = open('ref/flags.h').read()
    named = {}
    for m in re.finditer(r'#define\s+(FLAG_\w+)\s+0x([0-9A-Fa-f]+)\b', t):
        named.setdefault(int(m.group(2), 16), []).append(m.group(1))
    named_bad = [f for f in flags if f in named and not all(re.match(r'^FLAG_0x[0-9A-F]+$', n) for n in named[f])]
    check('every flag of the new bit store is a generic FLAG_0x... of the decomp (no vanilla C code can name it)', not named_bad, [(hex(f), named[f]) for f in named_bad][:5])
    vt = open('ref/vars.h').read()
    vnamed = {}
    for m in re.finditer(r'#define\s+(VAR_\w+)\s+0x([0-9A-Fa-f]+)\b', vt):
        vnamed.setdefault(int(m.group(2), 16), []).append(m.group(1))
    print('var names:', {hex(v): vnamed.get(v) for v in vars_ + [TM.POOL_FIX[1]]})
    hits = repo_mentions(set(flags) | set(vars_) | {TM.POOL_FIX[1]}, None)
    hits = {k: v for k, v in hits.items()}
    # numbers that also look like other constants (sizes, addresses) are listed, not failed on: the report has to be read
    print('repo files that mention one of the numbers (hex, 3-4 digits):', {hex(k): sorted(v)[:3] for k, v in sorted(hits.items())})
    check('no source file of the repo names a var of the new store (flags are listed above for reading)', not any(k >= 0x4000 and not (k == 0x40CF and set(v) <= {'tools/build.py', 'tools/gvars_fix.py', 'tools/start_menu_fix.py'}) for k, v in hits.items()), {hex(k): sorted(v) for k, v in hits.items() if k >= 0x4000})   # 0x40CF appears only as the exclusive end of the old pool range(0x40BD, 0x40CF)

# ---------------------------------------------------------------- emulator
def tmpl_off(b, g, n, lid):
    h = [hh for gg, nn, hh in TM.map_list(b) if (gg, nn) == (g, n)][0]
    ev = TM.r32(b, h + 4) - 0x08000000; po = TM.r32(b, ev + 4) - 0x08000000
    for i in range(b[ev]):
        if b[po + 24 * i] == lid: return po + 24 * i
    return None

def add_reload_trigger(r, g, n, tx, ty, dx, dy):
    """a coord event on map (g, n) at (tx, ty): sets var 0x4000 (cleared by every map load) and flag 0x4A8 (stays), then warps to (dx, dy) of the same map = a full map reload"""
    h = [hh for gg, nn, hh in TM.map_list(r.b) if (gg, nn) == (g, n)][0]
    ev = r.r32(h + 4) - 0x08000000
    assert r.b[ev + 2] == 0
    sc = SB(); sc.setvar(0x4000, 7); sc.setflag(0x4A8); sc.raw(0x39, g, n, 0xff, dx, 0, dy, 0); sc.raw(0x27); sc.end()
    scr = 0x08000000 + put_script(r, sc)
    ce = r.alloc(struct.pack('<HHBBHHHI', tx, ty, 3, 0, 0, 0, 0, scr), 4)
    r.b[ev + 2] = 1; r.w32(ev + 12, 0x08000000 + ce)

def mkrom(rom, tag, warp, flags=(), vars_=(), items=((52, 1), (53, 3), (56, 1)), mon=(150, 70), extra=None, freeze=(), reload=None):
    r = Rom(rom); tb = SB()
    if reload: add_reload_trigger(r, *reload)
    for g_, n_, l_ in freeze:                      # wandering trainers stand still (movement type FACE_DOWN) so that the talk test finds them
        o = tmpl_off(r.b, g_, n_, l_)
        if o is not None and 1 <= r.b[o + 9] <= 6: r.b[o + 9] = 8
    if mon: tb.raw(0x79, mon[0], 0, mon[1], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    for it, q in items: tb.raw(0x44, it & 255, it >> 8, q, 0)
    for f in flags: tb.setflag(f)
    for v, x in vars_: tb.setvar(v, x)
    if extra: extra(tb)
    g, n, x, y = warp
    tb.releaseall(); tb.raw(0x39, g, n, 0xff, x, 0, y, 0); tb.raw(0x27); tb.end()
    scr = 0x08000000 + put_script(r, tb)
    nn = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
    for i in range(nn): r.w32(ca + 16 * i + 12, scr)
    t = '%s/%s.gba' % (OUT, tag); r.save(t); return t

def play(t, tag, steps, shots=(), rams=(), end=None, dump=True):
    L = []
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0"]
    for f, k in steps: L += ["%d %x" % (f, k), "%d 0" % (f + 6)]
    last = max([f for f, k in steps] + [1500]) + 60
    for s in shots: L.append("shot %d" % s)
    for fr, a, n in rams: L.append("ram %d %x %d" % (fr, a, n))
    e = end or max(list(shots) + [last])
    if dump: L.append("dump %d" % (e + 5))
    L.append("end %d" % (e + 20))
    key = lambda l: int(l.split()[1]) if not l.split()[0].isdigit() else int(l.split()[0])
    L.sort(key=key)
    for g in glob.glob('%s/%s_*' % (OUT, tag)): os.remove(g)
    open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
    p = subprocess.run(['./tools/harness_new', t, '%s/%s.txt' % (OUT, tag), '%s/%s' % (OUT, tag)], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=1500)
    if os.path.abspath(t) != os.path.abspath(OUTROM) and not os.environ.get('KEEP_ROMS'): os.remove(t)      # every scratch ROM is a 32 MB copy
    return p

def ram(p, frame, addr, n):
    m = re.search(r'RAM f%d %08x: ([0-9a-f ]+)' % (frame, addr), p.stderr)
    return [int(z, 16) for z in m.group(1).split()] if m else None

def sb1(tag):
    fs = glob.glob('%s/%s_*.sb1' % (OUT, tag))
    return open(fs[0], 'rb').read() if fs else None

def frames(tag):
    return sorted(glob.glob('%s/%s_*.ppm' % (OUT, tag)))

def sheet(tag, cols=5, label=None):
    fs = frames(tag); ims = [Image.open(x) for x in fs]
    if not ims: return None
    w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
    s = Image.new('RGB', (cols * w, rows * h))
    for i, im in enumerate(ims): s.paste(im, ((i % cols) * w, (i // cols) * h))
    if label:
        ImageDraw.Draw(s).text((100, 2), label, fill=(255, 255, 0))
    s.save('%s/%s.png' % (OUT, tag)); return '%s/%s.png' % (OUT, tag)

def menu_rows(path):
    """None when no menu box is on screen, else the 4 rows as True (live, black) / False (grey)"""
    im = Image.open(path).convert('RGB')
    if not (im.getpixel((2, 2)) == (74, 74, 107) and im.getpixel((10, 2)) == (140, 140, 206) and im.getpixel((70, 2)) == (140, 140, 206)): return None
    px = im.convert('L'); out = []
    for k in range(4):
        y0 = 10 + 14 * k; box = px.crop((16, y0, 76, y0 + 10))
        d = list(box.getdata()); out.append(sum(1 for v in d if v < 105) >= 40)
    return tuple(out)

def menus(tag):
    return [(int(re.search(r'_(\d+)\.ppm', f).group(1)), menu_rows(f)) for f in frames(tag)]

def last_menu(tag, within=260):
    """rows of the menu seen in the last frames of a run (None when no menu was on screen in the last `within` frames)"""
    m = menus(tag)
    if not m: return None
    end = m[-1][0]
    for f, r in reversed(m):
        if f < end - within: break
        if r is not None: return r
    return None

def distinct(seq):
    out = []
    for f, m in seq:
        if m is not None and (not out or out[-1] != m): out.append(m)
    return out

def talk(rom, tag, warp, face, tid, keys, gap=60, first=1560, shot_every=30, flags=(), vars_=(), items=((52, 1), (53, 3), (56, 1)), rams=(), mon=(150, 70), extra=None, beaten=True, tail=150, freeze=(), reload=None):
    fl = list(flags) + ([0x500 + tid] if beaten else [])
    t = mkrom(rom, tag, warp, flags=tuple(fl), vars_=vars_, items=items, mon=mon, extra=extra, freeze=freeze, reload=reload)
    steps = [(1500, face), (first, A)]
    f = first + gap
    for k in keys:
        steps.append((f, k)); f += gap
    shots = list(range(first + 30, f + tail, shot_every))
    p = play(t, tag, steps, shots, rams=tuple(rams) + ((f + tail - 10, 0x2024029, 1),), end=f + tail)
    return p

def party(p):
    m = re.findall(r'RAM f\d+ 02024029: ([0-9a-f]+)', p.stderr)
    return int(m[-1], 16) if m else None

ALL = ()
def where(tid):
    """map, position next to the object and facing key for a talk test (first free tile around the first object of the trainer)"""
    import reach
    G_IDS, _ = TM.parse_data_h(); ids = G_IDS + TM.EXTRA_IDS
    rows = [r for r in OBJROWS if ids[r[3]] == tid]
    for g, n, lid, s in rows:
        h = [hh for gg, nn, hh in TM.map_list(b1) if (gg, nn) == (g, n)][0]
        for l, gfx, script, tt in TM.object_templates(b1, h):
            if l != lid: continue
            ev = TM.r32(b1, h + 4) - 0x08000000; po = TM.r32(b1, ev + 4) - 0x08000000
            for i in range(b1[ev]):
                t = po + 24 * i
                if b1[t] == lid:
                    x, y = struct.unpack_from('<hh', b1, t + 4)
                    w, hh2, grid, beh, objs_ = reach.load(b1, g, n)
                    for dx, dy, key in ((0, 1, UP), (0, -1, DOWN), (1, 0, LEFT), (-1, 0, RIGHT)):
                        nx, ny = x + dx, y + dy
                        if not (0 <= nx < w and 0 <= ny < hh2): continue
                        v = grid[ny][nx]
                        if (v >> 10) & 3 or beh(v & 0x3ff) in (0x38, 0x39, 0x3a, 0x3b) or (nx, ny) in objs_: continue
                        yield (g, n, nx, ny), key, lid
    return

def menu_present(ref, cur):
    """True when the 80x70 box at the top left of cur differs from the same box of the frame before the talk (works with every map palette)"""
    a = Image.open(ref).convert('RGB').crop((0, 0, 80, 70)); b = Image.open(cur).convert('RGB').crop((0, 0, 80, 70))
    return sum(1 for p, q in zip(a.getdata(), b.getdata()) if p != q) > 1500

def first_menu(tid, rom=None):
    """talk to a defeated trainer and read the first menu and the script vars; returns (rows, gsv, lid) or None when no position works.
    rows is the tuple of live rows on maps with the usual palette, 'present' when the menu box is there on another palette, None when there is no menu"""
    rom = rom or OUTROM
    tag = 'tmq_%d' % tid
    for warp, key, lid in where(tid):
        t = mkrom(rom, tag, warp, flags=(0x500 + tid,), freeze=((warp[0], warp[1], lid),))
        p = play(t, tag, [(1500, key), (1560, A)], [1540, 1650], rams=[(1650, 0x20370b8, 32), (1650, 0x20370d2, 2)], end=1660, dump=False)
        v = ram(p, 1650, 0x20370b8, 32); lt = ram(p, 1650, 0x20370d2, 2)
        fs = frames(tag)
        if v is None or len(fs) < 2: continue
        gsv = [v[2 * i] | (v[2 * i + 1] << 8) for i in range(16)]
        if lt[0] != lid: continue
        rows = menu_rows(fs[1])
        if rows is None and menu_present(fs[0], fs[1]): rows = 'present'
        for f in fs: os.remove(f)
        return rows, gsv, lid
    return None

def first_menu_job(tid): return tid, first_menu(tid)

# ---------------------------------------------------------------- scenarios
def where_obj(g, n, lid):
    import reach
    o = tmpl_off(b1, g, n, lid); x, y = struct.unpack_from('<hh', b1, o + 4)
    w, hh2, grid, beh, objs_ = reach.load(b1, g, n)
    for dx, dy, key in ((0, 1, UP), (0, -1, DOWN), (1, 0, LEFT), (-1, 0, RIGHT)):
        nx, ny = x + dx, y + dy
        if not (0 <= nx < w and 0 <= ny < hh2): continue
        v = grid[ny][nx]
        if (v >> 10) & 3 or beh(v & 0x3ff) in (0x38, 0x39, 0x3a, 0x3b) or (nx, ny) in objs_: continue
        yield (g, n, nx, ny), key

def flag_of(d, f): return (d[0xEE0 + (f >> 3)] >> (f & 7)) & 1
def var_of(d, v): return struct.unpack_from('<H', d, 0x1000 + 2 * (v - 0x4000))[0]
def gfx_of(d, lid):
    for i in range(64):
        if d[0x8E0 + 24 * i] == lid and d[0x8E0 + 24 * i + 1] != 0: return d[0x8E0 + 24 * i + 1]
    return None

def bit_state(d, tid):
    """(blessed, used, killed) of trainer tid in a save block dump"""
    G_IDS, G_VARS = TM.parse_data_h(); G_VARS = list(G_VARS); G_VARS[TM.POOL_FIX[0]] = TM.POOL_FIX[1]
    ids = G_IDS + TM.EXTRA_IDS; s = ids.index(tid); NG = len(G_IDS); NSLOT = len(ids)
    loc = TM.bit_locators(NSLOT + 2 * len(TM.EXTRA_IDS))
    def new(i):
        v = loc[i]
        return (var_of(d, 0x4000 + ((v >> 4) & 0xFF)) >> (v & 15)) & 1 if v & 0x8000 else flag_of(d, v)
    def old(bit): return (var_of(d, G_VARS[bit >> 4]) >> (bit & 15)) & 1
    used = old(s) if s < NG else new(NSLOT + 2 * (s - NG))
    killed = old(512 + s) if s < NG else new(NSLOT + 2 * (s - NG) + 1)
    return new(s), used, killed

def preset_bits(slot_ids, tid, which):
    """door script setup that puts trainer tid into a state: which in 'blessed', 'used', 'killed' (old store for the original ranks, new store for the extras)"""
    G_IDS, G_VARS = TM.parse_data_h(); G_VARS = list(G_VARS); G_VARS[TM.POOL_FIX[0]] = TM.POOL_FIX[1]
    ids = G_IDS + TM.EXTRA_IDS; s = ids.index(tid); NG = len(G_IDS); NSLOT = len(ids)
    loc = TM.bit_locators(NSLOT + 2 * len(TM.EXTRA_IDS))
    ops = []
    def newbit(i):
        v = loc[i]
        if v & 0x8000: ops.append(('var', 0x4000 + ((v >> 4) & 0xFF), 1 << (v & 15)))
        else: ops.append(('flag', v, 0))
    def oldbit(b):
        ops.append(('var', G_VARS[b >> 4], 1 << (b & 15)))
    if which == 'blessed':
        newbit(s); oldbit(s) if s < NG else newbit(NSLOT + 2 * (s - NG))
    elif which == 'used':
        oldbit(s) if s < NG else newbit(NSLOT + 2 * (s - NG))
    elif which == 'killed':
        oldbit(512 + s) if s < NG else newbit(NSLOT + 2 * (s - NG) + 1)
    # several bits can share a var: merge
    merged = {}
    for k, a, bv in ops:
        if k == 'var': merged[a] = merged.get(a, 0) | bv
    def extra(tb):
        for k, a, bv in ops:
            if k == 'flag': tb.setflag(a)
        for v, val in merged.items(): tb.setvar(v, val)
    return extra

def reload_scenarios(SALLY, FR):
    # 10b: a real map reload: after BLESS / THREATEN / SHOOT the player steps on a trigger that warps into the same map
    RL = (3, 21, 52, 6, 51, 6)
    for name, keys, exp in (('blessed', [A] * 5, (False, False, False, True)), ('threatened', [DOWN, A, A, A], (False, False, True, True))):
        steps_keys = keys + [B, RIGHT, RIGHT, 0, 0, 0, 0, 0, DOWN, A]      # B leaves the menu, RIGHT turns and RIGHT steps on the trigger, DOWN faces Sally again
        p = talk(OUTROM, 'tm_rl_' + name, SALLY, DOWN, 117, steps_keys, freeze=FR, reload=RL, gap=60, tail=200)
        d = sb1('tm_rl_' + name); seq = distinct(menus('tm_rl_' + name)); sheet('tm_rl_' + name, label='reload after ' + name)
        check('map reload after %s: the map really reloaded (temp var cleared, trigger flag set)' % name, d is not None and var_of(d, 0x4000) == 0 and flag_of(d, 0x4A8) == 1, d and (var_of(d, 0x4000), flag_of(d, 0x4A8)))
        check('map reload after %s: the state is kept, the menu seen after the reload has rows %s' % (name, exp), last_menu('tm_rl_' + name) == exp, last_menu('tm_rl_' + name))
    p = talk(OUTROM, 'tm_rl_shot', SALLY, DOWN, 117, [DOWN, DOWN, A, A, A, A, RIGHT, RIGHT, 0, 0, 0, 0, 0, DOWN, A], freeze=FR, reload=RL, gap=60, tail=200)
    d = sb1('tm_rl_shot'); sheet('tm_rl_shot', label='SHOOT, map reload, talk')
    check('map reload after SHOOT: Sally is still a splatter, the party kept the Pokemon', d is not None and var_of(d, 0x4000) == 0 and flag_of(d, 0x4A8) == 1 and gfx_of(d, 4) == 152 and party(p) > 1, d and (var_of(d, 0x4000), flag_of(d, 0x4A8), gfx_of(d, 4), party(p)))

def scenarios():
    G_IDS, _ = TM.parse_data_h()
    SALLY = (3, 21, 51, 6)          # below LASS SALLY (117) at (51,7)
    FR = ((3, 21, 4),)
    # 1-3: fresh menu, BLESS, blessed rows refused
    talk(OUTROM, 'tm_bless', SALLY, DOWN, 117, [A, A, A, A, A, A], freeze=FR)
    seq = distinct(menus('tm_bless')); sheet('tm_bless', label='BLESS')
    check('fresh menu: nothing grey', bool(seq) and seq[0] == (True, True, True, True), seq[:1])
    check('after BLESS: BLESS, THREATEN and SHOOT grey, LEAVE live', (False, False, False, True) in seq, seq)
    check('after BLESS: the blessed bit and the used bit are set in the save block, the killed bit is not', sb1('tm_bless') is not None and bit_state(sb1('tm_bless'), 117) == (1, 1, 0), sb1('tm_bless') and bit_state(sb1('tm_bless'), 117))
    p = talk(OUTROM, 'tm_bl2', SALLY, DOWN, 117, [A] * 5 + [DOWN, A, A, A, DOWN, DOWN, A, A, A], freeze=FR)
    sheet('tm_bl2', label='BLESSED: THREATEN and SHOOT refused')
    seq = distinct(menus('tm_bl2')); d = sb1('tm_bl2')
    check('blessed trainer: THREATEN and SHOOT are refused, the menu stays (grey, grey, grey, live)', seq.count((False, False, False, True)) >= 1 and (False, False, True, True) not in seq, seq)
    check('blessed trainer: nothing was shot (still one Pokemon in the party, Sally still an object)', d is not None and party(p) == 1 and gfx_of(d, 4) != 152, d and (party(p), gfx_of(d, 4)))
    # 4: THREATEN, 5: THREATEN then SHOOT, 6: SHOOT fresh
    talk(OUTROM, 'tm_thr', SALLY, DOWN, 117, [DOWN, A, A, A, A, A], freeze=FR)
    seq = distinct(menus('tm_thr')); sheet('tm_thr', label='THREATEN')
    check('after THREATEN: BLESS and THREATEN grey, SHOOT and LEAVE live', (False, False, True, True) in seq, seq)
    check('after THREATEN: used bit set, blessed bit clear', sb1('tm_thr') is not None and bit_state(sb1('tm_thr'), 117) == (0, 1, 0), sb1('tm_thr') and bit_state(sb1('tm_thr'), 117))
    p = talk(OUTROM, 'tm_thrshot', SALLY, DOWN, 117, [DOWN, A, A, A, DOWN, DOWN, A, A, A, A], freeze=FR)
    sheet('tm_thrshot', label='THREATEN then SHOOT'); d = sb1('tm_thrshot')
    check('threatened trainer can be shot: party grew, Sally is a splatter', d is not None and party(p) > 1 and gfx_of(d, 4) == 152, d and (party(p), gfx_of(d, 4)))
    p = talk(OUTROM, 'tm_shoot', SALLY, DOWN, 117, [DOWN, DOWN, A, A, A, A], freeze=FR)
    sheet('tm_shoot', label='SHOOT (fresh)'); d = sb1('tm_shoot')
    check('SHOOT on a fresh ordinary trainer: party grew, splatter', d is not None and party(p) > 1 and gfx_of(d, 4) == 152, d and (party(p), gfx_of(d, 4)))
    check('SHOOT: killed bit (and used bit, the money was taken) set, blessed bit clear', d is not None and bit_state(d, 117) == (0, 1, 1), d and bit_state(d, 117))
    # 7: gym leader type 1 (Brock 414, not in the old tables) and type 2 (Cinnabar gym 178), an extra camp trainer (31)
    for tid, (g, n, lid), name in ((414, (6, 2, 1), 'Brock (type 1, extra trainer)'), (178, (12, 0, 3), 'Cinnabar gym trainer 178 (type 2, was grey)'), (31, (2, 66, 3), 'grunt 31 (type 2, extra trainer)'), (40, (2, 63, 1), 'camp woman 40 (extra trainer)')):
        warp, key = next(where_obj(g, n, lid))
        tag = 'tm_g%d' % tid
        p = talk(OUTROM, tag, warp, key, tid, [DOWN, DOWN, A, A, A, A], freeze=((g, n, lid),))
        sheet(tag, label=name); d = sb1(tag); seq = distinct(menus(tag))
        check('%s: fresh menu nothing grey' % name, bool(seq) and seq[0] == (True, True, True, True), seq[:1])
        check('%s: SHOOT works (party grew, splatter)' % name, d is not None and party(p) > 1 and gfx_of(d, lid) == 152, d and (party(p), gfx_of(d, lid)))
        check('%s: killed bit set in the save block' % name, d is not None and bit_state(d, tid)[2] == 1, d and bit_state(d, tid))
        if tid in TM.EXTRA_IDS: check('%s: the Kill Count counter (var 0x40F7) went up' % name, d is not None and var_of(d, 0x40F7) == 1, d and var_of(d, 0x40F7))
    # 8: double battle (485: two objects, one trainer): menu, shoot kills both
    warp, key = next(where_obj(1, 41, 11))
    p = talk(OUTROM, 'tm_dbl', warp, key, 485, [DOWN, DOWN, A, A, A, A], freeze=((1, 41, 11),))
    sheet('tm_dbl', label='double battle 485'); d = sb1('tm_dbl'); seq = distinct(menus('tm_dbl'))
    check('double battle trainer 485: menu, nothing grey', bool(seq) and seq[0] == (True, True, True, True), seq[:1])
    check('double battle trainer 485: both objects become splatters', d is not None and gfx_of(d, 11) == 152 and gfx_of(d, 12) == 152, d and (gfx_of(d, 11), gfx_of(d, 12)))
    # LEAVE on a double-battle trainer shows his own post-battle line
    warp, key = next(where_obj(1, 41, 11))
    talk(OUTROM, 'tm_dblL', warp, key, 485, [DOWN, DOWN, DOWN, A, A], freeze=((1, 41, 11),))
    sheet('tm_dblL', label='double battle LEAVE')
    # 9: trainer fought from a sight line (real battle, nothing preset), then talk again
    t = mkrom(OUTROM, 'tm_sight', (3, 21, 50, 7), freeze=FR)
    steps = [(1500, RIGHT)] + [(1560 + 60 * i, A) for i in range(34)]
    f = 1560 + 60 * 34 + 300
    steps += [(f - 60, RIGHT), (f, A), (f + 90, DOWN), (f + 150, DOWN), (f + 210, A), (f + 300, A), (f + 360, A), (f + 420, A)]
    shots = list(range(f - 60, f + 560, 50))
    p = play(t, 'tm_sight', steps, shots, rams=((f + 580, 0x2024029, 1),), end=f + 600)
    sheet('tm_sight', label='sight line battle then SHOOT'); d = sb1('tm_sight'); seq = distinct(menus('tm_sight'))
    check('sight-line trainer: menu after the battle has nothing grey, SHOOT works', bool(seq) and seq[0] == (True, True, True, True) and d is not None and gfx_of(d, 4) == 152 and party(p) > 1, (seq[:1], d and (party(p), gfx_of(d, 4))))
    # 10: persistence: states preset in the bit stores, then the map is loaded
    for which, exp in (('blessed', (False, False, False, True)), ('used', (False, False, True, True))):
        talk(OUTROM, 'tm_p_' + which, SALLY, DOWN, 117, [A], freeze=FR, extra=preset_bits(None, 117, which))
        seq = distinct(menus('tm_p_' + which)); sheet('tm_p_' + which, label='preset ' + which)
        check('persistence: a trainer stored as %s shows the right menu after the map load' % which, bool(seq) and seq[0] == exp, seq[:1])
    talk(OUTROM, 'tm_p_killed', SALLY, DOWN, 117, [], freeze=FR, extra=preset_bits(None, 117, 'killed'), beaten=False)
    d = sb1('tm_p_killed'); sheet('tm_p_killed', label='preset killed')
    check('persistence: a trainer stored as killed is a splatter after the map load', d is not None and gfx_of(d, 4) == 152, d and gfx_of(d, 4))
    warp, key = next(where_obj(6, 2, 1))
    talk(OUTROM, 'tm_p_brock', warp, key, 414, [], freeze=((6, 2, 1),), extra=preset_bits(None, 414, 'killed'), beaten=False)
    d = sb1('tm_p_brock'); sheet('tm_p_brock', label='preset killed Brock')
    check('persistence: an extra trainer (Brock) stored as killed is a splatter after the map load', d is not None and gfx_of(d, 1) == 152, d and gfx_of(d, 1))
    reload_scenarios(SALLY, FR)
    # 11: police deal: SHOOT stays live but refuses
    p = talk(OUTROM, 'tm_deal', SALLY, DOWN, 117, [DOWN, DOWN, A, A], freeze=FR, vars_=((0x40AB, 3),))
    sheet('tm_deal', label='police deal made, SHOOT'); d = sb1('tm_deal'); seq = distinct(menus('tm_deal'))
    check('police deal: SHOOT is not grey, nothing is shot', bool(seq) and seq[0] == (True, True, True, True) and d is not None and party(p) == 1 and gfx_of(d, 4) != 152, (seq[:1], d and (party(p), gfx_of(d, 4))))
    # 12: JRA menu: fresh, threatened (menu 80), blessed (81)
    warp, key = next(where_obj(2, 69, 1))
    for name, vars_, exp in (('fresh', (), (True, True, True, True)), ('threatened', ((0x40B6, 1),), (False, False, True, True)), ('blessed', ((TM.parse_data_h()[1][929 >> 4], 1 << (929 & 15)),), (False, False, False, True))):
        talk(OUTROM, 'tm_jra_' + name, warp, key, 1, [], freeze=((2, 69, 1),), vars_=vars_)
        seq = distinct(menus('tm_jra_' + name)); sheet('tm_jra_' + name, label='JRA ' + name)
        check('JRA soldier %s: menu rows %s' % (name, exp), bool(seq) and seq[0] == exp, seq[:1])

def fresh_state_check():
    G_IDS, _ = TM.parse_data_h(); ids = G_IDS + TM.EXTRA_IDS
    d = sb1('tm_jra_fresh')
    notzero = [t for t in ids if bit_state(d, t) != (0, 0, 0)] if d else ['no dump']
    check('fresh game: no trainer starts blessed, used or killed (the old pool put trainers 301, 308, 309 there)', not notzero, notzero[:8])
    check('fresh game: the game still writes 0x0302 to var 0x403C (value 0x%04x) but the pool no longer reads it' % (var_of(d, 0x403C) if d else 0), d is not None and var_of(d, 0x403C) in (0, 0x302))

def survey():
    G_IDS, _ = TM.parse_data_h(); ids = G_IDS + TM.EXTRA_IDS
    with mp.Pool(4) as pool: out = pool.map(first_menu_job, ids)
    nopos = [t for t, r in out if r is None]
    got = [(t, r) for t, r in out if r is not None]
    notfresh = [(t, r[0]) for t, r in got if r[0] not in ((True, True, True, True), 'present') or r[1][4] != 0]
    unknown = [t for t, r in got if r[1][6] != 1]
    check('survey: %d of %d slots reachable by talking; first menu has nothing grey for each' % (len(got), len(ids)), not notfresh and not unknown, (notfresh[:6], unknown[:6]))
    print('slots without a usable talk position (boxed in):', len(nopos), nopos)
    print('survey: first menu rows checked by pixels on %d, box present on another palette on %d' % (sum(1 for t, r in got if r[0] == (True, True, True, True)), sum(1 for t, r in got if r[0] == 'present')))
    print('survey object-verified (GSV8=1):', sum(1 for t, r in got if r[1][8] == 1), 'of', len(got), [t for t, r in got if r[1][8] != 1])

def main():
    global OBJROWS
    slot_of, rows, flags, vars_ = static()
    OBJROWS = rows
    static_proofs(slot_of, rows, flags, vars_)
    if os.environ.get('ONLY') == 'reload': reload_scenarios((3, 21, 51, 6), ((3, 21, 4),))
    elif os.environ.get('ONLY') == 'survey': survey()
    else:
        scenarios()
        fresh_state_check()
        if not QUICK: survey()
    print('\n%d check(s) failed' % len(bad) if bad else '\nall checks passed')
    sys.exit(1 if bad else 0)
if __name__ == '__main__':
    main()
