"""Bless Tag is a key item and is not consumed.

The bag still checks that you have one. Blessing no longer removes it.
A map-load hook moves any copy sitting in the items pocket over to key items.
"""
import sys, struct
sys.path.insert(0, 'tools')
from inc import Rom

ITEM_BASE = 0x3db028
ITEM = 56
GW_PTR = 0x3AF284
MAGIC = b'BLESKEY1'
TAKE = bytes([0x45, 0x38, 0x00, 0x01, 0x00])

SRC = r'''
push {r4, r5, r6, r7, lr}
ldr r0, =%(old)s
mov r1, pc
adds r1, #3
bx r0
ldr r7, =0x03005008
ldr r7, [r7]
movs r4, #0
movs r5, #0
kfind:
cmp r5, #30
beq kfound
lsls r0, r5, #2
ldr r1, =0x3B8
adds r0, r0, r1
adds r0, r0, r7
ldrh r1, [r0]
cmp r1, #56
bne knext
movs r4, #1
knext:
adds r5, #1
b kfind
kfound:
movs r6, #0
movs r5, #0
kempty:
cmp r4, #1
beq clear
cmp r5, #30
beq clear
lsls r0, r5, #2
ldr r1, =0x3B8
adds r0, r0, r1
adds r0, r0, r7
ldrh r1, [r0]
cmp r1, #0
bne enext
adds r6, r5, #1
b clear
enext:
adds r5, #1
b kempty
clear:
cmp r4, #1
beq wipe
cmp r6, #0
beq done
wipe:
movs r5, #0
wloop:
cmp r5, #42
beq compact
lsls r0, r5, #2
ldr r1, =0x310
adds r0, r0, r1
adds r0, r0, r7
ldrh r1, [r0]
cmp r1, #56
bne wnext
movs r1, #0
strh r1, [r0]
strh r1, [r0, #2]
wnext:
adds r5, #1
b wloop
compact:
movs r5, #0
movs r3, #0
cloop:
cmp r3, #42
beq cpad
lsls r0, r3, #2
ldr r1, =0x310
adds r0, r0, r1
adds r0, r0, r7
ldrh r1, [r0]
cmp r1, #0
beq cnext
lsls r2, r5, #2
ldr r1, =0x310
adds r2, r2, r1
adds r2, r2, r7
ldrh r1, [r0]
strh r1, [r2]
ldrh r1, [r0, #2]
strh r1, [r2, #2]
adds r5, #1
cnext:
adds r3, #1
b cloop
cpad:
cmp r5, #42
beq place
lsls r0, r5, #2
ldr r1, =0x310
adds r0, r0, r1
adds r0, r0, r7
movs r1, #0
strh r1, [r0]
strh r1, [r0, #2]
adds r5, #1
b cpad
place:
cmp r4, #1
beq done
cmp r6, #0
beq done
subs r6, #1
lsls r0, r6, #2
ldr r1, =0x3B8
adds r0, r0, r1
adds r0, r0, r7
movs r1, #56
strh r1, [r0]
movs r1, #1
strh r1, [r0, #2]
done:
pop {r4, r5, r6, r7, pc}
'''


def apply(r):
    b = r.b
    if b.find(MAGIC) >= 0:
        print('bless key already')
        return
    o = ITEM_BASE + 44 * ITEM
    assert b[o:o + 9] == bytes([0xBC, 0xC6, 0xBF, 0xCD, 0xCD, 0x00, 0xCE, 0xBB, 0xC1]), b[o:o + 9]
    assert b[o + 26] == 1, b[o + 26]
    b[o + 24] = 1
    b[o + 26] = 2
    n = 0
    pos = 0
    while True:
        i = b.find(TAKE, pos)
        if i < 0:
            break
        b[i:i + 5] = b'\x00' * 5
        n += 1
        pos = i + 5
    assert n >= 1, n
    old = struct.unpack_from('<I', b, GW_PTR)[0]
    assert old & 1, hex(old)
    r.cur = (r.cur + 3) & ~3
    code = r.asm(SRC % {'old': hex(old)}, r.cur)
    at = r.alloc(code, 4)
    assert at == r.cur - len(code)
    r.w32(GW_PTR, 0x08000000 + at + 1)
    r.alloc(MAGIC, 1)
    print('bless key', n, 'takes removed, hook', hex(0x08000000 + at + 1), 'was', hex(old))


if __name__ == '__main__':
    r = Rom(sys.argv[1])
    apply(r)
    r.save(sys.argv[2])
    print('ok', hex(r.cur))
