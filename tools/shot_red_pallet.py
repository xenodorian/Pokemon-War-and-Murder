"""The Pallet base shooting ("BANG! You were shot!") gets the red screen and "The world goes red." (usage: shot_red_pallet.py IN.gba OUT.gba).
Owner rule: when the player is shot, the gunshot plays (the script already does, playse 347 before BANG!), the screen flashes red, and the text says red.
After "You were shot!" the 5 bytes `callnative karma` become a goto to a helper: red fade (retried until the battle/scene fade is idle), hold 40 frames,
then the same callnative, then back to the next command. Also "goes white." -> "goes red.  " (invisible padding) in that scene's heaven line.
Runs after death_fade.py. The other copies of the line (0xF62902, 0xF62AAF) are in two old death scripts nothing points to; left alone."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
from cry_open import SB, put_script
from g3 import ENC
import rebase_natives as RN
KARMA_CALL = bytes([0x23, 0x99, 0xae, 0xeb, 0x08])
def apply(r):
    b = bytes(r.b)
    hits = [i for i in range(len(b) - 8) if b[i:i + 5] == KARMA_CALL and b[i - 8] == 0x0f and b[i - 2:i] == b'\x09\x04'
            and 0 < struct.unpack_from('<I', b, i - 6)[0] - 0x08000000 < 0x1000000]
    shot = [i for i in hits if bytes(ENC[c] for c in 'BANG!') in b[struct.unpack_from('<I', b, i - 6)[0] - 0x08000000:][:8]]
    assert len(shot) == 1, 'Pallet shooting script not found uniquely (%s)' % [hex(x) for x in shot]
    at = shot[0]
    sc = struct.unpack_from('<I', b, RN.WHITEOUT_PTR)[0] - 0x08000000
    k = b[sc:sc + 600].find(bytes([0x05]) + struct.pack('<I', RN.CENTER_SCRIPT)); assert k > 0
    cs = struct.unpack_from('<I', b, sc + k + 6)[0] - 0x08000000
    assert b[cs] == 0x69 and b[cs + 1] == 0x23 and b[cs + 6] == 0x23, 'death script is not the death_fade.py one'
    fade = struct.unpack_from('<I', b, cs + 7)[0]
    T = SB(); T.lab('try'); T.raw(0x23); T.ptr(fade); T.cmp(0x800D, 1); T.goto_if(1, 'ok'); T.raw(0x28, 2, 0); T.goto('try')
    T.lab('ok'); T.raw(0x28, 40, 0); T.raw(0x23); T.ptr(0x08ebae99); T.raw(0x05); T.ptr(0x08000000 + at + 5)
    new = 0x08000000 + put_script(r, T)
    r.b[at:at + 5] = bytes([0x05]) + struct.pack('<I', new)
    old = bytes(ENC[c] for c in 'The world goes white.'); text = bytes(ENC[c] for c in 'The world goes red.  ')
    j = b.find(old + b'\xfb' + bytes(ENC[c] for c in 'Something warm'), struct.unpack_from('<I', b, at + 5 + 8 + 0)[0] if False else 0xf31000)
    assert 0xf31000 <= j < 0xf32000 and b.count(old, 0xf31000, 0xf32000) == 1
    r.b[j:j + len(old)] = text
    print('shot_red_pallet: karma call at %s -> helper %s, text at %s' % (hex(at), hex(new), hex(j)))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')
