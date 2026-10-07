import sys
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
HOOKAT=0x3af2b8     # free run inside bl range of the patch site
HOOK='''ldrb r0,[r2,#5]
cmp r0,#0x98
bne cont
ldr r0,[pc,#8]
bx r0
cont:
ldrb r0,[r6,#0xb]
lsls r0,r0,#0x1c
bx lr
.word 0x0806396d
'''
def apply(r):
    # DoesObjectCollideWithObjectAt (0x08063904): objects whose graphics id is the splatter (0x98) never block
    assert r.b[0x6394c:0x63950]==bytes([0xf0,0x7a,0x00,0x07])
    code=r.asm(HOOK,HOOKAT); assert len(code)==20
    r.put(HOOKAT,code)
    r.bl(0x6394c,HOOKAT)
    return HOOKAT
if __name__=='__main__':
    r=Rom(sys.argv[1]); h=apply(r); print(hex(h)); r.save(sys.argv[2])
