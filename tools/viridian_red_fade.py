"""Restore the red screen before the afterlife in the Viridian arrest loss (usage: viridian_red_fade.py IN.gba OUT.gba).
The old chain build did this (owner task 1) and the rebuild on the personal ROM lost it. In the loss script, right after "You were shot!" the six bytes
`setflag 0x848; setflag 0x86C` are replaced by a goto to a short script: retry the red fade (death_fade_try, from death_fade.py) until it starts,
hold 40 frames, set the same two flags, goto the original next command. Runs after death_fade.py."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
from cry_open import SB, put_script
import rebase_natives as RN
SITE = bytes([0x29, 0x48, 0x08, 0x29, 0x6c, 0x08, 0x16, 0x97, 0x40, 0x01, 0x00, 0x23])
def apply(r):
    b = bytes(r.b)
    assert b.count(SITE) == 1, 'Viridian loss script not found uniquely (%d)' % b.count(SITE)
    at = b.find(SITE); assert b[at - 2:at] == bytes([0x09, 0x04]), 'not right after a message'
    sc = struct.unpack_from('<I', b, RN.WHITEOUT_PTR)[0] - 0x08000000
    k = b[sc:sc + 600].find(bytes([0x05]) + struct.pack('<I', RN.CENTER_SCRIPT)); assert k > 0
    cs = struct.unpack_from('<I', b, sc + k + 6)[0] - 0x08000000
    assert b[cs] == 0x69 and b[cs + 1] == 0x23 and b[cs + 6] == 0x23, 'death script is not the death_fade.py one'
    fade = struct.unpack_from('<I', b, cs + 7)[0]
    cont = 0x08000000 + at + 6
    T = SB(); T.lab('try'); T.raw(0x23); T.ptr(fade); T.cmp(0x800D, 1); T.goto_if(1, 'ok'); T.raw(0x28, 2, 0); T.goto('try')
    T.lab('ok'); T.raw(0x28, 40, 0); T.setflag(0x848); T.setflag(0x86c); T.raw(0x05); T.ptr(cont)
    new = 0x08000000 + put_script(r, T)
    r.b[at:at + 6] = bytes([0x05]) + struct.pack('<I', new) + bytes([0x00])[:1]
    r.b[at + 5] = 0x00                                   # the 6th byte is never reached (goto), keep it a harmless nop
    print('viridian_red_fade: loss script patched at %s, helper script %s' % (hex(at), hex(new)))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')
