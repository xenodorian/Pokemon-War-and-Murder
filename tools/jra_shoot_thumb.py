"""The captain-loot wrapper was Thumb-2. This CPU is Thumb-1, so Shoot froze
after the money line, on the first wide instruction. Same behavior, 16-bit
instructions, and the call goes through the thunk jra_shoot_fix already uses.
"""
import sys
sys.path.insert(0, 'tools')
from inc import Rom

AT = 0xF8DA20
OLD = bytes.fromhex('30b51048008810494fea')  # push; ldr; ldrh; ldr; lsl.w
SRC = r'''
push {r4, r5, lr}
ldr r0, =0x020386ae
ldrh r0, [r0]
ldr r1, =0x08798790
lsls r2, r0, #5
lsls r3, r0, #3
adds r2, r2, r3
adds r4, r1, r2
ldrb r5, [r4, #1]
cmp r5, #44
bne do_orig
movs r3, r4
adds r3, #32
ldrb r5, [r3]
cmp r5, #0
beq do_orig
subs r5, #1
strb r5, [r3]
ldr r0, =0x08F22F41
bl 0x08F8C618
movs r3, r4
adds r3, #32
ldrb r5, [r3]
adds r5, #1
strb r5, [r3]
pop {r4, r5, pc}
do_orig:
ldr r0, =0x08F22F41
bl 0x08F8C618
pop {r4, r5, pc}
'''


def apply(r):
    cur = bytes(r.b[AT:AT + len(OLD)])
    if cur != OLD:
        new = r.asm(SRC, AT)
        if bytes(r.b[AT:AT + 10]) == new[:10]:
            print('shoot wrapper already thumb')
            return
        raise SystemExit('shoot wrapper missing: ' + cur.hex())
    code = r.asm(SRC, AT)
    assert len(code) == 80, len(code)
    assert AT + len(code) <= 0xF8DA7C
    r.b[AT:AT + len(code)] = code
    print('shoot wrapper thumb', hex(0x08000000 + AT), len(code))


if __name__ == '__main__':
    r = Rom(sys.argv[1])
    apply(r)
    r.save(sys.argv[2])
    print('ok')
