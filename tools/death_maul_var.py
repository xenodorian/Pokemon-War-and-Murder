"""The "mauled" line follows the killer, not the facing direction (usage: death_maul_var.py IN.gba OUT.gba), run through tools/patch.sh after police_vars.py.
death_fx_live (story/death_class_native.c) writes its mauled flag with GSV(12) = 0x020370D0, which is VAR_RESULT (0x800D), not 0x800C: the GSV macro is linear
only up to 0x800B (see shackle_fix.py). The death script from death_fade.py then (1) loops on death_fade_try, which writes VAR_RESULT and so overwrites the flag,
and (2) compares 0x800C, which is VAR_FACING. So "You were mauled to death by a pokemon." printed only when LEAF faced down, for any killer.
Fix, two words: the literal 0x020370D0 in death_fx_live's pool (ROM 0xF87474) becomes 0x020370C0 (= 0x8004, inside the linear range, not touched by the
fade loop or the continuation script at 0xF75D34, which reads 0x8007), and the compare operand in the death script (ROM 0xF873B2) becomes 0x8004."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
import rebase_natives as RN
LIT = 0xF87474; CMP = 0xF873B2; SCRIPT = 0xF87390
def install(r):
    b = r.b
    fx = RN.addrs(r)['death_fx'] & ~1; o = fx - 0x08000000
    assert bytes(b[o:o + 4]) == bytes([0x00, 0x4b, 0x18, 0x47]), 'death_class_fix trampoline missing'
    live = (struct.unpack_from('<I', b, o + 4)[0] & ~1) - 0x08000000
    assert live < LIT < live + 0x80, 'literal not in death_fx_live'
    assert struct.unpack_from('<I', b, LIT)[0] == 0x020370D0, 'literal already changed'
    # the death script: lockall, callnative death_fx, try: callnative fade, cmp 0x800D 1, goto_if, delay 2, goto try, delay 40, cmp 0x800C 1, goto_if 'm'
    assert b[SCRIPT] == 0x69 and b[SCRIPT + 1] == 0x23 and struct.unpack_from('<I', b, SCRIPT + 2)[0] == fx | 1
    assert bytes(b[CMP - 1:CMP + 4]) == bytes([0x21, 0x0C, 0x80, 0x01, 0x00]) and b[CMP - 4] == 0x28 and b[CMP + 4] == 0x06
    struct.pack_into('<I', b, LIT, 0x020370C0)
    struct.pack_into('<H', b, CMP, 0x8004)
if __name__ == '__main__':
    r = Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('ok')
