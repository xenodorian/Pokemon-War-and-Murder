"""Fix for bless_key.py (usage: bless_key_fix.py IN.gba OUT.gba). Run after bless_key.py.
The hook bless_key.py installed on the map-load call (slot 0x3AF284) jumped to the old function with bx and no link register,
so the old function returned straight to the map loader with five registers left on the stack. Every map change then crashed
(fade out, white flash, soft reset), in every town, not only Viridian.
This hook calls the old function normally (arguments in r0-r3 kept, result kept and returned), then moves the Bless Tag out of the items pocket."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import Rom
import bless_key
from start_menu_fix import thumb1_check

GW_PTR = bless_key.GW_PTR
HEAD = '''push {r4, r5, r6, r7, lr}
ldr r0, =%(old)s
mov r1, pc
adds r1, #3
bx r0
ldr r7, =0x03005008
'''
NEW_HEAD = '''push {r4, r5, r6, r7, lr}
sub sp, sp, #4
ldr r4, =%(old)s
bl callr4
str r0, [sp]
ldr r7, =0x03005008
'''
TAIL = 'done:\npop {r4, r5, r6, r7, pc}\n'
NEW_TAIL = 'done:\nldr r0, [sp]\nadd sp, sp, #4\npop {r4, r5, r6, r7, pc}\ncallr4:\nbx r4\n.ltorg\n'


def apply(r):
    b = r.b
    cur = struct.unpack_from('<I', b, GW_PTR)[0]
    a = (cur & ~1) - 0x08000000
    assert bytes(b[a:a + 4]) == bytes.fromhex('f0b53348'), 'the map-load slot does not hold the bless_key trampoline: %s' % bytes(b[a:a + 8]).hex()
    w = struct.unpack_from('<H', b, a + 2)[0]
    assert w & 0xF800 == 0x4800
    old = struct.unpack_from('<I', b, ((a + 2 + 4) & ~3) + (w & 0xFF) * 4)[0]
    assert old & 1 and 0x08000000 <= old < 0x09000000, hex(old)
    src = bless_key.SRC
    assert HEAD in src and TAIL in src
    src = (src.replace(HEAD, NEW_HEAD).replace(TAIL, NEW_TAIL)) % {'old': hex(old)}
    r.cur = (r.cur + 3) & ~3
    code = r.asm(src, r.cur)
    thumb1_check(code, r.cur, 'bless hook')
    at = r.alloc(code, 4)
    r.w32(GW_PTR, 0x08000000 + at + 1)
    print('bless hook fixed: slot %#x now %#x (calls %#x)' % (GW_PTR, 0x08000000 + at + 1, old))


if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')
