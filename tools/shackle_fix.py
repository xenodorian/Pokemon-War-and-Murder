"""Shackle prompt only for captains and the General (usage: shackle_fix.py IN.gba OUT.gba), run through tools/patch.sh.
Bug: the post-battle front script (pointer at 0x1A4ED9, 0x08F8CEC0 when written) started with `callnative shackle_check2` and then
`compare 0x800C,1; goto_if NE post`. The native stores its yes/no in GSV(12) = 0x020370D0 = script var 0x800D (VAR_RESULT), but 0x800C is
VAR_FACING (0x020370D4), so every trainer fought while the player faced DOWN (facing 1) got "Shackle this CAPTAIN with a SHACKLE BALL?" and a ball was used.
The GSV macro is only linear up to 0x800B: GSV(12) = 0x800D, GSV(13) = 0x800F (LastTalked), GSV(14) = 0x800C, GSV(15) = a plain word, not a script var.
Second mismatch: after shackle_do2 the script read `compare 0x800D,1` ('party is full' branch) but removeitem had just set 0x800D to 1, so every shackle printed the
PC message; shackle_do2 really stores its GIVE result with GSV(0xD) = 0x020370D2 = 0x800F.
Patch (2 bytes, the natives are not touched):
  1. front: `callnative shackle_check2; compare 0x800C,1` -> `compare 0x800D,1`
  2. front: `removeitem 89,1; call <do2 wrapper>; compare 0x800D,1; goto_if EQ pc` -> `compare 0x800F,1`
Located by pattern from the pointer at 0x1A4ED9, so it works after other stages edited the front script. Idempotent."""
import sys, os, re, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom

FRONT_PTR = 0x1A4ED9
CHECK2 = 0x08F8C769   # shackle_check2 (story/liberty_native.c), writes GSV(11)=0x800B and GSV(12)=0x800D

def install(r):
    b = r.b
    front = struct.unpack('<I', b[FRONT_PTR:FRONT_PTR + 4])[0] - 0x08000000
    assert 0 <= front < 0x1000000, hex(front)
    hay = bytes(b[front:front + 0x400])
    # 1. the captain gate: callnative check2; compare VAR; compare value 1; goto_if NE (cond 5)
    p1 = bytes([0x23]) + struct.pack('<I', CHECK2) + bytes([0x21])
    i = hay.find(p1)
    assert i == 0 and hay.find(p1, 1) < 0, 'front does not start with callnative shackle_check2'
    v = hay[i + 6:i + 8]
    if v == bytes([0x0C, 0x80]):
        assert hay[i + 8:i + 12] == bytes([0x01, 0x00, 0x06, 0x05]), 'gate is not compare 1; goto_if NE'
        b[front + i + 6] = 0x0D
    else:
        assert v == bytes([0x0D, 0x80]), 'unexpected gate var %s' % v.hex()
    # 2. the party-full branch after the do2 wrapper: removeitem 89,1; call W; compare VAR,1; goto_if EQ
    m = re.search(rb'\x45\x59\x00\x01\x00\x04[\x00-\xff]{3}\x08\x21([\x0d\x0f])\x80\x01\x00\x06\x01', hay)
    assert m, 'do2 result compare not found'
    assert len(re.findall(rb'\x45\x59\x00\x01\x00\x04[\x00-\xff]{3}\x08\x21[\x0d\x0f]\x80', hay)) == 1
    k = front + m.start(1)
    b[k] = 0x0F
    print('shackle_fix: front %#x gate var %s, do2 result var %s' % (0x08000000 + front, b[front + 6:front + 8].hex(), b[k:k + 2].hex()))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('ok')
