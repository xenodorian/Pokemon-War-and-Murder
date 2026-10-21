# Late fixes on a built ROM (usage: field_fixes.py IN.gba OUT.gba).
# Church: the grass north of the steeple is solid, and the door is a real door warp instead of a teleport pad.
# Start menu: POKeMON is always listed. Trainer class 81 (past the name table) is named RIVAL so the battle intro does not run off into garbage.
# If this ROM still has the old opening and the old white-out (the center machine inside the player's house), those are patched here too.
# A ROM rebuilt by apply_all after the source fixes already has the opening and the white-out; the checks below leave those alone.
import os, struct, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inc import Rom
from cry_open import SB, put_script, enc, say, u16, u32, loading_cover
from g3 import dec

GROUPS = 0x3526A8
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'story')
WORK = '/tmp/field_fix_build'
OLD_AFTER = 0x08F62F15
PROMPT = 0x08F62B60
MAX_REMOVE = 0x08F62CEC
CENTER_SCRIPT = 0x081A8D97
SETUP_SCRIPT = 0x08069AE4
SET_CB = 0x08000544
CB_CONT = 0x080568C5
GETMON = 0x0803FBE8
KARMA = 0x08EBAE98
SAVEDCB = 0x030030F8
VAR_YV = 0x40EF
VAR_CRY = 0x406D

LEAF_DOWN = r'''
push {r4, r5, r6, r7, lr}
ldr r4, =0x02024029
ldrb r4, [r4]
movs r5, #0
ldr r6, =0x020370C6
movs r0, #0
strh r0, [r6]
lp:
cmp r5, r4
bge dn
movs r0, #100
muls r0, r5
ldr r1, =0x02024284
adds r7, r0, r1
movs r0, r7
movs r1, #11
movs r2, #0
bl getmon
cmp r0, #255
bne nx
movs r0, r7
movs r1, #1
movs r2, #0
bl getmon
ldr r1, =0x53544E44
cmp r0, r1
beq nx
movs r0, r7
movs r1, #0x39
movs r2, #0
bl getmon
cmp r0, #0
bne nx
movs r0, #1
strh r0, [r6]
dn:
pop {r4, r5, r6, r7}
pop {r0}
bx r0
nx:
adds r5, #1
b lp
getmon:
ldr r3, =0x%08x
bx r3
.ltorg
''' % (GETMON + 1)

HEAL_KIND = r'''
ldr r0, =0x03005008
ldr r0, [r0]
ldrb r1, [r0, #0x1c]
ldrb r2, [r0, #0x1d]
ldr r0, =0x020370C6
movs r3, #1
cmp r1, #4
bne st
cmp r2, #0
bne st
movs r3, #0
st:
strh r3, [r0]
bx lr
.ltorg
'''

def after_pool(d):
    """The word max_prepare overwrites the battle-end callback with. Returns (file offset, current thumb address)."""
    i = bytes(d).find(b'STORYFN1')
    assert i > 0, 'story natives missing'
    mp = struct.unpack_from('<I', d, i + 16)[0] & ~1
    base = mp - 0x08000000
    window = d[base:base + 0x200]
    for k in range(len(window) - 8):
        if not (window[k] == 0x01 and window[k + 1] == 0x21 and window[k + 3] == 0x48
                and window[k + 4] == 0x08 and window[k + 5] == 0x43 and window[k + 7] == 0x49):
            continue
        pc = (mp + (k + 2) + 4) & ~3
        pool = pc + window[k + 2] * 4 - 0x08000000
        val = struct.unpack_from('<I', d, pool)[0]
        pc2 = (mp + (k + 6) + 4) & ~3
        pool2 = pc2 + window[k + 6] * 4 - 0x08000000
        if struct.unpack_from('<I', d, pool2)[0] == SAVEDCB and 0x08000000 <= (val & ~1) < 0x0A000000:
            return pool, val
    raise SystemExit('max_after pool not found')

def wrap_after(old, leaf, death):
    """Call the ROM's own battle-end callback, except a fainted permanent LEAF is death.
    Mason still carries her home. Yveltal's bloody ending (VAR_YV == 4) is left to the white-out script."""
    return r'''
push {r4, lr}
ldr r0, =0x02023E8A
ldrb r0, [r0]
cmp r0, #2
beq m1
cmp r0, #3
bne nomason
m1:
ldr r0, =0x02022B4C
ldr r0, [r0]
movs r1, #8
ands r0, r1
beq nomason
ldr r0, =0x020386AE
ldrh r0, [r0]
bl ismason
cmp r0, #0
bne old
nomason:
ldr r0, =0x03005008
ldr r0, [r0]
ldr r1, =0x11DE
ldrh r0, [r0, r1]
cmp r0, #4
beq old
bl 0x%08x
ldr r0, =0x020370C6
ldrh r0, [r0]
cmp r0, #0
beq old
ldr r0, =0x%08x
bl setup
ldr r0, =0x%08x
bl setcb
b ret
old:
pop {r4}
pop {r0}
mov lr, r0
ldr r1, =0x%08x
bx r1
ret:
pop {r4}
pop {r0}
bx r0
setup:
ldr r3, =0x%08x
bx r3
setcb:
ldr r3, =0x%08x
bx r3
ismason:
push {lr}
ldr r1, =326
cmp r0, r1
bcc no
ldr r1, =334
cmp r0, r1
bls yes
no:
ldr r1, =426
cmp r0, r1
beq yes
ldr r1, =429
cmp r0, r1
beq yes
ldr r1, =432
cmp r0, r1
beq yes
ldr r1, =435
cmp r0, r1
beq yes
ldr r1, =740
cmp r0, r1
beq yes
ldr r1, =741
cmp r0, r1
beq yes
ldr r1, =743
cmp r0, r1
beq yes
movs r0, #0
b mdn
yes:
movs r0, #1
mdn:
pop {r1}
bx r1
.ltorg
''' % (leaf, death, CB_CONT, old, SETUP_SCRIPT + 1, SET_CB + 1)

def controls(r):
    """OPTIONS, BUTTON MODE: HELP, LR, L=A, or SWAP. SWAP exchanges A and B. HELP is the normal layout.
    The hook must leave r1 pointing at the key struct (0x030030F0). The first version popped that
    pointer back off, so the game never saw a held button."""
    d = r.b
    stub = r'''
push {r0, lr}
eors r3, r1
ldr r0, =0x0300500c
ldr r0, [r0]
cmp r0, #0
beq noswap
ldrb r0, [r0, #0x13]
cmp r0, #3
bne noswap
movs r0, #3
ands r0, r3
movs r1, #1
ands r1, r0
lsrs r0, r0, #1
lsls r1, r1, #1
orrs r0, r1
movs r1, #3
bics r3, r1
orrs r3, r0
noswap:
ldr r1, =0x030030f0
pop {r0, pc}
.ltorg
'''
    at = 0x175228
    code = r.asm(stub, at)
    assert len(code) <= 56, len(code)
    if d[0x5F4:0x5F8] != bytes([0x4B, 0x40, 0x0D, 0x49]):
        broken = bytes([0x01, 0xBC, 0x02, 0xBC, 0x08, 0x47])
        if broken not in d[at:at + 56]:
            return
        d[at:at + len(code)] = code
        d[at + len(code):at + 56] = b'\x00\xbf' * ((56 - len(code)) // 2)
        print('controls repaired', hex(at))
        return
    assert d[0x3CC30C] == 3
    assert d[at:at + len(code)] == b'\xff' * len(code), (hex(at), len(code))
    r.put(at, code)
    r.bl(0x5F4, at)
    name = say(r, ["SWAP"])[0]
    tab = struct.pack('<IIII', 0x08419E46, 0x08419E4F, 0x08419E4B, name)
    r.w32(0x88A94, 0x08000000 + r.alloc(tab, 4))
    d[0x3CC30C] = 4
    print('controls', hex(at), 'swap', hex(name))

def header(d, g, n):
    gp = u32(d, GROUPS + 4 * g) - 0x08000000
    return u32(d, gp + 4 * n) - 0x08000000

def menu(r):
    d = r.b
    if d[0x6EDD2:0x6EDD4] == bytes([0xC0, 0x46]):
        return
    assert d[0x6EDD0:0x6EDD6] == bytes([0x01, 0x28, 0x02, 0xD1, 0x01, 0x20]), d[0x6EDD0:0x6EDD6].hex()
    d[0x6EDD2:0x6EDD4] = bytes([0xC0, 0x46])          # nop the FLAG_SYS_POKEMON_GET branch; always append POKeMON

def class_name(r):
    d = r.b
    src = 0x23E6D1 + 52 * 13
    dst = 0x23E6D1 + 81 * 13
    name = bytes(d[src:src + 6])
    assert name.endswith(b'\xff') and name[:5] != b'\x00' * 5
    if bytes(d[dst:dst + 6]) != name:
        assert bytes(d[dst:dst + 8]) == b'\x00' * 8, bytes(d[dst:dst + 8]).hex()
        d[dst:dst + 6] = name
    # the opening rival and the other class-81 MASON records use a real class slot as well
    t = 0x798790
    for i in range(800):
        if d[t + 40 * i + 1] == 81:
            d[t + 40 * i + 1] = 52

def church(r):
    d = r.b
    h = header(d, 3, 0)
    lay = u32(d, h) - 0x08000000
    w = u32(d, lay)
    mp = u32(d, lay + 12) - 0x08000000
    sec = u32(d, lay + 20) - 0x08000000
    sat = u32(d, sec + 20) - 0x08000000
    def cell(x, y):
        return mp + 2 * (y * w + x)
    # grass between the player's house and the back of the church stays open
    for x, y in ((7, 8), (8, 8)):
        v = u16(d, cell(x, y))
        if ((v >> 10) & 3) == 1:
            d[cell(x, y):cell(x, y) + 2] = struct.pack('<H', v & ~0x0C00)
    # the drawn doors are the solid tiles one row north of the teleport steps
    for x, y in ((7, 14), (8, 14)):
        v = u16(d, cell(x, y))
        mt = v & 0x3ff
        assert mt in (746, 747), (x, y, mt)
        d[cell(x, y):cell(x, y) + 2] = struct.pack('<H', mt | 0x3000)
        attr = sat + 4 * (mt - 640)
        old = u32(d, attr)
        assert old in (0x20000000, 0x20000069), hex(old)
        r.w32(attr, 0x20000069)                                  # MB_WARP_DOOR
    for mt in (750, 751):
        attr = sat + 4 * (mt - 640)
        old = u32(d, attr)
        assert old in (0x20000067, 0x20000000), hex(old)
        r.w32(attr, 0x20000000)                                  # the steps are ground, not a warp pad
    ev = u32(d, h + 4) - 0x08000000
    wp = u32(d, ev + 8) - 0x08000000
    moved = 0
    for i in range(d[ev + 1]):
        o = wp + 8 * i
        x, y, el, wid, mn, mg = struct.unpack_from('<hhBBBB', d, o)
        if (x, y) in ((7, 15), (8, 15)) and mg == 2:
            d[o:o + 4] = struct.pack('<hh', x, 14)
            moved += 1
        elif (x, y) in ((7, 14), (8, 14)) and mg == 2:
            moved += 1
    assert moved == 2, moved

def oak(r):
    d = r.b
    ptr = u32(d, 0x1695F8)
    if not (0x08000000 <= ptr < 0x0A000000):
        return
    text = dec(d[ptr - 0x08000000:ptr - 0x08000000 + 160])
    if 'no POKéMON' in text or 'no POKeMON' in text:
        return
    if 'robbed' not in text and 'empty' not in text:
        return
    r.w32(0x1695F8, say(r, ["OAK: I have no POKéMON."])[0])

def anne(r):
    d = r.b
    sig = bytes([0x29, 0xF2, 0x04, 0x16, 0x6D, 0x40, 0x02, 0x00, 0x6B, 0x02])
    hit = d.find(sig)
    if hit < 0 or d[hit - 2:hit] != bytes([0x09, 0x00]):
        return
    assert d.find(sig, hit + 1) < 0 or d[d.find(sig, hit + 1) - 2:d.find(sig, hit + 1)] != bytes([0x09, 0x00])
    right = 0x08000000 + r.alloc(bytes([0x13, 0x13, 0x13, 0x13, 0xFE]), 1)
    M = SB()
    M.close()
    M.move(13, right)
    M.waitmove(0)
    M.remobj(13)
    M.setflag(0x4F4)          # HIDE_ANNE
    M.setflag(0x4F2)          # F_ANNE
    M.setvar(VAR_CRY, 2)
    M.releaseall()
    M.end()
    tail = 0x08000000 + put_script(r, M)
    d[hit:hit + 5] = bytes([0x05]) + struct.pack('<I', tail)

def mason_trigger(r):
    d = r.b
    h = header(d, 3, 0)
    ms = u32(d, h + 8) - 0x08000000
    a = ms
    frame = None
    while d[a]:
        if d[a] == 2:
            frame = u32(d, a + 1) - 0x08000000
        a += 5
        if a > ms + 40:
            break
    assert frame, 'pallet has no on-frame table'
    entries = []
    p = frame
    while u16(d, p):
        var, val, scr = struct.unpack_from('<HHI', d, p)
        entries.append((var, val, scr))
        p += 8
        if len(entries) > 8:
            break
    if any(var == VAR_CRY and val == 1 for var, val, _ in entries):
        return
    # the coord script is Mason's
    ev = u32(d, h + 4) - 0x08000000
    cp = u32(d, ev + 12) - 0x08000000
    mason = None
    for i in range(d[ev + 2]):
        x, y, el, unk, var, val, unk2, scr = struct.unpack_from('<hhBBHHHI', d, cp + 16 * i)
        if var == VAR_CRY and val == 1:
            mason = scr
            break
    assert mason, 'mason coord script missing'
    tab = struct.pack('<HHI', VAR_CRY, 1, mason)
    for var, val, scr in entries:
        tab += struct.pack('<HHI', var, val, scr)
    tab += b'\x00' * 8
    new = 0x08000000 + r.alloc(tab, 4)
    a = ms
    while d[a]:
        if d[a] == 2:
            r.w32(a + 1, new)
            return
        a += 5
    raise SystemExit('on-frame entry not rewritten')

def whiteout(r):
    d = r.b
    lit0 = u32(d, 0x7F5CC)
    body = lit0 - 0x08000000
    if not (0x08000000 <= lit0 < 0x0A000000 and d[body] == 0x23 and d[body + 16:body + 19] == bytes([0x2B, 0x4A, 0x08])):
        return
    dead = u32(d, body + 12)
    remove = u32(d, body + 1)
    pool, old_after = after_pool(d)
    assert d[KARMA - 0x08000000:KARMA - 0x08000000 + 2] == bytes([0xD0, 0xB5])
    D = SB(); D.lockall(); D.raw(0x23); D.ptr(KARMA + 1); D.cmp(0x8007, 1); D.goto_if(1, 'hell')
    for i, p in enumerate(say(r, ["The world goes white.", "Something warm lifts you up."])):
        D.msg(p)
        if i == 0:
            D.close()
    D.raw(0x97, 1); D.raw(0x39, 2, 80, 0xFF); D.raw(*struct.pack('<HH', 8, 25)); D.raw(0x27); D.releaseall(); D.end()
    D.lab('hell')
    for i, p in enumerate(say(r, ["Your soul falls.", "Flames rise to meet you."])):
        D.msg(p)
        if i == 0:
            D.close()
    D.raw(0x97, 1); D.raw(0x39, 2, 68, 0xFF); D.raw(*struct.pack('<HH', 11, 23)); D.raw(0x27); D.releaseall(); D.end()
    death = 0x08000000 + put_script(r, D)
    leaf = 0x08000000 + r.fn(LEAF_DOWN)
    heal = 0x08000000 + r.fn(HEAL_KIND)
    wrap = 0x08000000 + r.fn(wrap_after(old_after, leaf, death))
    home_lines = say(r, ["You black out.", "You wake up at home.\nYour POKéMON have been healed."])
    S = SB(); S.raw(0x23); S.ptr(remove)
    S.cmp(VAR_YV, 4); S.goto_if(1, 'dead')
    S.raw(0x23); S.ptr(leaf + 1); S.cmp(0x8007, 1); S.goto_if(1, 'soul')
    S.raw(0x23); S.ptr(heal + 1); S.cmp(0x8007, 1); S.goto_if(1, 'center')
    S.lockall()
    S.msg(home_lines[0]); S.close(); S.msg(home_lines[1])
    S.raw(0x97, 1); S.raw(0x25, 0, 0); S.raw(0x39, 4, 0, 0xFF); S.raw(*struct.pack('<HH', 5, 6)); S.raw(0x27)
    S.releaseall(); S.end()
    S.lab('center'); S.raw(0x05); S.ptr(CENTER_SCRIPT)
    S.lab('soul'); S.raw(0x05); S.ptr(death)
    S.lab('dead'); S.raw(0x05); S.ptr(dead)
    sc = 0x08000000 + put_script(r, S)
    r.w32(0x7F5CC, sc)
    r.w32(0x7F5EC, sc)
    r.w32(pool, wrap + 1)
    print('whiteout', hex(sc), 'leaf', hex(leaf + 1), 'death', hex(death), 'wrap', hex(wrap + 1), 'old', hex(old_after))

REVIVE_LEAF = r'''
push {r4, r5, r6, lr}
ldr r4, =0x02024029
ldrb r4, [r4]
movs r5, #0
lp:
cmp r5, r4
bge dn
movs r0, #100
muls r0, r5
ldr r1, =0x02024284
adds r6, r0, r1
movs r0, r6
movs r1, #11
movs r2, #0
bl getmon
cmp r0, #255
bne nx
movs r0, r6
movs r1, #1
movs r2, #0
bl getmon
ldr r1, =0x53544E44
cmp r0, r1
beq nx
movs r0, r6
movs r1, #0x39
movs r2, #0
bl getmon
cmp r0, #0
bne nx
movs r1, #1
push {r1}
mov r2, sp
movs r0, r6
movs r1, #0x39
bl setmon
pop {r1}
nx:
adds r5, #1
b lp
dn:
pop {r4, r5, r6}
pop {r0}
bx r0
getmon:
ldr r3, =0x%08x
bx r3
setmon:
ldr r3, =0x%08x
bx r3
.ltorg
''' % (GETMON + 1, 0x0804037C + 1)

# If a save is already on the cart, New Game does not run the LEAF / female auto-select.
# It continues that save. A cart with no save still starts one new game as LEAF.
GATE_AT = 0x175260
SAVE_STATUS = 0x030053A0
START_NEW = 0x0812EB2C
CONT_GAME = 0x08110F14
CLEAR_RAM = 0x08003ECC
NEWGAME_BL = 0xCB3E

def once(r):
    d = r.b
    if d[NEWGAME_BL:NEWGAME_BL + 4] != bytes([0x21, 0xF1, 0xF5, 0xFF]):
        return
    assert d[GATE_AT:GATE_AT + 64] == b'\xff' * 64, d[GATE_AT:GATE_AT + 8].hex()
    code = r.asm(f'''
        push {{r4, lr}}
        ldr r4, =0x{SAVE_STATUS:x}
        ldrh r4, [r4]
        cmp r4, #1
        beq saved
        ldr r3, =0x{START_NEW + 1:x}
        bl callr3
        b done
      saved:
        ldr r3, =0x{CLEAR_RAM + 1:x}
        bl callr3
        movs r0, #0
        ldr r3, =0x{CONT_GAME + 1:x}
        bl callr3
      done:
        pop {{r4}}
        pop {{r1}}
        bx r1
      callr3:
        bx r3
    ''', GATE_AT)
    assert len(code) <= 64, len(code)
    r.put(GATE_AT, code)
    r.bl(NEWGAME_BL, GATE_AT)
    print('once', hex(GATE_AT), len(code))

def revive(r):
    """Arceus and Giratina send the player back to Pallet. The permanent LEAF comes back at 1 HP."""
    d = r.b
    sites = (0xF2E6C4, 0xF2EFBC)
    seq = bytes([0x97, 1, 0x39, 3, 0, 0xFF, 11, 0, 10, 0, 0x27, 0x6B, 0x02])
    if d[sites[0]:sites[0] + 1] == b'\x05' and d[sites[1]:sites[1] + 1] == b'\x05':
        return
    for at in sites:
        assert d[at:at + len(seq)] == seq, (hex(at), d[at:at + len(seq)].hex())
    fn = 0x08000000 + r.fn(REVIVE_LEAF)
    S = SB()
    S.raw(0x23)
    S.ptr(fn + 1)
    S.raw(0x97, 1)
    S.raw(0x39, 3, 0, 0xFF)
    S.raw(*struct.pack('<HH', 11, 10))
    S.raw(0x27)
    S.releaseall()
    S.end()
    sc = 0x08000000 + put_script(r, S)
    jump = bytes([0x05]) + struct.pack('<I', sc) + bytes([0x02] * 8)
    assert len(jump) == len(seq)
    for at in sites:
        d[at:at + len(jump)] = jump
    print('revive', hex(sc), 'leaf', hex(fn + 1))

def install(r):
    if r.b[0x1304EE] == 0x19:
        loading_cover(r)
    menu(r)
    class_name(r)
    controls(r)
    church(r)
    oak(r)
    anne(r)
    mason_trigger(r)
    whiteout(r)
    revive(r)
    once(r)

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    install(r)
    r.save(sys.argv[2])
    print('field_fixes end', hex(r.cur))
