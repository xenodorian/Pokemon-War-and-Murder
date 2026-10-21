"""CONTROLS: full in-game input mapping in the start menu (usage: controls_menu.py IN.gba OUT.gba).

The game asks for each of the ten GBA buttons in turn ("Press A.", "Press B.", ... "Press RIGHT."). The player presses
whichever physical button should do that job. The game then shows which signal that press arrived as
("A is set. The game sees that button as B."), or that nothing arrived in 5 seconds (that button keeps its old input).
The game only sees the ten GBA signals the emulator sends; it cannot tell physical X from Y.
- Start menu: a new entry CONTROLS (action 12) after the player's name entry. The order list has room for 11 entries
  (startscroll.py grew it from 9), and the scrolling menu shows them all.
- Each acknowledgement stays up one second and the next prompt follows, so no button press is needed to continue.
- The key reader (the hook bl at 0x5F4 -> 0x175228) translates the raw keys through the mapping before the game sees
  them. BUTTON MODE SWAP (option value 3) still applies after the mapping.
- Reset: holding START + SELECT + UP together (raw keys, before the mapping) clears the mapping at once, and the game
  sees no keys on that frame.
- Storage: vars 0x408C (magic 0xC7A1 when a mapping is active), 0x408D..0x408F (one 4-bit source key index per GBA key:
  A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L). These vars have no name or use in pret, no use in the Outlaw map
  scripts (allmaps.txt) and no use in this repo's tools. Any other value in 0x408C means no mapping (normal buttons).
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inc import Rom
from cry_open import SB, put_script, say, enc

MARK = b'CTLMAP01'
SB1 = 0x03005008
VAROFF = 0x1000 + (0x408C - 0x4000) * 2        # 0x1118 from the save block 1 pointer
MAGIC = 0xC7A1
RESET = 0x4C                                   # START | SELECT | UP (raw); L and R are left out because they open the HELP screen
GSV8004 = 0x020370C0
STUB = 0x175228                                # existing hook target of the bl at 0x5F4 (inside BL range)
ACTS_REFS = (0x6ef9c, 0x6f374, 0x6f3f8)        # code literals of the start menu action table (plus the scroll code's TBL)
DESC_REFS = (0x6f138, 0x6f368)
TAIL_LIT = 0x6edec
FADE_LIT = 0x6f398
ADD_ACTION = 0x0806ed95
CB_CALLS = (0x0806ef19, 0x080f7999, 0x0806fea1)
SCRIPT_RUN = 0x08069ae5
CB_VAR = 0x020370f0

HOOK = r'''
push {r4, r5, r6, r7, lr}
eors r3, r1
ldr r4, =0x%08x
ldr r4, [r4]
cmp r4, #0
beq swap
ldr r5, =0x%x
adds r4, r4, r5
ldr r0, =0x%x
movs r2, r3
ands r2, r0
cmp r2, r0
bne chk
movs r0, #0
strh r0, [r4]
movs r3, #0
b swap
chk:
ldrh r0, [r4]
ldr r5, =0x%x
cmp r0, r5
bne swap
movs r6, #0
movs r7, #0
lp:
cmp r7, #10
bge mapped
movs r0, r7
lsrs r0, r0, #2
lsls r0, r0, #1
adds r0, #2
ldrh r0, [r4, r0]
movs r1, r7
movs r2, #3
ands r1, r2
lsls r1, r1, #2
lsrs r0, r1
movs r2, #15
ands r0, r2
movs r1, r3
lsrs r1, r0
movs r2, #1
ands r1, r2
lsls r1, r7
orrs r6, r1
adds r7, #1
b lp
mapped:
movs r3, r6
swap:
ldr r0, =0x0300500c
ldr r0, [r0]
cmp r0, #0
beq done
ldrb r0, [r0, #0x13]
cmp r0, #3
bne done
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
done:
ldr r1, =0x030030f0
pop {r4, r5, r6, r7}
pop {r0}
bx r0
.ltorg
''' % (SB1, VAROFF, RESET, MAGIC)

BEGIN = r'''
ldr r0, =0x%08x
ldr r0, [r0]
ldr r1, =0x%x
adds r0, r0, r1
movs r1, #0
strh r1, [r0]
ldr r1, =0x3210
strh r1, [r0, #2]
ldr r1, =0x7654
strh r1, [r0, #4]
ldr r1, =0xFF98
strh r1, [r0, #6]
bx lr
.ltorg
''' % (SB1, VAROFF)

COMMIT = r'''
ldr r0, =0x%08x
ldr r0, [r0]
ldr r1, =0x%x
adds r0, r0, r1
ldr r1, =0x%x
strh r1, [r0]
bx lr
.ltorg
''' % (SB1, VAROFF, MAGIC)

# Busy-waits on the raw key register; interrupts keep running, so the prompt reaches VRAM and music plays.
CAPTURE = r'''
push {r4, r5, r6, r7, lr}
ldr r4, =0x04000130
ldr r7, =0x3FF
bl release
movs r6, #0
pl:
ldrh r0, [r4]
mvns r0, r0
ands r0, r7
cmp r0, #0
bne got
bl frame
adds r6, #1
ldr r1, =300
cmp r6, r1
blt pl
b none
got:
movs r1, #0
bit:
movs r2, #1
lsls r2, r1
tst r0, r2
bne have
adds r1, #1
cmp r1, #10
blt bit
b none
have:
movs r6, r1
ldr r2, =0x%08x
ldrh r2, [r2]
ldr r3, =0x%08x
ldr r3, [r3]
ldr r5, =0x%x
adds r3, r3, r5
movs r5, r2
lsrs r5, r5, #2
lsls r5, r5, #1
adds r3, r3, r5
movs r5, #3
ands r2, r5
lsls r2, r2, #2
ldrh r5, [r3]
movs r0, #15
lsls r0, r2
bics r5, r0
lsls r1, r2
orrs r5, r1
strh r5, [r3]
ldr r1, =0x02021cd0
ldr r0, =0x%%08x
ldr r2, =0x020370c0
ldrh r2, [r2]
lsls r2, r2, #2
ldr r0, [r0, r2]
bl cpy
ldr r0, =0x%%08x
lsls r2, r6, #2
ldr r0, [r0, r2]
bl cpy
movs r3, #0xad
strb r3, [r1]
movs r3, #0xff
strb r3, [r1, #1]
ldr r0, =0x020370c2
movs r1, #1
strh r1, [r0]
bl release
b out
none:
ldr r0, =0x020370c2
movs r1, #0
strh r1, [r0]
out:
pop {r4, r5, r6, r7}
pop {r0}
bx r0
release:
push {r6, lr}
movs r6, #0
wr:
ldrh r0, [r4]
mvns r0, r0
ands r0, r7
cmp r0, #0
beq wrd
bl frame
adds r6, #1
ldr r1, =600
cmp r6, r1
blt wr
wrd:
pop {r6, pc}
cpy:
ldrb r3, [r0]
cmp r3, #0xff
beq cpd
strb r3, [r1]
adds r0, #1
adds r1, #1
b cpy
cpd:
bx lr
frame:
ldr r2, =0x04000006
w1:
ldrh r3, [r2]
cmp r3, #160
bne w1
w2:
ldrh r3, [r2]
cmp r3, #160
beq w2
bx lr
.ltorg
''' % (GSV8004, SB1, VAROFF + 2)

KEY_NAMES = ['A', 'B', 'SELECT', 'START', 'RIGHT', 'LEFT', 'UP', 'DOWN', 'R', 'L']

BUTTONS = [(0, 'A'), (1, 'B'), (3, 'START'), (2, 'SELECT'), (9, 'L'), (8, 'R'), (6, 'UP'), (7, 'DOWN'), (5, 'LEFT'), (4, 'RIGHT')]


def u32(d, o):
    return struct.unpack_from('<I', d, o)[0]


def repoint(d, old, new):
    pat = struct.pack('<I', old); n = 0
    for o in range(0, len(d) - 3, 4):
        if d[o:o + 4] == pat:
            d[o:o + 4] = struct.pack('<I', new); n += 1
    return n


def apply(r):
    d = r.b
    assert MARK not in d, 'CONTROLS already installed'
    acts = u32(d, ACTS_REFS[0])
    assert all(u32(d, o) == acts for o in ACTS_REFS), 'action table literals moved'
    desc = u32(d, DESC_REFS[0])
    assert all(u32(d, o) == desc for o in DESC_REFS), 'description table literals moved'
    n_acts = 12
    for i in range(n_acts):
        nm, cb = struct.unpack_from('<II', d, acts - 0x08000000 + 8 * i)
        assert 0x08000000 <= nm < 0x0A000000 and cb & 1, ('action', i)
    assert d[0x5F4:0x5F8] != bytes([0x4B, 0x40, 0x0D, 0x49]), 'key reader hook missing (run field_fixes first)'
    assert d[STUB:STUB + 2] == bytes([0x01, 0xB5]), 'unexpected hook stub at 0x175228'

    # key reader: the in-range stub tail-jumps to the full hook (lr still points back into the key reader)
    hook = r.fn(HOOK)
    tramp = r.asm('ldr r0, =0x%08x\nbx r0\n.ltorg\n' % (0x08000000 + hook + 1), STUB)
    d[STUB:STUB + 56] = tramp + b'\xc0\x46' * ((56 - len(tramp)) // 2)

    # natives and the script
    f_begin = 0x08000000 + r.fn(BEGIN) + 1
    f_commit = 0x08000000 + r.fn(COMMIT) + 1
    names = say(r, KEY_NAMES)
    names_tab = 0x08000000 + r.alloc(b''.join(struct.pack('<I', p) for p in names), 4)
    full = {0: 'A', 1: 'B', 2: 'SELECT', 3: 'START', 4: 'RIGHT', 5: 'LEFT', 6: 'UP', 7: 'DOWN', 8: 'R', 9: 'L'}
    prefixes = [0x08000000 + r.alloc(enc("%s is set. The game sees\nthat button as " % full[k]), 1) for k in range(10)]
    prefix_tab = 0x08000000 + r.alloc(b''.join(struct.pack('<I', p) for p in prefixes), 4)
    f_capture = 0x08000000 + r.fn(CAPTURE % (prefix_tab, names_tab)) + 1
    assert enc('.')[0] == 0xAD

    def show(S, p, frames):
        S.raw(0x67); S.ptr(p)              # message
        S.raw(0x66)                        # waitmessage
        if frames:
            S.raw(0x28, frames & 0xff, frames >> 8)   # delay

    intro = say(r, ["Each button will be named.\nPress the one you want for it."])[0]
    done1, done2 = say(r, ["Controls saved.", "To reset them, hold START,\nSELECT and UP together."])
    S = SB()
    S.lockall()
    S.raw(0x23); S.ptr(f_begin)
    show(S, intro, 90)
    for k, n in BUTTONS:
        ask = say(r, ["Press %s.\n(Wait 5 seconds to skip.)" % n])[0]
        skip = say(r, ["No button pressed.\n%s stays as it was." % n])[0]
        S.setvar(0x8004, k)
        show(S, ask, 0)
        S.raw(0x23); S.ptr(f_capture)
        S.cmp(0x8005, 1)
        S.goto_if(1, 'ok%d' % k)
        show(S, skip, 60)
        S.goto('nx%d' % k)
        S.lab('ok%d' % k)
        show(S, 0x02021cd0, 60)          # text composed by capture: "<button> is set ... as <signal>."
        S.lab('nx%d' % k)
    S.raw(0x23); S.ptr(f_commit)
    show(S, done1, 60)
    show(S, done2, 120)
    S.raw(0x68)                            # closemessage
    S.releaseall()
    S.end()
    script = 0x08000000 + put_script(r, S)

    # start menu callback, same shape as the KARMA entry
    thunk = r.alloc(bytes([0x08, 0x47]), 4)
    call = lambda a: 'ldr r1, =0x%08x\nbl 0x%08x\n' % (a, 0x08000000 + thunk)
    cb = 0x08000000 + r.fn('push {lr}\n' + ''.join(call(a) for a in CB_CALLS) +
                           'ldr r0, =0x%08x\n' % script + call(SCRIPT_RUN) +
                           'movs r0, #1\npop {r1}\nbx r1\n.ltorg\n') + 1

    # action and description tables with entry 12
    name = say(r, ["CONTROLS"])[0]
    blurb = say(r, ["Choose which button\ndoes what."])[0]
    a_old = acts - 0x08000000; d_old = desc - 0x08000000
    a_new = 0x08000000 + r.alloc(bytes(d[a_old:a_old + 8 * n_acts]) + struct.pack('<II', name, cb), 4)
    d_new = 0x08000000 + r.alloc(bytes(d[d_old:d_old + 4 * n_acts]) + struct.pack('<I', blurb), 4)
    na = repoint(d, acts, a_new); nd = repoint(d, desc, d_new)
    assert na == 4 and nd == 2, (na, nd)          # three menu literals + the scroll code's TBL; two description literals

    # menu order: ... KARMA (11), player (3), CONTROLS (12), SAVE, OPTION, EXIT
    order = (2, 9, 10, 11, 3, 12, 4, 5, 6)
    tail = r.fn(''.join('movs r0, #%d\n' % n + call(ADD_ACTION) for n in order) + 'pop {r0}\nbx r0\n.ltorg\n')
    r.w32(TAIL_LIT, 0x08000000 + tail + 1)

    # fade exemption: the CONTROLS callback keeps the menu from fading, like the other script entries
    old_fade = u32(d, FADE_LIT)
    fade = r.fn('push {lr}\nldr r0, =0x%08x\nldr r1, [r0]\nldr r0, =0x%08x\ncmp r1, r0\nbeq skip\n'
                'pop {r1}\nmov lr, r1\nldr r1, =0x%08x\nbx r1\nskip:\npop {r0}\nbx r0\n.ltorg\n'
                % (CB_VAR, cb, old_fade))
    r.w32(FADE_LIT, 0x08000000 + fade + 1)

    r.alloc(MARK, 4)
    print('controls_menu: hook %#x, script %#x, cb %#x, actions %#x, desc %#x, tail %#x, fade %#x, end %#x'
          % (0x08000000 + hook, script, cb, a_new, d_new, 0x08000000 + tail, 0x08000000 + fade, 0x08000000 + r.cur))


if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')
