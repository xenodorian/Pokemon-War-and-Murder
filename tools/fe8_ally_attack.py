"""FE8 ally attack animations, step 3: the hooks (usage: fe8_ally_attack.py IN.gba OUT.gba).
Grows the ROM to 32 MB (0xFF fill), packs the data (fe8_ally_attack_data.pack), builds the natives (fe8_ally_attack_native.build)
and hooks PlayerDoMoveAnimation (0x08032978), five Thumb-1 stubs reached through a 'ldr r3,[pc,#0]; bx r3; .word stub' trampoline
(all five sites are 4-aligned and the 8 bytes overwritten are re-executed by the stub):
  A 0x08032A1C  state 1, no special anim: affine off; if should_play(battler): start(battler), animationState = 4 (DoMoveAnim is NOT called);
                else the original path (adds r0,r4,#0; bl DoMoveAnim 0x0807259C), return to 0x08032A26
  B 0x080329D0  switch: new state 4 waits for has_reached_hit(), then DoMoveAnim(r4 = move) and state = 2; states 2 and 3 as before
  C 0x08032A4C  state 2, once the move script is no longer active: if an attack is active wait for is_done(), then end(); then the original
                'affine on' continuation at 0x08032A54
Stubs preserve r4-r7 (r4 = move id, r6 = &gActiveBattler, r7 = &gBattleSpritesDataPtr in this function).
  D 0x08006BA8  BuildOamBuffer entry: if an attack is active call hide() (after every sprite callback and move-script task of the frame, so
                the move script cannot un-hide the portrait for a frame; hiding from the part sprites' own callback was not enough: Quick Attack
                showed the portrait mid-move).  The part SpriteCB is the plain native one (data[0]++).
  E 0x08072DF0  IsBattlerSpriteVisible entry: false for the attacking battler when called from the monbg script commands (keeps the portrait off
                the BG layers, see HOOK_E)
Opponents never reach start(): should_play() is false for odd battlers.
Never run twice on the same ROM (it checks the original bytes at the five sites)."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inc import Rom
from start_menu_fix import thumb1_check
import fe8_ally_attack_data as D
import fe8_ally_attack_native as N

B = 0x08000000
DO_MOVE_ANIM = 0x0807259D
SET_AFFINE = 0x08035451
SITE_A, SITE_B, SITE_C, SITE_D, SITE_E = 0x32A1C, 0x329D0, 0x32A4C, 0x6BA8, 0x72DF0
ORIG = {SITE_A: '02f018fd201c3ff0', SITE_B: '022a32d0032a6bd0', SITE_C: '02f000fd38683278', SITE_D: '30b500f023f800f0', SITE_E: '10b50006040e201c'}
SENT = 0x7FFFFFF1

# BuildOamBuffer (0x08006BA8) entry: hide() while an attack is active.  It runs after every sprite callback (AnimateSprites) and the
# battle callbacks, so nothing the move scripts do to the portrait (AttackerFadeFromInvisible etc.) can show it for a frame.
# Re-executes the 8 overwritten bytes: push {r4,r5,lr}; bl 0x08006BF4; first half of 'bl 0x08006CB8' (so the whole bl is redone here).
HOOK_D = '''
push {r4, r5, lr}
ldr r3, =%(ram)d
ldrb r0, [r3, #9]
cmp r0, #0
beq skip
ldr r3, =%(hide)d
bl c3
skip:
ldr r3, =0x08006BF5
bl c3
ldr r3, =0x08006CB9
bl c3
ldr r3, =0x08006BB3
bx r3
c3:
bx r3
.ltorg
'''

# IsBattlerSpriteVisible (0x08072DF0) entry: while an attack is active and the argument is the attacking battler, answer 0 when the caller is one
# of the monbg style script commands (return address 0x08072C31..0x080735E0: monbg, clearmonbg, monbg_22 ...).  Otherwise monbg copies the
# hidden portrait onto a BG layer (MoveBattlerSpriteToBG; Quick Attack showed it) because the function only looks at the sprite's own
# invisible bit when battlerData.invisible is set.  Re-executes the 4 overwritten instructions (push {r4,lr}; lsls r0,r0,#24; lsrs r4,r0,#24; adds r0,r4,#0).
HOOK_E = '''
mov r1, lr
ldr r3, =%(ram)d
ldrb r2, [r3, #9]
cmp r2, #0
beq orig
ldrb r2, [r3, #8]
lsls r3, r0, #24
lsrs r3, r3, #24
cmp r3, r2
bne orig
ldr r3, =0x08072C31
cmp r1, r3
blo orig
ldr r3, =0x080735E1
cmp r1, r3
bhs orig
movs r0, #0
bx lr
orig:
push {r4, lr}
lsls r0, r0, #24
lsrs r4, r0, #24
adds r0, r4, #0
ldr r3, =0x08072DF9
bx r3
.ltorg
'''

HOOK_A = '''
movs r0, #0
ldr r3, =%(aff)d
bl c3
ldrb r0, [r6]
ldr r3, =%(sp)d
bl c3
cmp r0, #0
beq normal
ldrb r0, [r6]
ldr r3, =%(st)d
bl c3
ldr r0, [r7]
ldrb r1, [r6]
ldr r2, [r0, #4]
lsls r0, r1, #1
adds r0, r0, r1
lsls r0, r0, #2
adds r0, r0, r2
movs r1, #4
strb r1, [r0, #4]
ldr r3, =0x08032AED
bx r3
normal:
adds r0, r4, #0
ldr r3, =%(dma)d
bl c3
ldr r3, =0x08032A27
bx r3
c3:
bx r3
.ltorg
'''

HOOK_B = '''
cmp r2, #4
bne other
ldr r3, =%(hr)d
bl c3
cmp r0, #0
beq wait
adds r0, r4, #0
ldr r3, =%(dma)d
bl c3
ldr r0, [r7]
ldrb r1, [r6]
ldr r2, [r0, #4]
lsls r0, r1, #1
adds r0, r0, r1
lsls r0, r0, #2
adds r0, r0, r2
movs r1, #2
strb r1, [r0, #4]
wait:
ldr r3, =0x08032AED
bx r3
other:
cmp r2, #2
bne t3
ldr r3, =0x08032A3B
bx r3
t3:
cmp r2, #3
bne fall
ldr r3, =0x08032AB1
bx r3
fall:
ldr r3, =0x080329D9
bx r3
c3:
bx r3
.ltorg
'''

HOOK_C = '''
ldr r3, =%(ram)d
ldrb r1, [r3, #9]
cmp r1, #0
beq cont
ldr r3, =%(dn)d
bl c3
cmp r0, #0
beq wait
ldr r3, =%(en)d
bl c3
cont:
movs r0, #1
ldr r3, =%(aff)d
bl c3
ldr r0, [r7]
ldrb r2, [r6]
ldr r3, =0x08032A55
bx r3
wait:
ldr r3, =0x08032AED
bx r3
c3:
bx r3
.ltorg
'''


def _alloc_code(r, src, what):
    at = (r.cur + 3) & ~3
    code = r.asm(src, at)
    thumb1_check(code, at, what)
    a = r.alloc(code, 4)
    assert a == at
    return a, code


def apply(r):
    for site, hx in ORIG.items():
        assert r.b[site:site + 8].hex() == hx, 'unexpected bytes at %#x: %s (stage already applied?)' % (site, r.b[site:site + 8].hex())
    if len(r.b) < D.ROM_SIZE_MAX:
        r.b.extend(b'\xff' * (D.ROM_SIZE_MAX - len(r.b)))
    wcb = N.alloc_cb(r)                          # SpriteCB: data[0]++ (the packer puts it into every SpriteTemplate)
    table = D.pack(r, wcb)
    n = N.build(r, table, wcb)
    p = dict(aff=SET_AFFINE, dma=DO_MOVE_ANIM, sp=n['should_play'], st=n['start'], hr=n['has_reached_hit'],
             dn=n['is_done'], en=n['end'], ram=N.RAM_BASE, hide=n['hide'])
    stubs = {}
    for site, src, what in ((SITE_A, HOOK_A, 'hook A'), (SITE_B, HOOK_B, 'hook B'), (SITE_C, HOOK_C, 'hook C'), (SITE_D, HOOK_D, 'hook D'), (SITE_E, HOOK_E, 'hook E')):
        a, _ = _alloc_code(r, src % p, 'ally_attack ' + what)
        stubs[site] = B + a
        assert site % 4 == 0
        r.b[site:site + 8] = bytes.fromhex('004b1847') + struct.pack('<I', (B + a) | 1)
    return table, n, stubs


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    r = Rom(argv[1])
    table, n, stubs = apply(r)
    r.save(argv[2])
    print('ROM grown to %#x; species table %#x' % (len(r.b), table))
    print({k: hex(v) if isinstance(v, int) else v for k, v in n.items() if k != 'sizes'})
    print('hook stubs', {hex(B + k): hex(v) for k, v in stubs.items()})
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
