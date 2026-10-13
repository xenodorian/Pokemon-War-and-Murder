"""Blood splatter draw order. The splatter (graphics 0x98, 0x99 and 0xA1, one shared image table) is sorted among the other sprites by the same
SetObjectSubpriorityByElevation as the player: its subpriority is derived from its y position, so which one is drawn on top depended on the direction
the player came from. The sprite subpriority of anything that uses the splatter image table is now forced to 0xFF (behind every other object), so the splatter is
always over the ground tiles and under the player and every NPC.
usage: splat_order.py IN.gba OUT.gba"""
import sys,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
SET_SUBPRIO_TAIL=0x6832E        # adds r1,#0x43 ; strb r2,[r1]   in SetObjectSubpriorityByElevation
STUB_AT=0x3AE340                # free run within BL range
GFX_TABLE,GFX_COUNT,SPLAT_GFX=0x5F2F4,0x5F2E0,0x98
def apply(r):
    d=r.b
    assert bytes(d[SET_SUBPRIO_TAIL:SET_SUBPRIO_TAIL+4])==bytes([0x43,0x31,0x0A,0x70]),bytes(d[SET_SUBPRIO_TAIL:SET_SUBPRIO_TAIL+4]).hex()
    gt=r.r32(GFX_TABLE)-0x08000000
    info=r.r32(gt+4*SPLAT_GFX)-0x08000000
    images=r.r32(info+0x1C)                 # image table pointer shared by every splatter graphics id
    src=f"""
        adds r1, #0x43
        strb r2, [r1]
        subs r1, #0x43
        ldr r3, [r1, #0xC]
        ldr r2, =0x{images:x}
        cmp r3, r2
        bne done
        adds r1, #0x43
        movs r2, #0xFF
        strb r2, [r1]
      done:
        bx lr
    """
    code=r.asm(src,STUB_AT); r.put(STUB_AT,code)
    r.bl(SET_SUBPRIO_TAIL,STUB_AT)
    return images
if __name__=='__main__':
    r=Rom(sys.argv[1]); im=apply(r); r.save(sys.argv[2]); print('splat image table',hex(im))
