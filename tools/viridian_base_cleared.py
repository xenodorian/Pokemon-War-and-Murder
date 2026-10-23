"""Viridian base stays cleared once the captain is defeated, and the Viridian medal is made sure of (usage: viridian_base_cleared.py IN.gba OUT.gba).
viridian_flag_fix.py cleared the cleared flag 0x4C2 on entering the base whenever the bag had no Purple Heart (item 59), so a captain defeated
without the medal being given brought the entrance guards back ("Halt! Nobody enters JRA BASE NO. 2 without the ..."). The flag is now the truth:
entering the base never clears it, and when it is set and the Purple Heart is missing the Purple Heart is added to the bag."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import Rom
from cry_open import SB, put_script
from leg1 import header

FLAG_VIRIDIAN = 0x4C2
PURPLE_HEART = 59
OLD_SCRIPT_HEAD = bytes.fromhex('473b000100')          # checkitem 59,1 (viridian_flag_fix.py)


def apply(r):
    b = r.b
    h = header(r, 2, 71)
    tab = struct.unpack_from('<I', b, h + 8)[0] - 0x08000000
    assert b[tab] == 3, 'map 2,71 has no on-transition script'
    old = struct.unpack_from('<I', b, tab + 1)[0] - 0x08000000
    assert bytes(b[old:old + 5]) == OLD_SCRIPT_HEAD or b[old] == 0x2b, 'unexpected script at %#x: %s' % (old, bytes(b[old:old + 8]).hex())
    S = SB()
    S.chkflag(FLAG_VIRIDIAN); S.goto_if(1, 'cleared'); S.end()
    S.lab('cleared')
    S.raw(0x47, PURPLE_HEART, 0, 1, 0); S.cmp(0x800D, 1); S.goto_if(1, 'have')
    S.raw(0x44, PURPLE_HEART, 0, 1, 0)                         # additem: the captain was defeated, the medal is owed
    S.lab('have'); S.end()
    new = 0x08000000 + put_script(r, S)
    struct.pack_into('<I', b, tab + 1, new)
    print('viridian base: on-transition script %#x -> %#x (flag is kept, missing medal added)' % (0x08000000 + old, new))


if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')
