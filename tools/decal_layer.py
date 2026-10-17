"""Decals (blood splatter 0x98/0x99/0xA1 and the black feather, graphics 155) always draw under the player and NPCs and never block walking.
 1) sort: SetObjectSubpriorityByElevation tail hook (0x6832E, stub at 0x3AE340, written by splat_order.py for the splatter table only) is rewritten to force
    subpriority 0xFF for the splatter image table and for the feather image table (the feather is a 16x16 object, so it sorted 8 pixels nearer than the 16x32 player and was drawn over the head).
 2) collision: the DoesObjectCollideWithObjectAt exemption stub (0x3B2300, army.py) now also exempts graphics 155, so LEAF can walk over feathers.
usage: decal_layer.py IN.gba OUT.gba"""
import sys,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
HOOK_STUB,COLL_STUB=0x3AE340,0x3B2300
GFX_TABLE=0x5F2F4; SPLAT,FEATHER=0x98,155
def apply(r):
    d=r.b
    def put(at,code):
        assert len(code)<=0x40,len(code); d[at:at+len(code)]=code
    gt=r.r32(GFX_TABLE)-0x08000000
    def images(g): return r.r32(r.r32(gt+4*g)-0x08000000+0x1C)
    A,B=images(SPLAT),images(FEATHER)
    assert (A,B)!=(0,0) and A!=B
    assert bytes(d[HOOK_STUB+0x28:HOOK_STUB+0x40])==b'\xff'*0x18 and bytes(d[COLL_STUB+0x20:COLL_STUB+0x40])==b'\xff'*0x20
    put(HOOK_STUB,r.asm(f"""
        adds r1, #0x43
        strb r2, [r1]
        subs r1, #0x43
        ldr r3, [r1, #0xC]
        ldr r2, =0x{A:x}
        cmp r3, r2
        beq hit
        ldr r2, =0x{B:x}
        cmp r3, r2
        bne done
      hit:
        adds r1, #0x43
        movs r2, #0xFF
        strb r2, [r1]
      done:
        bx lr
    """,HOOK_STUB))
    put(COLL_STUB,r.asm(f"""
        ldrb r0, [r2, #5]
        cmp r0, #0xA1
        beq exempt
        cmp r0, #{FEATHER}
        beq exempt
        subs r0, #0x98
        cmp r0, #1
        bhi normal
      exempt:
        ldr r0, =0x0806396d
        bx r0
      normal:
        ldrb r0, [r6, #0xb]
        lsls r0, r0, #0x1c
        bx lr
    """,COLL_STUB))
    print('decal tables',hex(A),hex(B))
if __name__=='__main__':
    r=Rom(sys.argv[1]); apply(r); r.save(sys.argv[2])
