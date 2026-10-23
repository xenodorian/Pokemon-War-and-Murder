"""FE8 ally attack animations, step 2: the natives (hand written Thumb-1, assembled with keystone).
Port of /home/user/poekemblem/decomp_overlay/src/ally_attack.c.  No ROM data other than the species table is needed here.

Usage from a stage:
    cb = fe8_ally_attack_native.alloc_cb(r)            # SpriteCB|1, needed first by fe8_ally_attack_data.pack(r, cb)
    table = fe8_ally_attack_data.pack(r, cb)           # ROM address of the species table
    n = fe8_ally_attack_native.build(r, table, cb)     # dict of thumb addresses (|1)
Keys of the dict: sprite_cb, find, should_play, start, has_reached_hit, is_done, end, hide, ram.
    should_play(battler u8) -> 1 if battler is on the player side and its species is in the table
    start(battler u8)       -> load palette, create the part sprites, hide the portrait, set active
    has_reached_hit()       -> sprite 0 frame counter (data[0]) >= table hit
    is_done()               -> every part sprite has animEnded
    end()                   -> destroy the parts, free the palette, clear active, portrait visible again (no-op when not active)
    hide()                  -> while active: portrait and every in-use sprite with the same template and tileNum invisible
All are plain AAPCS-style functions (args in r0, return in r0, r4-r7 preserved), safe to call with bl through a bx thunk.

Table (written by fe8_ally_attack_data.py): 16-byte entries {u16 species, u8 numParts, u8 hit, u32 palPtr, u32 partsPtr, u32 pad}
ended by species 0xFFFF.  Parts are {u32 templatePtr, s16 x, s16 y}.  numParts must be <= 8 (not checked here).
A part whose CreateSprite fails (returns 64) is stored as 0xFF and skipped everywhere.

RAM (RAM_BASE, 0x30 bytes reserved):
  +0x00 u8 sSpriteIds[8]   +0x08 u8 battler   +0x09 u8 active   +0x0C u32 entry pointer   +0x10 SpritePalette {u32 data, u16 tag, u16 pad}
Why 0x0203FC80: it is in the unused top of EWRAM.  (1) A scan of the whole 0x08000000-0x08FFFFFF ROM for the word range 0x0203FC00-0x0203FD00 finds
only 0x0203FC00 itself and the odd, unaligned 0x0203FCFF (data, not pointers); nothing can reach 0x0203FC80-0x0203FCB0 with an immediate offset
from either (ldr word reach +0x7C, ldrh +0x3E).  Used neighbours: 0x0203F900 (old start_controls report, 16 refs), 0x0203FB74-0x0203FB88.
(2) 0x0203F3A9-0x0203FFFF stayed all zero in the emulator at 10 sample frames from boot to inside a battle (tools/harness_new, battle.py flow).
(3) The battle structs, gSprites and the save scratch buffer (0x02039A3C) are all far below.  EWRAM is cleared at boot, so 'active' starts at 0.
Emulator-tested (scratch ROM with test hooks in PlayerDoMoveAnimation, dummy 2-part table, species 27): parts appear at the table centers, data[0]
counts 1/frame, animEnded (0x3F bit 0x10) sets, the portrait is hidden while active and visible again after end(), RAM stays zero outside the state.
NOTE for the data packer: an OamData is 8 bytes {y, shape<<6, x_lo, size<<6 | x_hi, tileNum_lo, priority<<2 | tileNum_hi, 0, 0};
64x64 priority 1 = 00 00 00 C0 00 04 00 00 (the bytes quoted in CURRENT_WORK.md, 00 00 C0 00 04 00 00 00, draw an 8x8 sprite at x=0xC0).
Verified addresses (disassembled on PokemonWarAndMurder.gba, see the report in the commit/notes):
  gSprites 0x0202063C stride 0x44 (CreateSpriteAt memcpy of 0x44), template* at +0x14 (NOT +0x00: CreateSpriteAt does str r1,[r7,#0x14]),
  oam attr2 at +0x04, data[0] at +0x2E and data[1] at +0x30 (battle code strh r,[spr,#0x2e]/[#0x30]), flags +0x3E (inUse 1, invisible 4),
  +0x3F (CreateSpriteAt ORs 4|8|0x40 = animBeginning|affineAnimBeginning|usingSheet, so animEnded = 0x10),
  CreateSprite 0x08006F8C(template,x,y,subpriority), DestroySprite 0x08007280, LoadSpritePalette 0x08008928 (struct {data, u16 tag @4}),
  FreeSpritePaletteByTag 0x08008A30, gBattlerSpriteIds 0x02023D44, gBattleMons 0x02023BE4 stride 0x58."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from start_menu_fix import thumb1_check

RAM_BASE = 0x0203FC80
RAM_SIZE = 0x30
PAL_TAG = 0xEA01
GSPRITES = 0x0202063C
GBATTLERSPRITEIDS = 0x02023D44
GBATTLEMONS = 0x02023BE4
CREATE_SPRITE = 0x08006F8C
DESTROY_SPRITE = 0x08007280
LOAD_SPRITE_PALETTE = 0x08008928
FREE_PAL_BY_TAG = 0x08008A30

# state offsets
O_IDS, O_BATTLER, O_ACTIVE, O_ANIM, O_PAL = 0x00, 0x08, 0x09, 0x0C, 0x10


def _fn(r, src, what):
    at = (r.cur + 3) & ~3
    code = r.asm(src, at)
    thumb1_check(code, at, what)
    a = r.alloc(code, 4)
    assert a == at
    return (0x08000000 + a) | 1, len(code)


SPRITE_CB = '''
ldrh r1, [r0, #0x2e]
adds r1, #1
strh r1, [r0, #0x2e]
bx lr
'''


def alloc_cb(r):
    """SpriteCB: sprite->data[0]++ .  Returns the thumb address."""
    return _fn(r, SPRITE_CB, 'ally_attack SpriteCB')[0]


# r0 = species (u16) -> r0 = table entry or 0.  Clobbers r1-r3.
FIND = '''
ldr r1, =%(table)d
ldr r3, =0xFFFF
floop:
ldrh r2, [r1]
cmp r2, r3
beq fnone
cmp r2, r0
beq ffound
adds r1, #16
b floop
ffound:
adds r0, r1, #0
bx lr
fnone:
movs r0, #0
bx lr
.ltorg
'''

SHOULD_PLAY = '''
push {lr}
movs r1, #1
tst r0, r1
bne no
movs r1, #0x58
muls r1, r0
ldr r2, =%(mons)d
adds r2, r2, r1
ldrh r0, [r2]
bl %(find)d
cmp r0, #0
beq no
movs r0, #1
pop {r1}
bx r1
no:
movs r0, #0
pop {r1}
bx r1
.ltorg
'''

# r4 = loop index, r5 = state, r6 = entry, r7 = call target
START = '''
push {r4, r5, r6, r7, lr}
ldr r5, =%(ram)d
strb r0, [r5, #8]
movs r1, #0x58
muls r1, r0
ldr r2, =%(mons)d
ldrh r0, [r2, r1]
bl %(find)d
adds r6, r0, #0
str r6, [r5, #12]
ldr r0, [r6, #4]
str r0, [r5, #16]
ldr r0, =%(tag)d
strh r0, [r5, #20]
movs r0, #0
strh r0, [r5, #22]
adds r0, r5, #0
adds r0, #16
ldr r7, =%(loadpal)d
bl callr7
movs r4, #0
loop:
ldrb r0, [r6, #2]
cmp r4, r0
bge done
ldr r0, [r6, #8]
lsls r1, r4, #3
adds r2, r0, r1
movs r3, #6
ldrsh r3, [r2, r3]
movs r1, #4
ldrsh r1, [r2, r1]
ldr r0, [r2]
adds r2, r3, #0
movs r3, #0
ldr r7, =%(create)d
bl callr7
adds r1, r5, r4
cmp r0, #0x40
bhs fail
strb r0, [r1]
movs r1, #0x44
muls r1, r0
ldr r2, =%(sprites)d
adds r1, r1, r2
ldrb r2, [r5, #8]
strh r2, [r1, #0x30]
b next
fail:
movs r0, #0xFF
strb r0, [r1]
next:
adds r4, #1
b loop
done:
ldrb r0, [r5, #8]
ldr r1, =%(bsi)d
ldrb r0, [r1, r0]
movs r1, #0x44
muls r1, r0
ldr r2, =%(sprites)d
adds r1, r1, r2
adds r1, #0x3e
ldrb r2, [r1]
movs r3, #4
orrs r2, r3
strb r2, [r1]
movs r0, #1
strb r0, [r5, #9]
pop {r4, r5, r6, r7}
pop {r1}
bx r1
callr7:
bx r7
.ltorg
'''

HAS_REACHED_HIT = '''
ldr r3, =%(ram)d
ldrb r0, [r3, #0]
cmp r0, #0x40
bhs yes
movs r1, #0x44
muls r1, r0
ldr r2, =%(sprites)d
adds r1, r1, r2
ldrh r0, [r1, #0x2e]
ldr r2, [r3, #12]
ldrb r2, [r2, #3]
cmp r0, r2
blo no
yes:
movs r0, #1
bx lr
no:
movs r0, #0
bx lr
.ltorg
'''

IS_DONE = '''
push {r4, lr}
ldr r3, =%(ram)d
ldr r2, [r3, #12]
ldrb r2, [r2, #2]
movs r4, #0
loop:
cmp r4, r2
bge yes
ldrb r0, [r3, r4]
adds r4, #1
cmp r0, #0x40
bhs loop
movs r1, #0x44
muls r1, r0
ldr r0, =%(sprites)d
adds r1, r1, r0
adds r1, #0x3f
ldrb r0, [r1]
movs r1, #0x10
tst r0, r1
beq no
b loop
yes:
movs r0, #1
pop {r4}
pop {r1}
bx r1
no:
movs r0, #0
pop {r4}
pop {r1}
bx r1
.ltorg
'''

END = '''
push {r4, r5, r6, r7, lr}
ldr r5, =%(ram)d
ldrb r0, [r5, #9]
cmp r0, #0
beq out
ldr r6, [r5, #12]
movs r4, #0
loop:
ldrb r0, [r6, #2]
cmp r4, r0
bge done
ldrb r0, [r5, r4]
adds r4, #1
cmp r0, #0x40
bhs loop
movs r1, #0x44
muls r1, r0
ldr r2, =%(sprites)d
adds r0, r1, r2
ldr r7, =%(destroy)d
bl callr7
b loop
done:
ldr r0, =%(tag)d
ldr r7, =%(freepal)d
bl callr7
movs r0, #0
strb r0, [r5, #9]
ldrb r0, [r5, #8]
ldr r1, =%(bsi)d
ldrb r0, [r1, r0]
movs r1, #0x44
muls r1, r0
ldr r2, =%(sprites)d
adds r1, r1, r2
adds r1, #0x3e
ldrb r2, [r1]
movs r3, #4
bics r2, r3
strb r2, [r1]
out:
pop {r4, r5, r6, r7}
pop {r1}
bx r1
callr7:
bx r7
.ltorg
'''

# r5 = counter, r6 = portrait sprite, r7 = scan pointer, r3 = template, r4 = tileNum
HIDE = '''
push {r4, r5, r6, r7, lr}
ldr r5, =%(ram)d
ldrb r0, [r5, #9]
cmp r0, #0
beq out
ldrb r0, [r5, #8]
ldr r1, =%(bsi)d
ldrb r0, [r1, r0]
movs r1, #0x44
muls r1, r0
ldr r7, =%(sprites)d
adds r6, r1, r7
adds r0, r6, #0
adds r0, #0x3e
ldrb r1, [r0]
movs r2, #4
orrs r1, r2
strb r1, [r0]
ldr r3, [r6, #0x14]
ldrh r4, [r6, #4]
lsls r4, r4, #22
lsrs r4, r4, #22
movs r5, #0
loop:
cmp r7, r6
beq next
adds r0, r7, #0
adds r0, #0x3e
ldrb r1, [r0]
movs r2, #1
tst r1, r2
beq next
ldr r2, [r7, #0x14]
cmp r2, r3
bne next
ldrh r2, [r7, #4]
lsls r2, r2, #22
lsrs r2, r2, #22
cmp r2, r4
bne next
movs r2, #4
orrs r1, r2
strb r1, [r0]
next:
adds r7, #0x44
adds r5, #1
cmp r5, #64
blt loop
out:
pop {r4, r5, r6, r7}
pop {r1}
bx r1
.ltorg
'''


def build(r, table, cb):
    """Allocate the natives.  table = ROM file offset of the species table (as returned by pack) or its 0x08xxxxxx address; cb = alloc_cb result."""
    if table < 0x08000000:
        table += 0x08000000
    p = dict(table=table, mons=GBATTLEMONS, sprites=GSPRITES, bsi=GBATTLERSPRITEIDS, ram=RAM_BASE, tag=PAL_TAG,
             create=CREATE_SPRITE | 1, destroy=DESTROY_SPRITE | 1, loadpal=LOAD_SPRITE_PALETTE | 1, freepal=FREE_PAL_BY_TAG | 1)
    out = {'sprite_cb': cb, 'ram': RAM_BASE}
    sizes = {}
    find, sizes['find'] = _fn(r, FIND % p, 'ally_attack find'); out['find'] = find
    p['find'] = 0x08000000 + (find & ~1)
    for name, src in (('should_play', SHOULD_PLAY), ('start', START), ('has_reached_hit', HAS_REACHED_HIT),
                      ('is_done', IS_DONE), ('end', END), ('hide', HIDE)):
        out[name], sizes[name] = _fn(r, src % p, 'ally_attack ' + name)
    out['sizes'] = sizes
    return out


def selftest():
    import struct
    from inc import Rom
    S = '/tmp/claude-0/-home-user/d4300b87-da27-5b91-90f9-0bc8d9580245/scratchpad/an'
    src = os.environ.get('SRC_ROM', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'PokemonWarAndMurder.gba'))
    r = Rom(src)                       # read only: the copy is what gets saved
    cb = alloc_cb(r)
    # dummy table: two entries and the terminator
    tbl = r.alloc(struct.pack('<HBBIII', 256, 2, 34, 0, 0, 0) + struct.pack('<HBBIII', 259, 1, 5, 0, 0, 0) + struct.pack('<HBBIII', 0xFFFF, 0, 0, 0, 0, 0), 4)
    n = build(r, tbl, cb)
    for k, v in n.items():
        print(k, hex(v) if isinstance(v, int) else v)
    # every function already passed thumb1_check inside _fn
    os.makedirs(S, exist_ok=True)
    out = os.path.join(S, 'native_test.gba')
    r.save(out)
    print('saved', out)
    return n


if __name__ == '__main__':
    selftest()
