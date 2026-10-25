"""Police kill bits move off the reputation variable (usage: police_vars.py IN.gba OUT.gba), run through tools/patch.sh after trainer_menu_fix.py.
gun/gun.c keeps 29 bits (24 generated officers, trainer ids 55..78, and 5 story officers) in two consecutive vars from PVAR = 0x40E8: bits 0..15 in 0x40E8, bits 16..28 in 0x40E9.
0x40E9 is VAR_REPADJ (reputation adjustment, stored as 1000 + adjustment). Effects: shooting officer 16 or higher flipped bits of the reputation adjustment, and while the adjustment was 1000
(0b1111101000) officers 19, 21, 22, 23 and the story officers 24 and 25 read as already shot, so they were splattered from the first map load.
The three natives that use the store (pbit in police_apply, pset in pol_mark and in npc_shoot) load the byte offset of the first var from a literal, 0x000011D0 (= 0x1000 + 2 * (0x40E8 - 0x4000)),
at ROM 0xF227E0, 0xF22888 and 0xF22C64. The literal becomes the offset of var 0x401E (0x103C), so the store is 0x401E and 0x401F. Those two vars were taken out of the trainer menu's bit store
(trainer_menu_fix.py BIT_VARS stops at 0x401D). Vars 0x4018..0x401F are object graphics vars that no object template uses (templates use graphics 0xF0..0xF7 = vars 0x4010..0x4017).
Saves: officers shot before this stage come back (their bits stay in 0x40E8 / 0x40E9). Reputation values polluted by earlier police kills are not repaired."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
LITS=(0xF227E0,0xF22888,0xF22C64)
OLD=0x1000+2*(0x40E8-0x4000); NEW=0x1000+2*(0x401E-0x4000)
def install(r):
    b=r.b
    for a in LITS:
        assert struct.unpack('<I',b[a:a+4])[0]==OLD,hex(a)
        b[a:a+4]=struct.pack('<I',NEW)
    # the trainer menu store must not use the police vars
    import trainer_menu_fix as T
    assert 0x401E not in T.BIT_VARS and 0x401F not in T.BIT_VARS
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
