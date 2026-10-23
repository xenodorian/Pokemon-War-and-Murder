"""Shackled captains really leave the map (usage: shackle_despawn2.py IN.gba OUT.gba).
shackle_despawn.py removed the sprite with `removeobject 0x800F`, but 0x800F is a scratch word the battle and shop code overwrite
(unstable_order.py writes it every attack), so the wrong local id was removed. A new native now finds the captain's own object in the
map header (the object whose script is a trainerbattle against the opponent just fought) and puts its local id in 0x8004;
the shackle wrapper script then removes that one. The hide flag set by shackle_do2 keeps them gone on later visits."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import Rom
from start_menu_fix import thumb1_check

DO2 = 0x08F8C7FD
FIND = """
push {r4, r5}
ldr r0, =0x020370C0
ldr r1, =0x02036DFC
ldr r1, [r1, #4]
ldrb r2, [r1, #0]
ldr r1, [r1, #4]
ldr r3, =0x020386AE
ldrh r3, [r3]
loop:
cmp r2, #0
beq done
ldr r4, [r1, #16]
cmp r4, #0
beq next
ldrb r5, [r4, #0]
cmp r5, #0x5C
bne next
ldrh r5, [r4, #2]
cmp r5, r3
bne next
ldrb r5, [r1, #0]
strh r5, [r0]
b done
next:
adds r1, #24
subs r2, #1
b loop
done:
pop {r4, r5}
bx lr
"""


def apply(r):
    b = r.b
    pat = b'\x23' + struct.pack('<I', DO2)
    i = b.find(pat)
    assert i >= 0 and b[i + 5:i + 9] == bytes([0x53, 0x0F, 0x80, 0x03]), 'unexpected wrapper %s' % bytes(b[i:i + 12]).hex()
    r.cur = (r.cur + 3) & ~3
    code = r.asm(FIND, r.cur)
    thumb1_check(code, r.cur, 'captain find')
    fn = r.alloc(code, 4)
    scr = pat + b'\x23' + struct.pack('<I', 0x08000001 + fn) + bytes([0x53, 0x04, 0x80, 0x03])
    at = r.alloc(scr, 4)
    new = 0x08000000 + at
    old = 0x08000000 + i
    n = 0
    k = 0
    while True:
        k = b.find(bytes([0x04]) + struct.pack('<I', old), k)
        if k < 0: break
        struct.pack_into('<I', b, k + 1, new); n += 1; k += 1
    assert n == 2, n
    print('captain finder %#x, wrapper %#x -> %#x, %d call sites' % (0x08000001 + fn, old, new, n))


if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')
