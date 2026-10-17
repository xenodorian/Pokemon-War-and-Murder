# CryMon cottage opening, ported onto the War and Murder ROM.
# usage: cry_open.py IN.gba OUT.gba
# No naming screens: the player is LEAF and the rival is MASON. New games start in the player's house (the Slums are gone).
# Player's house 1F uses the CryMon wood tiles (tools/cry_house_tiles.json, baked from the CryMon sprites).
# Father, empty bed, shelf (Sandshrew) and crate (Potion) replace Mom's scene.
# Oak has no starters and says he was robbed. The ultra-ball man and the
# Pallet exit block are gone. Mason (Gary's sprite) battles on the way out.
# Anne (little girl sprite) gives six Poke Balls and a Potion after that fight.
# Quillpup -> Sandshrew, Glimmoth -> Pikachu, linen wrap -> Potion,
# capture crystals -> Poke Balls.
import sys, struct
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, '/home/claude/work/tools')
from inc import Rom
from g3 import ENC
import gfx

MARKER = b'CRYOPEN2'

# 0x4EF..0x4F6 are unused vanilla flags (0x4D0..0x4EE belong to the spirit quests)
F_TOOK, F_CRATE, F_MASON, F_ANNE = 0x4EF, 0x4F0, 0x4F1, 0x4F2
HIDE_MASON, HIDE_ANNE, HIDE_ULTRA, HIDE_MOM = 0x4F3, 0x4F4, 0x4F5, 0x4F6
# 0x406D is an unused map-scene slot. 0x40F7 is the police kill counter.
VAR_CRY = 0x406D
VAR_OAK_SCENE = 0x4050
FLAG_HIDE_OAK = 0x02B
FLAG_BALLS = (0x028, 0x029, 0x02A)
SANDSHREW, PIKACHU = 27, 25
POTION, POKEBALL = 13, 4
GFX_BLUE, GFX_LASS, GFX_LAYING = 72, 22, 34
GFX_LITTLE_GIRL = 17          # pret OBJ_EVENT_GFX_LITTLE_GIRL: Anne is a child
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
    def battle(s, tid, intro, defeat, cont):
        # type 2 (TRAINER_BATTLE_CONTINUE_SCRIPT): after the battle the script goes on at `cont`. Type 0 ends the script when the battle ends.
        s.raw(0x5c, 2)
        s.raw(*struct.pack('<HH', tid, 0))
        s.ptr(intro)
        s.ptr(defeat)
        s.ref(cont)
        s.lab(cont)

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

def u16(d, a):
    return struct.unpack_from('<H', d, a)[0]

def u32(d, a):
    return struct.unpack_from('<I', d, a)[0]


# ---------------------------------------------------------------------------------------------- no naming screens
# The hack's new game goes title -> naming screen (task state 0x1303b4 calls DoNamingScreen) -> "Are you sure?" confirmation -> start.
# Both DoNamingScreen calls in that task state are redirected to a stub that writes the names into the save and returns straight to the screen's own return
# callback, as if the name had been typed: LEAF for the player, MASON for the rival (the rival is never asked in this hack, so it is set here too).
# LEAF is female (docs/SPEC_ARREST_AND_PARTY.md): the stub also writes playerGender = 1 (SaveBlock2 + 8), so the overworld avatar is FireRed's vanilla Leaf, not Red.
# The confirmation's Yes/No handler (0x130554) answers Yes by itself.
SB2_PTR, SB1_PTR = 0x0300500C, 0x03005008
NAMING_TASK, NAMING_TASK_END, DO_NAMING, SET_MAIN_CB2 = 0x1303B4, 0x130464, 0x0809D954, 0x08000545
DESTROY_TASK = 0x08077509      # r6 holds the naming task's id in that state and the stub leaves r6 alone
YESNO_CALL = 0x13055C
RIVAL_NAME_OFF = 0x3A4C
RIVAL_PRESETS = 0x463124      # table of 4 name pointers read by 0x131754 for the rival
GMAIN_STATE = 0x030030F0 + 0x438      # gMain.state: the return callback is a state machine that starts at 0
STUB_AT = 0x3B4D84

def skip_naming(r):
    d = r.b
    sites = []
    for o in range(NAMING_TASK, NAMING_TASK_END, 2):
        hi, lo = u16(d, o), u16(d, o + 2)
        if hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800:
            off = (((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1))
            off = off - (1 << 23) if off & (1 << 22) else off
            if 0x08000000 + o + 4 + off == DO_NAMING: sites.append(o)
    assert len(sites) == 2, [hex(x) for x in sites]
    assert u16(d, YESNO_CALL) & 0xF800 == 0xF000 and u16(d, YESNO_CALL + 2) & 0xF800 == 0xF800, 'Yes/No call not where expected'
    mx = enc('LEAF')[:-1] + b'\xff' * 4
    ms = enc('MASON')[:-1] + b'\xff' * 3
    pm = 0x08000000 + r.alloc(mx + ms, 4)
    stub_src = f"""
        push {{r4, lr}}
        ldr r4, [sp, #12]
        cmp r0, #0
        bne rival
        ldr r2, =0x{pm:x}
        ldr r3, [r2]
        str r3, [r1]
        ldr r3, [r2, #4]
        str r3, [r1, #4]
        movs r3, #1
        strb r3, [r1, #8]
        ldr r1, =0x{SB1_PTR:x}
        ldr r1, [r1]
        ldr r0, =0x{RIVAL_NAME_OFF:x}
        adds r1, r1, r0
        adds r2, r2, #8
        b copy
      rival:
        ldr r2, =0x{pm + 8:x}
      copy:
        ldr r3, [r2]
        str r3, [r1]
        ldr r3, [r2, #4]
        str r3, [r1, #4]
        ldr r0, =0x{GMAIN_STATE:x}
        movs r1, #0
        strb r1, [r0]
        adds r0, r4, #0
        ldr r3, =0x{SET_MAIN_CB2:x}
        bl callr3
        adds r0, r6, #0
        ldr r3, =0x{DESTROY_TASK:x}
        bl callr3
        pop {{r4}}
        pop {{r0}}
        bx r0
      callr3:
        bx r3
    """
    code = r.asm(stub_src, STUB_AT)       # BL reaches +-4 MB: the stub sits in a free run near the speech code
    r.put(STUB_AT, code)
    for o in sites: r.bl(o, STUB_AT)
    # after the confirmation the speech copies rival preset 0 into the save (SetDefaultName stage 1): that preset is MASON
    r.w32(RIVAL_PRESETS, pm + 8)
    d[YESNO_CALL:YESNO_CALL + 4] = bytes([0x00, 0x20, 0xC0, 0x46])      # movs r0,#0 ; nop  (always Yes)

# ---------------------------------------------------------------------------------------------- new game starts at home
NEWGAME_WARP = 0x54A00        # movs r0,#6 (y); .. movs r0,#1; movs r1,#0x58; movs r3,#6 (x)
START_X, START_Y = 4, 5
def start_at_home(r):
    d = r.b
    assert bytes(d[0x54A00:0x54A0A]) == bytes([0x06, 0x20, 0x00, 0x90, 0x01, 0x20, 0x58, 0x21, 0x06, 0x23]), bytes(d[0x54A00:0x54A0A]).hex()
    d[0x54A00:0x54A0A] = bytes([START_Y, 0x20, 0x00, 0x90, 0x04, 0x20, 0x00, 0x21, START_X, 0x23])      # map (4,0): the player's house 1F

# ---------------------------------------------------------------------------------------------- the Slums are removed
def remove_slums(r):
    """Pallet's rock hut led down to the Slums (map 1,88). Its warp (id 3, other warps keep their ids) is parked off the walkable map and the hut becomes dark lawn."""
    d = r.b
    pev = 0x71d990
    wo = u32(d, pev + 8) - 0x08000000 + 8 * 3
    assert struct.unpack('<hhBBBB', d[wo:wo + 8]) == (4, 17, 0, 0, 88, 1), 'slums warp not where expected'
    d[wo:wo + 4] = struct.pack('<hh', 0, 0)
    gp = u32(d, 0x3526A8 + 12) - 0x08000000
    lay = u32(d, u32(d, gp) - 0x08000000) - 0x08000000
    w = u32(d, lay)
    mp = u32(d, lay + 12) - 0x08000000
    cell = lambda x, y: mp + 2 * (y * w + x)
    assert [u16(d, cell(x, 16)) & 0x3ff for x in (3, 4, 5)] == [104, 105, 106] and [u16(d, cell(x, 17)) & 0x3ff for x in (3, 4, 5)] == [120, 169, 122], 'hut not where expected'
    bits = u16(d, cell(2, 16)) & 0xfc00
    assert bits >> 10 == 0x0c, hex(bits)         # open ground, elevation 3
    for x in (3, 4, 5):
        for y in (16, 17):
            d[cell(x, y):cell(x, y) + 2] = struct.pack('<H', bits | ([8, 9] if y % 2 == 0 else [16, 17])[x % 2])


# ---------------------------------------------------------------------------------------------- quest log text
def update_quest_text(r):
    """the FIRST POKéMON quest log entry exists four times in the ROM (the quest table is copied); every copy is rewritten in place"""
    d = r.b
    head = enc('QUEST: FIRST POKéMON')[:-1] + b'\xfb'
    pages = ["QUEST: FIRST POKéMON", "GO TO: PALLET TOWN, then PROF.\nOAK's LAB.", "TO DO: Take your father's\nPOKéMON from the shelf at home.", "Then leave and go to OAK's LAB\nin the north of PALLET TOWN."]
    body = b'\xfb'.join(enc(p)[:-1] for p in pages)
    n = 0
    i = 0
    while True:
        i = bytes(d).find(head, i)
        if i < 0: break
        j = i
        while d[j] != 0xFF: j += 1
        old = bytes(d[i:j])
        assert enc('Leave the SLUMS')[:-1] in old and len(body) <= len(old), (hex(i), len(body), len(old))
        d[i:j + 1] = body + bytes([0x00]) * (len(old) - len(body)) + b'\xff'
        n += 1
        i = j + 1
    assert n == 4, n
    return n

# ---------------------------------------------------------------------------------------------- the rival is MASON everywhere
def rename_rival(r):
    """every trainer entry named TERRY (the rival's fights) is named MASON, same length"""
    d = r.b
    old, new = enc('TERRY')[:-1], enc('MASON')[:-1]
    n = 0
    for tid in range(0, 900):
        o = T_TABLE + 40 * tid + 4
        if bytes(d[o:o + 5]) == old and d[o + 5] == 0xFF:
            d[o:o + 5] = new
            n += 1
    assert n >= 10, n
    return n

def free_trainer(d):
    for tid in range(700, 760):
        e = d[T_TABLE + 40 * tid:T_TABLE + 40 * tid + 40]
        if e[4] == 0xFF and u32(d, T_TABLE + 40 * tid + 36) in (0, 0xFFFFFFFF):
            return tid
    raise SystemExit('no free trainer slot')

def build_tiles(r):
    """secondary tileset of the player's house 1F with the CryMon wood floor, wall, door, shelf, crate and beds appended (baked)"""
    j = json.load(open(os.path.join(HERE, 'cry_house_tiles.json')))
    lay = 0x2d5200
    sec_ptr = u32(r.b, lay + 20) - 0x08000000
    assert r.b[sec_ptr] == 1 and r.b[sec_ptr + 1] == 1, 'house tileset already replaced'
    hdr = bytearray(bytes.fromhex(j['hdr']))
    ta = r.alloc(bytes.fromhex(j['tiles']), 4)
    pa = r.alloc(bytes.fromhex(j['pals']), 4)
    ma = r.alloc(bytes.fromhex(j['meta']), 4)
    aa = r.alloc(bytes.fromhex(j['attr']), 4)
    hdr[4:8] = struct.pack('<I', 0x08000000 + ta)
    hdr[8:12] = struct.pack('<I', 0x08000000 + pa)
    hdr[12:16] = struct.pack('<I', 0x08000000 + ma)
    hdr[20:24] = struct.pack('<I', 0x08000000 + aa)
    ns = r.alloc(bytes(hdr), 4)
    r.w32(lay + 20, 0x08000000 + ns)
    first = 640 + 24
    names = ['floor', 'wall', 'door', 'shelf', 'crate', 'f0', 'f1', 'f2', 'f3', 'e0', 'e1']
    return {names[i]: first + i for i in range(len(names))}

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
    SRC, OUT = sys.argv[1], sys.argv[2]
    r = Rom(SRC)
    if MARKER in r.b:
        print('already patched')
        return
    r.alloc(MARKER, 4)
    d = r.b
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
    # CryMon masonFight lines (content/dialogue.json talk.masonFight), CryMon -> POKéMON and crystal -> ball
    mason_intro = say(r, [
        "MASON: {P}. Stop right there.",
        "{P}: Mason.",
        "MASON: You walked out with your\nfather's hound and a ball.",
        "MASON: Where are you going?",
        "{P}: To the Prison.",
        "MASON: This place is a prison.\nNobody walks out of the Prison.",
        "{P}: Shinigami is chained there.\nLocked up for necromancy.",
        "{P}: I'm going to free him.\nHe owes me power for it.",
        "MASON: You're eight.\nYou cannot win this war.",
        "MASON: And you cannot bargain\nwith a necromancer.",
        "{P}: I'm not asking.",
        "MASON: Then your POKéMON faints\nhere, and you go back inside.",
    ])
    # battle text needs a trailing space so the last letter is not dropped
    mb_in = 0x08000000 + r.alloc(enc("MASON: Stop. We're fighting. ")[:-1] + b' \xff', 1)
    mb_de = 0x08000000 + r.alloc(enc("MASON: ...Fine. You win. ")[:-1] + b' \xff', 1)
    # CryMon masonAfter, then masonWin (the battle ends the same way for a win or a loss here)
    mason_after = say(r, [
        "MASON: Fine. Calder is still\nout there.",
        "{P}: I won't die first.",
        "Mason spits in the dirt.\nHis POKéMON won't rise.",
        "MASON: Go, then. But the Weeping\nArmy guards the road.",
        "MASON: And the Prison\nguards itself.",
        "{P}: I didn't ask for your\nblessing.",
        "MASON: You didn't need it.\nYou took it anyway.",
    ])
    anne = say(r, [
        "ANNE: {P}. You actually fought.",
        "ANNE: Take these. Six POKé BALLS.\nDon't waste them on the first moth.",
        "ANNE: And take this POTION too.",
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
            S.raw(0x23); S.ptr(0x083b24b1)      # story_native leaf_join (trampoline in padding): LEAF becomes a party member
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
    D.chkflag(0x84B)          # F_MODEASKED (story_ids): the run mode is chosen once, here, before LEAF leaves the house
    D.goto_if(1, 'go')
    D.msg(0x08000000 + r.alloc(enc("Before you go, LEAF.\nHow will you fight this war?"), 1), 4)
    D.msg(0x08000000 + r.alloc(enc("Play as a POKéMON?\nA lost battle means death."), 1), 5)
    D.setflag(0x84B)
    D.cmp(0x800D, 1)
    D.goto_if(1, 'play')
    D.msg(0x08000000 + r.alloc(enc("A normal run. If you lose,\nyou wake in a POKéMON CENTER."), 1), 4)
    D.goto('go')
    D.lab('play')
    D.setflag(0x84A)          # F_PLAYABLE
    D.msg(0x08000000 + r.alloc(enc("A playable run. If you lose,\nyou die. ARCEUS or GIRATINA decides."), 1), 4)
    D.lab('go')
    D.setvar(VAR_CRY, 1)
    D.releaseall()
    D.end()
    door_scr = 0x08000000 + put_script(r, D)
    if os.environ.get('TEST_BATTLE'):   # TEST ONLY: stepping onto the door tile starts a wild Pidgey battle (lv 5); never set for a release build
        foe = [int(x) for x in os.environ.get('TEST_FOE', '16,5').split(',')]
        tb = SB()
        for g in os.environ.get('TEST_GIVE_MORE', '').split(';'):   # TEST ONLY: TEST_GIVE_MORE=species,level;species,level adds more mons
            if g:
                gs, gl = [int(x) for x in g.split(',')]
                tb.raw(0x79, gs & 255, gs >> 8, gl, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        if os.environ.get('TEST_MASTER'):   # TEST ONLY: five MASTER BALLs
            tb.raw(0x44, 1, 0, 5, 0)
        if os.environ.get('TEST_GIVE'):   # TEST ONLY: TEST_GIVE=species,level adds that mon first (so the stand-in is not used)
            gs, gl = [int(x) for x in os.environ['TEST_GIVE'].split(',')]
            tb.raw(0x79, gs & 255, gs >> 8, gl, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        if os.environ.get('TEST_LEAF'):   # TEST ONLY: LEAF joins the party as the shelf script does
            tb.raw(0x23); tb.ptr(0x083b24b1)
        if os.environ.get('TEST_WARP'):   # TEST ONLY: TEST_WARP=group,num,x,y warps there instead of starting a battle
            wg, wn, wx, wy = [int(x) for x in os.environ['TEST_WARP'].split(',')]
            tb.releaseall(); tb.raw(0x39, wg, wn, 0xff, wx & 255, wx >> 8, wy & 255, wy >> 8); tb.raw(0x27); tb.end()
        elif os.environ.get('TEST_TRAINER'):   # TEST ONLY: TEST_TRAINER=id starts that trainer battle (mode 0) instead of the wild one
            tt = 0x08000000 + r.alloc(enc("TEST ")[:-1] + b' \xff', 1)
            tb.raw(0x5c, 0, int(os.environ['TEST_TRAINER']) & 255, int(os.environ['TEST_TRAINER']) >> 8, 0, 0); tb.ptr(tt); tb.ptr(tt); tb.releaseall(); tb.end()
        else:
            tb.raw(0xb6, foe[0] & 255, foe[0] >> 8, foe[1], 0, 0); tb.raw(0xb7); tb.end()
        door_scr = 0x08000000 + put_script(r, tb)
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
    M.battle(tid, mb_in, mb_de, 'post')
    boxes(M, mason_after)
    M.close()
    M.setflag(F_MASON)
    M.remobj(mason_id)
    M.clearflag(HIDE_ANNE)
    M.addobj(anne_id)
    M.move(anne_id, left)
    M.waitmove(0)
    boxes(M, anne)
    M.giveitem(POKEBALL, 6)
    M.giveitem(POTION, 1)
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
    objs += obj_bytes(anne_id, GFX_LITTLE_GIRL, 9, 8, anne_scr, HIDE_ANNE, 0)
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
    update_quest_text(r)
    rename_rival(r)
    skip_naming(r)
    start_at_home(r)
    remove_slums(r)
    r.save(OUT)
    print('trainer', tid, 'mason', mason_id, 'anne', anne_id, 'end', hex(r.cur))

if __name__ == '__main__':
    main()
