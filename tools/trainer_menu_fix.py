"""Trainer menu (usage: trainer_menu_fix.py IN.gba OUT.gba), run through tools/patch.sh. Independent of every other stage; apply it after ordinary_shoot.py and shoot_order.py.

Owner rule: every trainer can be blessed, threatened or shot. Nothing is grey unless one of the options was already used:
  fresh              BLESS THREATEN SHOOT LEAVE all live                  (menu 78)
  after BLESS        BLESS THREATEN SHOOT all grey: a blessed person cannot be threatened or shot  (menu 81)
  after THREATEN     BLESS THREATEN grey, SHOOT live                      (menu 80)
  after SHOOT        the trainer is a splatter
The old post-battle menu (S1, ordinary_shoot.py) picked its rows from the 'robbed' bit, which BLESS and THREATEN both set, and from rob_info's SHOOT test
(g_shoot, and an object script that has to start with trainerbattle type 0). The 16 trainers with a continue script (type 2: Cinnabar gym, Rocket hideouts, dojo ...) had SHOOT grey,
the 14 double-battle trainers (type 4) never reached the menu, and the Kanto gym leaders, the camp women and the camp grunts (ids not in g_ids) had no menu at all. This stage replaces that menu by a new script that uses new natives (story/trainer_menu_native.c):
 - tm_info: GSV4 = 0 fresh / 1 threatened / 2 blessed, GSV6 = known trainer, GSV8 = the object talked to belongs to this trainer.
 - tm_bless: the stock bless routine plus a 'blessed' bit.  tm_pay: the money of threatening or of a shot trainer.  tm_shoot: splatters every object of the trainer, takes the party.
 - tm_wrap_load / tm_wrap_scripts: replace rob.c's apply_killed (shot trainers stay splatters); both hook literals in the gun natives are redirected.
Trainers are found by (map group, map number, local id) from a table built here from the object scripts of the ROM being patched, not by looking at the first bytes of the script.
Persistence: one 'blessed' bit per slot (417 original ranks + 23 extra trainers) in a new bit store: the vars 0x4018..0x401D and 0x40BC (112 bits) and 326 generic flags
(BIT_FLAG_RANGES), plus a used and a killed bit for each extra trainer. The original ranks keep their used bit (g_vars bit r) and killed bit (g_vars bit 512+r): the Kill Count keeps counting them.
g_vars position 12 pointed at var 0x403C, which the game sets to 0x0302 at every new game (trainers 301, 308 and 309 started 'used'); all 9 copies of the pool now point at 0x40CF there.
The police deal rule is kept: after the deal SHOOT stays live but answers 'You gave the police your word, soldiers only.' (no grey for something that was not selected).
Also here: the double-battle 'already beaten' branch of the engine script (0x1A4EFA) jumps to the post-battle script so double-battle trainers get the menu; the JRA menu uses
menu 80 after THREATEN (bless and threaten grey) and refuses a second THREATEN. The first 0x40 bytes of the front script (shackle check and prompt) are not touched."""
import sys, struct, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inc import Rom
from shinigami import SB, put_script
from g3 import ENC

SRC = os.path.join(HERE, '..', 'story')
WORK = '/tmp/trainer_menu_build'
FRONT = 0xF8CEC0
ROB_INFO = 0x08A09939
DEAL_STATE = 0x08F22DED
OLD_BLESS = 0x08EBB05D
JRA_STATE = 0x08F8C3BD
GVARS_OFF = 0xA0A2E2
JIDS_OFF = 0xF23A40                                                # the 94 JRA trainer ids (gun natives)
WRAP_LITERALS = {0xF22988: 0x08A09901, 0xF22C90: 0x08A0991D}   # gun natives: rob.c wrap_load / wrap_scripts
DOUBLE_BEATEN = 0x1A4EFA                                          # goto_if != in the double-battle engine script: 06 05 <1A4F20>
GFX_SPLAT, SPLAT_SCRIPT = 152, 0x08A09811
ITEM_TAG, ITEM_GLOCK, ITEM_9MM = 56, 52, 53
STAGE2_DATA = os.path.join(HERE, '..', 'stage2', 'data.h')

# Extra trainers (not in the original g_ids): they reach the post-battle script by talking to them again after the battle (trainerbattle types 0..2).
#   30..32 grunts (camp), 36..48 the women of the camps, 414..420 the Kanto gym leaders.
# Left alone on purpose: JRA troopers (own menu), police 50..78, story fights 49 / 743..751, the Elite Four 410..413 and Giovanni 348 and other
# type 3 scripted fights (their own scripts decide what happens after the battle).
EXTRA_IDS = [30, 31, 32] + list(range(36, 49)) + list(range(414, 421))

# New bit store. Vars 0x4018..0x401F are object graphics vars that no object template uses (templates use graphics 0xF0..0xF7 = vars 0x4010..0x4017 only), 0x40CF (VAR_FRONTIER_FACILITY, no Battle Frontier in FireRed) and 0x40BC is the unused seventh Mystery Gift var; no script of the ROM touches any of them. Flags are generic ones (FLAG_0x... in the decomp, never
# named, nothing in the maps, objects or scripts of this ROM reads or writes them, see tools/tests/trainer_menu_fix.py).
POOL_FIX = (12, 0x40CF)                                          # g_vars position 12 was var 0x403C, which the game sets to 0x0302 at every new game: trainers 301, 308 and 309 started 'used'
BIT_VARS = list(range(0x4018, 0x401E)) + [0x40BC]          # 0x401E and 0x401F belong to the police store (police_vars.py)
BIT_FLAG_RANGES = [(0x335, 0x3D7), (0x319, 0x333), (0x304, 0x317), (0x300, 0x302), (0x204, 0x22F), (0x10A, 0x153), (0xB0, 0xDA)]

def r32(b, o): return struct.unpack_from('<I', b, o)[0]
def r16(b, o): return struct.unpack_from('<H', b, o)[0]
def pk(v): return struct.pack('<H', v)

# ------------------------------------------------------------------ script walker (object scripts -> trainer ids)
SZ = {0:0,1:0,2:0,3:0,4:4,5:4,6:5,7:5,8:1,9:1,0xa:2,0xb:2,0xc:0,0xd:0,0xe:1,0xf:5,0x10:2,0x11:5,0x12:5,0x13:5,0x14:2,0x15:8,0x16:4,0x17:4,0x18:4,0x19:4,0x1a:4,
      0x1b:2,0x1c:2,0x1d:5,0x1e:5,0x1f:5,0x20:8,0x21:4,0x22:4,0x23:4,0x24:4,0x25:2,0x26:4,0x27:0,0x28:2,0x29:2,0x2a:2,0x2b:2,0x2c:4,0x2d:0,0x2e:0,0x2f:2,0x30:0,
      0x31:2,0x32:0,0x33:3,0x34:2,0x35:0,0x36:2,0x37:1,0x38:1,0x39:7,0x3a:7,0x3b:7,0x3c:2,0x3d:7,0x3e:7,0x3f:7,0x40:7,0x41:2,0x42:4,0x43:0,0x44:4,0x45:4,0x46:4,
      0x47:4,0x48:2,0x49:4,0x4a:4,0x4b:2,0x4c:2,0x4d:2,0x4e:2,0x4f:6,0x50:10,0x51:2,0x52:4,0x53:2,0x54:4,0x55:2,0x56:4,0x57:6,0x58:4,0x59:4,0x5a:0,0x5b:3,
      0x5d:0,0x5e:0,0x5f:0,0x60:2,0x61:2,0x62:2,0x63:6,0x64:2,0x65:3,0x66:0,0x67:4,0x68:0,0x69:0,0x6a:0,0x6b:0,0x6c:0,0x6d:0,0x6e:2,0x6f:4,0x70:5,0x71:5,
      0x72:4,0x73:4,0x74:0,0x75:4,0x76:0,0x77:1,0x78:4,0x79:14,0x7a:2,0x7b:4,0x7c:2,0x7d:3,0x7e:1,0x7f:3,0x80:3,0x81:3,0x82:3,0x83:3,0x84:3,0x85:5,0x86:4,
      0x87:4,0x88:4,0x89:2,0x8f:2,0x90:5,0x91:5,0x92:5,0x93:3,0x94:2,0x95:3,0x96:2,0x97:1,0x98:2,0x99:2,0x9a:1,0x9b:4,0x9c:2,0x9d:3,0x9e:2,0x9f:2,0xa0:0,
      0xa1:4,0xa2:8,0xa3:0,0xa4:2,0xa5:0,0xa6:1,0xa7:2,0xa8:5,0xa9:4}
TB_EXTRA = {0: 0, 1: 4, 2: 4, 4: 4, 5: 0, 6: 8, 7: 4, 8: 8}
GROUPS = 0x3526A8

def map_list(b):
    """(group, num, header offset) of every map; group 2 was relocated and holds 82 maps, group 1 123, group 3 66"""
    gps = [r32(b, GROUPS + 4 * i) - 0x08000000 for i in range(43)]
    sizes = {0: 5, 1: 123, 2: 82, 3: 66, 42: 1}
    for i in range(4, 42): sizes[i] = (gps[i + 1] - gps[i]) // 4
    out = []
    for g in range(43):
        for n in range(sizes[g]):
            out.append((g, n, r32(b, gps[g] + 4 * n) - 0x08000000))
    return out

def object_templates(b, h):
    ev = r32(b, h + 4) - 0x08000000
    no = b[ev]
    po = r32(b, ev + 4) - 0x08000000
    out = []
    for i in range(no):
        t = po + 24 * i
        out.append((b[t], b[t + 1], r32(b, t + 16), r16(b, t + 12)))   # local id, graphics, script, trainer type
    return out

def trainer_ids_of(b, root, maxn=400):
    """every trainerbattle (type, id) reachable from the script at file offset root (linear, follows goto / call / conditional jumps)"""
    out = []; seen = set(); q = [root]; nb = 0
    while q:
        a = q.pop()
        while 0 <= a < len(b) and a not in seen:
            seen.add(a); nb += 1
            if nb > maxn: return out
            op = b[a]
            if op == 0x5c:
                t = b[a + 1]
                out.append((t, r16(b, a + 2)))
                if t == 3: a += 10
                elif t in TB_EXTRA: a += 14 + TB_EXTRA[t]
                else: break
                continue
            if op not in SZ: break
            s = SZ[op]; args = b[a + 1:a + 1 + s]
            if op in (4, 5):
                t = struct.unpack('<I', args)[0]
                if 0x08000000 <= t < 0x0A000000: q.append(t - 0x08000000)
            if op in (6, 7):
                t = struct.unpack('<I', args[1:])[0]
                if 0x08000000 <= t < 0x0A000000: q.append(t - 0x08000000)
            a += 1 + s
            if op in (2, 3, 5, 0x24, 0x5e, 0x0c, 0x0d): break
    return out

def parse_data_h():
    t = open(STAGE2_DATA).read()
    def lst(name):
        i = t.index(name); i = t.index('{', i); j = t.index('}', i)
        return [int(x) for x in t[i + 1:j].split(',')]
    return lst('g_ids[]'), lst('g_vars[]')

def object_table(b, slot_of):
    """sorted (group, map, local id, slot) for every object whose script can start a battle with a trainer of a slot"""
    rows = set()
    for g, n, h in map_list(b):
        for lid, gfx, script, tt in object_templates(b, h):
            if not (0x08000000 <= script < 0x0A000000): continue
            for t, tid in trainer_ids_of(b, script - 0x08000000):
                if tid in slot_of: rows.add((g, n, lid, slot_of[tid]))
    return sorted(rows)

# ------------------------------------------------------------------ text lookup
def find_text(b, s):
    raw = bytes(ENC[c] for c in s) + b'\xff'
    i = bytes(b).find(raw, 0xE00000)
    assert i > 0, s
    return 0x08000000 + i

def find_text_raw(b, raw, lo=0xE00000):
    i = bytes(b).find(raw, lo)
    assert i > 0, raw.hex()
    return 0x08000000 + i

# ------------------------------------------------------------------ build
def compile_native(r, hdr, nbits_bytes_dummy=None):
    os.makedirs(WORK, exist_ok=True)
    open(os.path.join(WORK, 'tm_gen.h'), 'w').write(hdr)
    r.cur = (r.cur + 3) & ~3
    base = 0x08000000 + r.cur
    ld = os.path.join(WORK, 'tm.ld'); o = os.path.join(WORK, 'tm.o'); e = os.path.join(WORK, 'tm.elf'); bn = os.path.join(WORK, 'tm.bin')
    open(ld, 'w').write('ENTRY(tm_info)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n' % base)
    subprocess.run(['clang', '--target=thumbv4t-none-eabi', '-mthumb', '-Os', '-ffreestanding', '-fno-builtin', '-fno-pic', '-fno-stack-protector', '-nostdlib',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-I', WORK, '-c', os.path.join(SRC, 'trainer_menu_native.c'), '-o', o], check=True)
    subprocess.run(['ld.lld', '-T', ld, o, '-o', e], check=True)
    subprocess.run(['llvm-objcopy', '-O', 'binary', e, bn], check=True)
    blob = open(bn, 'rb').read()
    a = r.alloc(blob, 4)
    assert 0x08000000 + a == base, (hex(a), hex(base))
    sym = {}
    for ln in subprocess.run(['nm', e], capture_output=True, text=True, check=True).stdout.split('\n'):
        f = ln.split()
        if len(f) == 3 and f[2] in ('tm_info', 'tm_bless', 'tm_pay', 'tm_shoot', 'tm_wrap_load', 'tm_wrap_scripts'):
            sym[f[2]] = (int(f[0], 16) & ~1) | 1
    assert len(sym) == 6, sym
    return sym

def bit_locators(count):
    """count locators: the 16 graphics vars (16 bits each) first, then flags from BIT_FLAG_RANGES"""
    loc = []
    for v in BIT_VARS:
        for k in range(16): loc.append(0x8000 | ((v - 0x4000) << 4) | k)
    for lo, hi in BIT_FLAG_RANGES:
        for f in range(lo, hi + 1): loc.append(f)
    assert len(loc) >= count, (len(loc), count)
    assert len(set(loc)) == len(loc)
    return loc[:count]

def install(r):
    b = r.b
    G_IDS, G_VARS = parse_data_h()
    NG = len(G_IDS); assert NG == 417
    # the old bit store pool must be the one the natives in the ROM use
    pool = struct.pack('<64H', *G_VARS)
    assert bytes(b[GVARS_OFF:GVARS_OFF + 128]) == pool, 'g_vars pool in the ROM differs from stage2/data.h'
    assert G_VARS[POOL_FIX[0]] == 0x403C
    G_VARS = list(G_VARS); G_VARS[POOL_FIX[0]] = POOL_FIX[1]
    newpool = struct.pack('<64H', *G_VARS)
    n = 0; i = 0
    while True:                                     # every native carries its own copy of the table
        i = bytes(b).find(pool, i)
        if i < 0: break
        b[i:i + 128] = newpool; i += 128; n += 1
    assert n == 9, n
    assert bytes(b).find(struct.pack('<%dH' % NG, *G_IDS)) > 0, 'g_ids table not in the ROM'
    ids = G_IDS + EXTRA_IDS
    assert len(set(ids)) == len(ids)
    jids = set(struct.unpack_from('<94H', b, JIDS_OFF)); assert r16(b, JIDS_OFF) == 1 and not (jids & set(ids)), 'a slot trainer is a JRA trainer'
    assert not any(55 <= t <= 78 for t in ids), 'police ids are not slots'
    slot_of = {tid: s for s, tid in enumerate(ids)}
    NX = len(EXTRA_IDS); NSLOT = NG + NX
    rows = object_table(b, slot_of)
    have = {s for _, _, _, s in rows}
    missing = [ids[s] for s in range(NSLOT) if s not in have]
    # a trainer without an object is still known (menu, bless, threaten, shoot work; there is just no splatter)
    nbits = NSLOT + 2 * NX
    loc = bit_locators(nbits)
    hdr = '#define NG %d\n#define NX %d\n#define NSLOT %d\n#define NMT %d\n#define GFX_SPLAT %d\n#define SPLAT_SCRIPT 0x%08x\n#define OLD_BLESS 0x%08x\n' % (NG, NX, NSLOT, len(rows), GFX_SPLAT, SPLAT_SCRIPT, OLD_BLESS)
    hdr += 'static const u16 TM_IDS[NSLOT]={%s};\n' % ','.join(map(str, ids))
    hdr += 'static const u16 GVARS[64]={%s};\n' % ','.join(map(str, G_VARS))
    hdr += 'static const u16 BLOC[%d]={%s};\n' % (nbits, ','.join(map(str, loc)))
    hdr += 'static const u8 MT_G[NMT]={%s};\nstatic const u8 MT_N[NMT]={%s};\nstatic const u8 MT_L[NMT]={%s};\nstatic const u16 MT_S[NMT]={%s};\n' % (
        ','.join(str(x[0]) for x in rows), ','.join(str(x[1]) for x in rows), ','.join(str(x[2]) for x in rows), ','.join(str(x[3]) for x in rows))
    fn = compile_native(r, hdr)

    # ---- texts (found by content; the existing post-battle script uses the same ones)
    T = {k: find_text(b, v) for k, v in dict(
        nobless='They will not be blessed.', nothreat='They will not be threatened.', noshot='They will not be shot.', done='They have nothing left for you.',
        notag='You have no BLESS TAG.', nogun='You have nothing to threaten\nthem with.', need='You need a GLOCK and a 9MM ROUND\nto shoot.',
        mons='You took their POKéMON!', dont="Don't shoot! Here, take\neverything I have!").items()}
    T['took'] = find_text_raw(b, bytes.fromhex('d3e3e900e8e3e3df00b7fd02abff'))
    T['thanks'] = find_text_raw(b, bytes.fromhex('cedcd5e2df00ede3e900dae3e600e8dcd900d6e0d9e7e7dde2dbe7b800e1edfee7dde2e700dad9d9e000d7e0d9d5e2e7d9d8ab00c2d9e6d9b800d5e700d5fbe8e3dfd9e200e3da00e1ed00dbe6d5e8dde8e9d8d9b800dcd5ead900d5e2fedde8d9e1abff'))   # 'Thank you for the blessings ...' (breaks are FE and FB)
    T['police'] = find_text_raw(b, bytes.fromhex('d3e3e900dbd5ead900e8dcd900e4e3e0ddd7d900ede3e9e600ebe3e6d8f0fee7e3e0d8ddd9e6e700e3e2e0edadff'))

    # ---- the new menu script
    S = SB()
    S.lab('top')
    S.raw(0x23); S.ptr(fn['tm_info'])
    S.compare(0x8004, 0); S.goto_if(1, 'fresh')
    S.compare(0x8004, 1); S.goto_if(1, 'thr')
    S.raw(0x6F, 0, 0, 81, 0); S.goto('res')            # blessed: everything grey
    S.lab('fresh'); S.raw(0x6F, 0, 0, 78, 0); S.goto('res')
    S.lab('thr'); S.raw(0x6F, 0, 0, 80, 0)             # threatened: bless and threaten grey, shoot live
    S.lab('res')
    S.compare(0x800D, 0); S.goto_if(1, 'bless')
    S.compare(0x800D, 1); S.goto_if(1, 'threat')
    S.compare(0x800D, 2); S.goto_if(1, 'shoot')
    S.raw(0x5E)                                        # LEAVE / B: the trainer's own post-battle line
    def have(item, lack):
        S.raw(0x47); S._add(pk(item) + pk(1)); S.compare(0x800D, 0); S.goto_if(1, lack)
    S.lab('bless')
    S.compare(0x8004, 0); S.goto_if(5, 'nobless')
    have(ITEM_TAG, 'notag')
    S.raw(0x23); S.ptr(fn['tm_bless'])
    S.msg(T['thanks'], 4); S.raw(0x09, 0); S.goto('top')
    S.lab('nobless')
    S.compare(0x8004, 2); S.goto_if(1, 'left')
    S.msg(T['nobless'], 4); S.goto('top')              # threatened: a threatened person cannot be blessed
    S.lab('left'); S.msg(T['done'], 4); S.goto('top')
    S.lab('notag'); S.msg(T['notag'], 4); S.goto('top')
    S.lab('threat')
    S.compare(0x8004, 0); S.goto_if(5, 'nothreat')
    have(ITEM_GLOCK, 'nogun')
    S.raw(0x23); S.ptr(fn['tm_pay']); S.msg(T['dont'], 4); S.msg(T['took'], 4); S.goto('top')
    S.lab('nothreat')
    S.compare(0x8004, 2); S.goto_if(1, 'nt_bl')
    S.msg(T['done'], 4); S.goto('top')                 # threatened already
    S.lab('nt_bl'); S.msg(T['nothreat'], 4); S.goto('top')
    S.lab('nogun'); S.msg(T['nogun'], 4); S.goto('top')
    S.lab('shoot')
    S.compare(0x8004, 2); S.goto_if(1, 'noshoot')
    S.raw(0x23); S.ptr(DEAL_STATE); S.compare(0x8007, 1); S.goto_if(1, 'police')
    have(ITEM_GLOCK, 'need'); have(ITEM_9MM, 'need')
    S.raw(0x45); S._add(pk(ITEM_9MM) + pk(1))
    S.raw(0x2F); S._add(pk(347)); S.raw(0x30)
    S.compare(0x8008, 0); S.goto_if(1, 'noobj')
    S.raw(0x53); S._add(pk(0x800F)); S.raw(0x23); S.ptr(fn['tm_shoot']); S.raw(0x55); S._add(pk(0x800F))
    S.goto('shot')
    S.lab('noobj'); S.raw(0x23); S.ptr(fn['tm_shoot'])
    S.lab('shot')
    S.compare(0x8007, 0); S.goto_if(1, 'nopart')
    S.raw(0x53); S._add(pk(0x8007)); S.raw(0x55); S._add(pk(0x8007))
    S.lab('nopart')
    S.compare(0x8004, 0); S.goto_if(5, 'paid')
    S.raw(0x23); S.ptr(fn['tm_pay']); S.msg(T['took'], 4)
    S.lab('paid'); S.msg(T['mons'], 4); S.raw(0x6C); S.raw(0x02)
    S.lab('noshoot'); S.msg(T['noshot'], 4); S.goto('top')
    S.lab('police'); S.msg(T['police'], 4); S.goto('top')
    S.lab('need'); S.msg(T['need'], 4); S.goto('top')
    s2 = 0x08000000 + put_script(r, S)

    # ---- hook the front script (after its first 0x40 bytes)
    fb = bytes(b[FRONT:FRONT + 0x700])
    # (1) the ordinary branch asks tm_info instead of rob_info
    pat = bytes([0x23]) + struct.pack('<I', ROB_INFO) + bytes([0x21, 0x06, 0x80, 0x00, 0x00, 0x06, 0x01])
    i = fb.find(pat); assert i > 0x40 and fb.find(pat, i + 1) < 0, 'rob_info branch not found'
    r.w32(FRONT + i + 1, fn['tm_info'])
    # (2) the jump to the old ordinary menu (S1)
    s1 = bytes(b).find(bytes.fromhex('233999a008' + '230d2ef208' + '2104800000' + '0601'), 0x1100000)
    assert s1 > 0 and bytes(b).find(bytes.fromhex('233999a008' + '230d2ef208' + '2104800000' + '0601'), s1 + 1) < 0, 'S1 not unique'
    gp = bytes([0x05]) + struct.pack('<I', 0x08000000 + s1)
    j = fb.find(gp); assert j > 0x40 and fb.find(gp, j + 1) < 0, 'goto S1 not found'
    r.w32(FRONT + j + 1, s2)
    # (3) JRA menu: threatened shows menu 80 (bless and threaten grey), a second THREATEN is refused
    jp = bytes([0x23]) + struct.pack('<I', JRA_STATE)
    k = fb.find(jp); assert k > 0x40
    c2 = bytes([0x21, 0x04, 0x80, 0x02, 0x00, 0x06, 0x01])
    assert fb[k + 5:k + 12] == c2
    c1 = bytes([0x21, 0x04, 0x80, 0x01, 0x00, 0x06, 0x01])
    assert fb[k + 16:k + 23] == c1
    m84 = r32(b, FRONT + k + 23) - 0x08000000
    assert b[m84] == 0x6F and b[m84 + 3] == 84
    b[m84 + 3] = 80
    th = bytes([0x21, 0x0D, 0x80, 0x01, 0x00, 0x06, 0x01])
    q = fb.find(th, k); assert q > 0
    tt = r32(b, FRONT + q + 7) - 0x08000000
    assert bytes(b[tt:tt + 7]) == c2
    b[tt + 3] = 0; b[tt + 4] = 0; b[tt + 6] = 5      # cmpvar 8004,0 / goto_if != : "They will not be threatened." unless fresh
    # ---- double battles: beaten -> post-battle script
    assert bytes(b[DOUBLE_BEATEN:DOUBLE_BEATEN + 2]) == bytes([0x06, 0x05]) and r32(b, DOUBLE_BEATEN + 2) == 0x081A4F20
    r.w32(DOUBLE_BEATEN + 2, 0x08000000 + FRONT)
    # ---- map load hooks
    for off, old in WRAP_LITERALS.items():
        assert r32(b, off) == old, hex(off)
    r.w32(0xF22988, fn['tm_wrap_load']); r.w32(0xF22C90, fn['tm_wrap_scripts'])
    print('trainer_menu: slots', NSLOT, 'extra', NX, 'objects', len(rows), 'no object', missing, 'bits', nbits, 'menu', hex(s2))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end', hex(r.cur))
