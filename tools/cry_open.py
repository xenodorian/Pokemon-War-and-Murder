# CryMon cottage opening, ported onto the Outlaw FireRed ROM.
# Naming screen leads with MAX. Player's house 1F uses the CryMon wood tiles.
# Father, empty bed, shelf (Sandshrew) and crate (Potion) replace Mom's scene.
# Oak has no starters and says he was robbed. The ultra-ball man and the
# Pallet exit block are gone. Mason (Gary's sprite) battles on the way out.
# Anne (Lass sprite) gives five Poke Balls after that fight.
# Quillpup -> Sandshrew, Glimmoth -> Pikachu, linen wrap -> Potion,
# capture crystals -> Poke Balls.
import sys, struct
from PIL import Image
sys.path.insert(0, '/workspace/Pokemon-Outlaw-Mod/tools')
from inc import Rom
from g3 import ENC
import gfx

SRC = '/workspace/Pokemon-Outlaw-Mod/roms/m_final_latest_build.gba'
TILE = '/tmp/Psuedo-CryMon/CryMon/public/sprites'
MARKER = b'CRYOPEN1'

F_TOOK, F_CRATE, F_MASON, F_ANNE = 0x4E6, 0x4E7, 0x4E8, 0x4E9
HIDE_MASON, HIDE_ANNE, HIDE_ULTRA, HIDE_MOM = 0x4EA, 0x4EB, 0x4EC, 0x4ED
# 0x406D is an unused map-scene slot. 0x40F7 is the police kill counter.
VAR_CRY = 0x406D
VAR_OAK_SCENE = 0x4050
FLAG_HIDE_OAK = 0x02B
FLAG_BALLS = (0x028, 0x029, 0x02A)
SANDSHREW, PIKACHU = 27, 25
POTION, POKEBALL = 13, 4
GFX_BLUE, GFX_LASS, GFX_LAYING = 72, 22, 34
T_TABLE = 0x798790
T_CLASS, T_PIC = 81, 106          # rival early class, Gary battle pic
PAL = 10
KEEP = {0x12, 0x13, 0x14, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F}

class SB:
    def __init__(s):
        s.parts = []
        s.labels = {}
        s.size = 0
    def raw(s, *b):
        b = bytes(b)
        s.parts.append(('b', b))
        s.size += len(b)
    def ptr(s, p):
        s.parts.append(('p', p))
        s.size += 4
    def lab(s, n):
        s.labels[n] = s.size
    def ref(s, n):
        s.parts.append(('l', n))
        s.size += 4
    def build(s, base):
        out = bytearray()
        for k, v in s.parts:
            if k == 'b':
                out += v
            elif k == 'p':
                out += struct.pack('<I', v)
            else:
                out += struct.pack('<I', 0x08000000 + base + s.labels[v])
        return bytes(out)
    def msg(s, p, std=4):
        s.raw(0x0f, 0)
        s.ptr(p)
        s.raw(0x09, std)
    def close(s):
        s.raw(0x68)
    def lock(s):
        s.raw(0x6a)
    def lockall(s):
        s.raw(0x69)
    def release(s):
        s.raw(0x6c)
    def releaseall(s):
        s.raw(0x6b)
    def face(s):
        s.raw(0x5a)
    def end(s):
        s.raw(0x02)
    def setflag(s, f):
        s.raw(0x29)
        s.raw(*struct.pack('<H', f))
    def clearflag(s, f):
        s.raw(0x2a)
        s.raw(*struct.pack('<H', f))
    def chkflag(s, f):
        s.raw(0x2b)
        s.raw(*struct.pack('<H', f))
    def setvar(s, v, n):
        s.raw(0x16)
        s.raw(*struct.pack('<HH', v, n))
    def cmp(s, v, n):
        s.raw(0x21)
        s.raw(*struct.pack('<HH', v, n))
    def goto(s, n):
        s.raw(0x05)
        s.ref(n)
    def goto_if(s, cond, n):
        s.raw(0x06, cond)
        s.ref(n)
    def move(s, who, p):
        s.raw(0x4f)
        s.raw(*struct.pack('<H', who))
        s.ptr(p)
    def waitmove(s, who=0):
        s.raw(0x51)
        s.raw(*struct.pack('<H', who))
    def addobj(s, i):
        s.raw(0x55)
        s.raw(*struct.pack('<H', i))
    def remobj(s, i):
        s.raw(0x53)
        s.raw(*struct.pack('<H', i))
    def givemon(s, sp, lv):
        s.raw(0x79, sp & 255, sp >> 8, lv, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    def giveitem(s, item, qty):
        s.setvar(0x8000, item)
        s.setvar(0x8001, qty)
        s.raw(0x09, 0)
    def heal(s):
        s.raw(0x97, 1)
        s.raw(0x31, 0x00, 0x01)
        s.raw(0x32)
        s.raw(0x25, 0x00, 0x00)
        s.raw(0x97, 0)
    def battle(s, tid, intro, defeat):
        s.raw(0x5c, 0)
        s.raw(*struct.pack('<HH', tid, 0))
        s.ptr(intro)
        s.ptr(defeat)

def enc(s):
    o = bytearray()
    i = 0
    while i < len(s):
        if s.startswith('{P}', i):
            o += b'\xfd\x01'
            i += 3
            continue
        c = s[i]
        if c == '\n':
            o.append(0xFE)
        else:
            o.append(ENC[c])
        i += 1
    o.append(0xFF)
    return bytes(o)

def put_script(r, sb):
    r.cur = (r.cur + 3) & ~3
    base = r.cur
    code = sb.build(base)
    a = r.alloc(code, 1)
    assert a == base, (hex(a), hex(base))
    return a

def say(r, lines):
    return [0x08000000 + r.alloc(enc(t), 1) for t in lines]

def boxes(sb, ptrs):
    for i, p in enumerate(ptrs):
        sb.msg(p)
        if i != len(ptrs) - 1:
            sb.close()

def nearest(cols, rgb):
    return min(range(len(cols)), key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb, cols[i])))

def prep(path, size, bg=(96, 68, 44)):
    im = Image.open(path).convert('RGBA')
    im = im.resize(size, Image.Resampling.LANCZOS)
    base = Image.new('RGBA', size, bg + (255,))
    base.alpha_composite(im)
    return base.convert('RGB')

def tiles_of(im, cols):
    blobs = []
    w, h = im.size
    assert w % 16 == 0 and h % 16 == 0
    for my in range(h // 16):
        for mx in range(w // 16):
            chunk = []
            for ty in range(2):
                for tx in range(2):
                    b = bytearray(32)
                    for y in range(8):
                        for x in range(0, 8, 2):
                            px = mx * 16 + tx * 8 + x
                            py = my * 16 + ty * 8 + y
                            c0 = nearest(cols, im.getpixel((px, py)))
                            c1 = nearest(cols, im.getpixel((px + 1, py)))
                            b[y * 4 + x // 2] = c0 | (c1 << 4)
                    chunk.append(bytes(b))
            blobs.append(chunk)
    return blobs

def palette_of(images):
    data = []
    for im in images:
        data.extend(im.getdata())
    sheet = Image.new('RGB', (len(data), 1))
    sheet.putdata(data)
    q = sheet.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    return [tuple(pal[i * 3:i * 3 + 3]) for i in range(16)]

def u16(d, a):
    return struct.unpack_from('<H', d, a)[0]

def u32(d, a):
    return struct.unpack_from('<I', d, a)[0]

def free_trainer(d):
    for tid in range(700, 760):
        e = d[T_TABLE + 40 * tid:T_TABLE + 40 * tid + 40]
        if e[4] == 0xFF and u32(d, T_TABLE + 40 * tid + 36) in (0, 0xFFFFFFFF):
            return tid
    raise SystemExit('no free trainer slot')

def build_tiles(r):
    floor = prep(f'{TILE}/tiles/floor-wood-1.png', (16, 16))
    wall = prep(f'{TILE}/tiles/wall-wood.png', (16, 16))
    door = prep(f'{TILE}/tiles/door-wood.png', (16, 16))
    shelf = prep(f'{TILE}/props/shelf.png', (16, 16))
    crate = prep(f'{TILE}/props/crate.png', (16, 16))
    fbed = prep(f'{TILE}/props/bed-father.png', (32, 32))
    ebed = prep(f'{TILE}/props/bed-empty.png', (32, 16))
    images = [floor, wall, door, shelf, crate, fbed, ebed]
    cols = palette_of(images)
    lay = 0x2d5200
    sec_ptr = u32(r.b, lay + 20) - 0x08000000
    hdr = bytearray(r.b[sec_ptr:sec_ptr + 24])
    assert hdr[0] == 1 and hdr[1] == 1
    tiles_p = u32(r.b, sec_ptr + 4) - 0x08000000
    pals_p = u32(r.b, sec_ptr + 8) - 0x08000000
    mt_p = u32(r.b, sec_ptr + 12) - 0x08000000
    at_p = u32(r.b, sec_ptr + 20) - 0x08000000
    old_tiles = gfx.lz_decomp(r.b, tiles_p) if r.b[tiles_p] == 0x10 else bytes(r.b[tiles_p:tiles_p + 63 * 32])
    assert len(old_tiles) >= 63 * 32
    old_tiles = old_tiles[:63 * 32]
    chunks = []
    for im in (floor, wall, door, shelf, crate):
        chunks += tiles_of(im, cols)
    chunks += tiles_of(fbed, cols)
    chunks += tiles_of(ebed, cols)
    # chunks: 0 floor, 1 wall, 2 door, 3 shelf, 4 crate, 5-8 father bed, 9-10 empty bed
    raw = bytearray(old_tiles)
    ids = []
    base_tile = 640 + 63
    n = 0
    for ch in chunks:
        four = []
        for blob in ch:
            raw += blob
            four.append(base_tile + n)
            n += 1
        ids.append(four)
    pals = bytearray(r.b[pals_p:pals_p + 16 * 32])
    pals[PAL * 32:(PAL + 1) * 32] = gfx.rgb_to_pal(cols)
    old_mt = bytes(r.b[mt_p:mt_p + 24 * 16])
    old_at = bytes(r.b[at_p:at_p + 24 * 4])
    extra_mt = bytearray()
    for four in ids:
        ents = [((PAL << 12) | t) for t in four] + [0, 0, 0, 0]
        extra_mt += struct.pack('<8H', *ents)
    extra_at = b'\x00' * (4 * len(ids))
    ta = r.alloc(bytes(raw), 4)
    pa = r.alloc(bytes(pals), 4)
    ma = r.alloc(old_mt + bytes(extra_mt), 4)
    aa = r.alloc(old_at + extra_at, 4)
    nh = bytearray(hdr)
    nh[0] = 0
    nh[4:8] = struct.pack('<I', 0x08000000 + ta)
    nh[8:12] = struct.pack('<I', 0x08000000 + pa)
    nh[12:16] = struct.pack('<I', 0x08000000 + ma)
    nh[20:24] = struct.pack('<I', 0x08000000 + aa)
    ns = r.alloc(bytes(nh), 4)
    r.w32(lay + 20, 0x08000000 + ns)
    first = 640 + 24
    names = ['floor', 'wall', 'door', 'shelf', 'crate', 'f0', 'f1', 'f2', 'f3', 'e0', 'e1']
    mid = {names[i]: first + i for i in range(len(names))}
    return mid

def paint_house(r, mid):
    lay = 0x2d5200
    w, h = u32(r.b, lay), u32(r.b, lay + 4)
    mp = u32(r.b, lay + 12) - 0x08000000
    assert (w, h) == (13, 10)

    def get(x, y):
        return u16(r.b, mp + 2 * (y * w + x))

    def put(x, y, v):
        r.b[mp + 2 * (y * w + x):mp + 2 * (y * w + x) + 2] = struct.pack('<H', v)

    for y in range(h):
        for x in range(w):
            v = get(x, y)
            tid = v & 0x3FF
            if tid in KEEP:
                continue
            # keep the room's shape: solid tiles stay solid wood, open tiles become floor
            solid = (v & 0x0C00) != 0 or x == 0 or y == 0 or x == w - 1 or y == h - 1
            if solid:
                put(x, y, (v & 0xF000) | 0x0400 | mid['wall'])
            else:
                put(x, y, 0x3000 | mid['floor'])
    # father bed 2x2, empty bed, shelf, crate. Door approach stays floor.
    quads = [('f0', 2, 3), ('f1', 3, 3), ('f2', 2, 4), ('f3', 3, 4)]
    for name, x, y in quads:
        put(x, y, 0x0400 | mid[name])
    put(2, 6, 0x0400 | mid['e0'])
    put(3, 6, 0x0400 | mid['e1'])
    put(8, 3, 0x0400 | mid['shelf'])
    put(10, 5, 0x0400 | mid['crate'])

def obj_bytes(local, gfx, x, y, script, flag=0, move=0):
    t = bytearray(24)
    t[0] = local
    t[1] = gfx
    t[4:8] = struct.pack('<hh', x, y)
    t[8] = 3
    t[9] = move
    t[16:20] = struct.pack('<I', script)
    t[20:22] = struct.pack('<H', flag)
    return bytes(t)

def main():
    r = Rom(SRC)
    if MARKER in r.b:
        print('already patched')
        return
    r.alloc(MARKER, 4)
    d = r.b
    # ---- names: MAX is the first choice for both genders
    MAX = 0x081C57B4
    male = [u32(d, 0x46308c + 4 * i) for i in range(19)]
    if male[0] != MAX:
        male = [MAX] + [p for p in male if p != MAX]
        assert len(male) == 19
        for i, p in enumerate(male):
            r.w32(0x46308c + 4 * i, p)
    female = [u32(d, 0x4630d8 + 4 * i) for i in range(19)]
    if female[0] != MAX:
        female = [MAX] + [p for p in female if p != MAX]
        female = female[:19]
        assert len(female) == 19
        for i, p in enumerate(female):
            r.w32(0x4630d8 + 4 * i, p)
    # ---- house art
    mid = build_tiles(r)
    paint_house(r, mid)
    # ---- strings
    father = say(r, [
        "The army is at our gates, father.",
        "They burn what they don't steal.\nPALLET TOWN is bleeding.",
        "You're too sick to fight them.\nI know that.",
        "So I'm taking your POKéMON.",
        "It sleeps in the ball until\nsomeone opens it.",
        "Father does not wake.\nThe POKé BALL is still on the shelf.",
    ])
    father_after = say(r, [
        "I already took SANDSHREW.\nSleep. I'll do the fighting.",
        "His breath is thin.\nHe does not answer.",
    ])
    bed = say(r, [
        "Just until they breathe again.",
        "The bed is empty. The POKéMON\nsleep. Cuts close.",
    ])
    shelf = say(r, [
        "This is it. Father's ball.\nSANDSHREW is inside.",
        "{P} closes a hand around the ball.",
        "You're coming.\nPALLET TOWN doesn't get to fall.",
    ])
    shelf_empty = say(r, ["Dust. The ball is already open."])
    shelf_full = say(r, ["There's no room for another\nPOKéMON."])
    crate = say(r, [
        "A wrap. He won't miss it.",
        "A POTION under the lid.",
    ])
    crate_empty = say(r, ["Splinters and a moth. Empty."])
    door = say(r, ["Not yet. Father's POKéMON\nis still on the shelf."])
    tv = say(r, ["Dust on the screen.\nNobody has turned it on."])
    oak = say(r, ["OAK: I was robbed.\nThe balls on that table are empty.\nThey took every POKéMON I had."])
    mason_intro = say(r, [
        "MASON: {P}. Stop right there.",
        "{P}: Mason.",
        "MASON: You walked out with your\nfather's hound and a ball.",
        "MASON: Where are you going?",
        "{P}: Out of town.",
        "MASON: You're eight.\nYou cannot win this.",
        "MASON: Then your POKéMON faints\nhere, and you go back inside.",
    ])
    # battle text needs a trailing space so the last letter is not dropped
    mb_in = 0x08000000 + r.alloc(enc("MASON: Stop. We're fighting. ")[:-1] + b' \xff', 1)
    mb_de = 0x08000000 + r.alloc(enc("MASON: ...Fine. You win. ")[:-1] + b' \xff', 1)
    mason_after = say(r, [
        "MASON: Go, then.\nThe road is still guarded.",
        "{P}: I didn't ask for your blessing.",
    ])
    anne = say(r, [
        "ANNE: {P}. You actually fought.",
        "ANNE: Take these. Five POKé BALLS.\nDon't waste them on the first moth.",
        "{P}: I won't.",
    ])
    up = 0x08000000 + r.alloc(bytes([0x11, 0xFE]), 1)
    left = 0x08000000 + r.alloc(bytes([0x12, 0xFE]), 1)
    # ---- father (was Mom)
    S = SB()
    S.lock()
    S.face()
    S.chkflag(F_TOOK)
    S.goto_if(1, 'after')
    boxes(S, father)
    S.release()
    S.end()
    S.lab('after')
    boxes(S, father_after)
    S.release()
    S.end()
    father_scr = 0x08000000 + put_script(r, S)
    # Mom's script stays in the ROM. She is hidden: the father is drawn in the bed.
    ho = 0x3b9708
    d[ho + 20:ho + 22] = struct.pack('<H', HIDE_MOM)
    HS = SB()
    HS.setflag(HIDE_MOM)
    HS.end()
    hlist = bytes([3]) + struct.pack('<I', 0x08000000 + put_script(r, HS)) + b'\x00'
    r.w32(0x350d58, 0x08000000 + r.alloc(hlist, 1))
    # ---- bed, shelf, crate, dark TV, door lock
    def sign_script(lines, after=None, flag=None, empty=None, item=None, mon=None):
        S = SB()
        S.lock()
        if flag is not None:
            S.chkflag(flag)
            S.goto_if(1, 'empty')
        boxes(S, lines)
        S.close()
        if mon is not None:
            S.givemon(mon, 3)
            S.cmp(0x800D, 2)
            S.goto_if(1, 'full')
            S.setflag(flag)
            S.setvar(VAR_CRY, 1)
        if item is not None:
            S.giveitem(item, 1)
            S.setflag(flag)
        if after:
            S.heal()
        S.release()
        S.end()
        if flag is not None:
            S.lab('empty')
            boxes(S, empty)
            S.release()
            S.end()
        if mon is not None:
            S.lab('full')
            boxes(S, shelf_full)
            S.release()
            S.end()
        return 0x08000000 + put_script(r, S)
    bed_scr = sign_script(bed, after=True)
    shelf_scr = sign_script(shelf, flag=F_TOOK, empty=shelf_empty, mon=SANDSHREW)
    crate_scr = sign_script(crate, flag=F_CRATE, empty=crate_empty, item=POTION)
    tv_scr = sign_script(tv)
    D = SB()
    D.lockall()
    D.cmp(VAR_OAK_SCENE, 0)
    D.goto_if(1, 'fresh')
    # a save that already left Pallet is not locked in the cottage
    D.setvar(VAR_CRY, 2)
    D.releaseall()
    D.end()
    D.lab('fresh')
    D.chkflag(F_TOOK)
    D.goto_if(1, 'open')
    boxes(D, door)
    D.move(0xFF, up)
    D.waitmove(0)
    D.releaseall()
    D.end()
    D.lab('open')
    D.setvar(VAR_CRY, 1)
    D.releaseall()
    D.end()
    door_scr = 0x08000000 + put_script(r, D)
    # house bg events: old TV sign replaced, plus bed, shelf, crate
    hev = 0x3b974c
    bgs = []
    def bg(x, y, scr):
        return struct.pack('<HHBBHI', x, y, 0, 0, 0, scr)
    bgs.append(bg(6, 1, tv_scr))
    bgs.append(bg(2, 4, father_scr))
    bgs.append(bg(3, 4, father_scr))
    bgs.append(bg(2, 3, father_scr))
    bgs.append(bg(3, 3, father_scr))
    bgs.append(bg(2, 6, bed_scr))
    bgs.append(bg(3, 6, bed_scr))
    bgs.append(bg(8, 3, shelf_scr))
    bgs.append(bg(10, 5, crate_scr))
    ba = r.alloc(b''.join(bgs), 4)
    d[hev + 3] = len(bgs)
    r.w32(hev + 16, 0x08000000 + ba)
    coords = b''
    for x, y in ((4, 7), (5, 7)):
        coords += struct.pack('<hhBBHHHI', x, y, 3, 0, VAR_CRY, 0, 0, door_scr)
    ca = r.alloc(coords, 4)
    d[hev + 2] = 2
    r.w32(hev + 12, 0x08000000 + ca)
    # ---- Oak robbed, balls stay hidden, Oak is visible
    r.w32(0x1695f8, oak[0])
    W = SB()
    W.clearflag(FLAG_HIDE_OAK)
    for f in FLAG_BALLS:
        W.setflag(f)
    W.raw(0x05)
    W.ptr(0x08168F8E)
    lab_wrap = 0x08000000 + put_script(r, W)
    r.w32(0x168f7f, lab_wrap)
    # ---- Pallet: hide the ultra-ball man, drop the exit block, add Mason and Anne
    tid = free_trainer(d)
    e = bytearray(d[T_TABLE + 40 * 326:T_TABLE + 40 * 327])
    e[0] = 0
    e[1] = T_CLASS
    e[2] = 0
    e[3] = T_PIC
    name = enc('MASON')[:-1]
    e[4:16] = name + b'\xff' * (12 - len(name))
    e[16:28] = bytes(12)
    e[32] = 1
    party = struct.pack('<HBBHH', 255, 3, 0, PIKACHU, 0)
    e[36:40] = struct.pack('<I', 0x08000000 + r.alloc(party, 4))
    d[T_TABLE + 40 * tid:T_TABLE + 40 * tid + 40] = e
    pev = 0x71d990
    no = d[pev]
    po = u32(d, pev + 4) - 0x08000000
    objs = bytearray(d[po:po + 24 * no])
    for i in range(no):
        if objs[24 * i] == 2:
            objs[24 * i + 20:24 * i + 22] = struct.pack('<H', HIDE_ULTRA)
            d[0x16582f] = 0x02          # his script is now just end
    ids = [objs[24 * i] for i in range(no)]
    mason_id = max(ids) + 1
    anne_id = mason_id + 1
    # scripts need the local ids, so build them now
    M = SB()
    M.lockall()
    M.chkflag(F_MASON)
    M.goto_if(1, 'skip')
    M.clearflag(HIDE_MASON)
    M.addobj(mason_id)
    M.move(mason_id, up)
    M.waitmove(0)
    boxes(M, mason_intro)
    M.close()
    M.battle(tid, mb_in, mb_de)
    boxes(M, mason_after)
    M.close()
    M.setflag(F_MASON)
    M.remobj(mason_id)
    M.clearflag(HIDE_ANNE)
    M.addobj(anne_id)
    M.move(anne_id, left)
    M.waitmove(0)
    boxes(M, anne)
    M.giveitem(POKEBALL, 5)
    M.setflag(F_ANNE)
    M.setvar(VAR_CRY, 2)
    M.releaseall()
    M.end()
    M.lab('skip')
    M.setvar(VAR_CRY, 2)
    M.releaseall()
    M.end()
    mason_scr = 0x08000000 + put_script(r, M)
    anne_talk = SB()
    anne_talk.lock()
    anne_talk.face()
    boxes(anne_talk, anne[-1:])
    anne_talk.release()
    anne_talk.end()
    anne_scr = 0x08000000 + put_script(r, anne_talk)
    # (6,10) and (6,9) are open ground south of the door. Anne stands clear of that path.
    objs += obj_bytes(mason_id, GFX_BLUE, 6, 10, mason_scr, HIDE_MASON, 0)
    objs += obj_bytes(anne_id, GFX_LASS, 9, 8, anne_scr, HIDE_ANNE, 0)
    oa = r.alloc(bytes(objs), 4)
    d[pev] = no + 2
    r.w32(pev + 4, 0x08000000 + oa)
    spots = [(5, 8), (6, 8), (7, 8)]
    pc = b''
    for x, y in spots:
        pc += struct.pack('<hhBBHHHI', x, y, 3, 0, VAR_CRY, 1, 0, mason_scr)
    pca = r.alloc(pc, 4)
    d[pev + 2] = len(spots)
    r.w32(pev + 12, 0x08000000 + pca)
    # every Pallet load hides Mason, Anne, and the ultra-ball man
    H = SB()
    H.setflag(HIDE_MASON)
    H.setflag(HIDE_ANNE)
    H.setflag(HIDE_ULTRA)
    H.raw(0x05)
    H.ptr(0x08165465)
    hide_scr = 0x08000000 + put_script(r, H)
    r.w32(0x16545b, hide_scr)
    out = SRC
    r.save(out)
    print('trainer', tid, 'mason', mason_id, 'anne', anne_id, 'end', hex(r.cur))

if __name__ == '__main__':
    main()
