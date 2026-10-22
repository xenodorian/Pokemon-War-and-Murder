"""Captain loot split.
When a captain is shot, the player receives every party member except the
last (the namesake). Shackle is unchanged and still gives only the last.
Soldiers and the general are unaffected."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import *

OLD_SHOOT = 0x08F22F41
LITERAL = 0xF8C608   # the pool slot jra_shoot_fix loads

WRAPPER = '''
push {r4, r5, lr}
ldr r0, =0x020386ae
ldrh r0, [r0]
ldr r1, =0x08798790
lsl r2, r0, #5
lsl r3, r0, #3
add r2, r2, r3
add r4, r1, r2
ldrb r5, [r4, #1]
cmp r5, #44
bne do_orig
ldrb r5, [r4, #32]
cmp r5, #0
beq do_orig
sub r5, r5, #1
strb r5, [r4, #32]
ldr r0, =0x08F22F41
blx r0
ldrb r5, [r4, #32]
add r5, r5, #1
strb r5, [r4, #32]
pop {r4, r5, pc}
do_orig:
ldr r0, =0x08F22F41
blx r0
pop {r4, r5, pc}
'''

def install(r):
    r.cur = (r.cur + 3) & ~3
    code = r.asm(WRAPPER, r.cur)
    wrapper = r.alloc(code, 4)
    wrapper_ptr = 0x08000000 + wrapper + 1
    # Repoint the literal so jra_shoot_fix calls the wrapper
    assert struct.unpack('<I', r.b[LITERAL:LITERAL+4])[0] == OLD_SHOOT
    r.w32(LITERAL, wrapper_ptr)
    print(f'wrapper {hex(wrapper_ptr)}, literal repointed')

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    install(r)
    r.save(sys.argv[2])
    print('end', hex(r.cur))
