# Fixes the dropped last letter of text boxes at the fastest text speed.
# usage: text_flush.py IN.gba OUT.gba
# Cause: the Outlaw base hooks RenderFont (bl at 0x08002e00 in RunTextPrinters -> 0x083af270 -> 0x08a03699).
# At text speed 3 it calls RenderFont twice per frame and returns the second result. When the first call
# draws a glyph (0) and the second hits the end of the string or a button wait (3 or 1), RunTextPrinters
# gets a non-zero result and skips CopyWindowToVram, so that glyph is drawn into the window buffer but
# never reaches VRAM. It hits every string whose last glyph before a stop is the first of a pair
# (stock and custom text alike), e.g. "The army is at our gates, father." showed without the full stop.
# Fix: same two calls, but if a glyph was drawn this frame and the printer then stopped, copy the window
# to VRAM (CopyWindowToVram(windowId, COPYWIN_GFX)) before returning. Strings are not changed.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inc import Rom

HOOK_LIT = 0x3af274           # literal of the 0x083af270 trampoline (was 0x08a03699, the Outlaw double-speed routine)
OLD = 0x08a03699

def apply(r):
    assert r.r32(HOOK_LIT) == OLD, 'text hook already patched or unexpected: %x' % r.r32(HOOK_LIT)
    a = r.fn("""
        push {r4, r5, r6, lr}
        adds r4, r0, #0
        ldr r1, =0x0300500c
        ldr r1, [r1]
        ldrb r1, [r1, #0x14]
        lsls r1, r1, #29
        lsrs r1, r1, #29
        cmp r1, #3
        bne normal
        movs r6, #0
        movs r5, #2
    loop:
        movs r0, #0
        strb r0, [r4, #0x1e]
        adds r0, r4, #0
        ldr r1, =0x08002e7d
        bl callr1
        cmp r0, #0
        bne stop
        movs r6, #1
        subs r5, #1
        bne loop
        b ret
    stop:
        cmp r6, #0
        beq ret
        adds r5, r0, #0
        ldrb r0, [r4, #4]
        movs r1, #2
        ldr r2, =0x08003f21
        bl callr2
        adds r0, r5, #0
        b ret
    normal:
        adds r0, r4, #0
        ldr r1, =0x08002e7d
        bl callr1
    ret:
        pop {r4, r5, r6}
        pop {r1}
        bx r1
    callr1:
        bx r1
    callr2:
        bx r2
    """)
    r.w32(HOOK_LIT, 0x08000001 + a)
    print('text flush at', hex(0x08000000 + a))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2])
