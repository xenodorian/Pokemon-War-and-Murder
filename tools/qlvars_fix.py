"""Stop the vanilla quest-log backup from overwriting our saved vars (usage: qlvars_fix.py IN.gba OUT.gba), run through tools/patch.sh.
On every map load the vanilla routines at 0x08110D94 / 0x08110E20 (and the restore twins at 0x081116xx / 0x08111708) write 4 trainer-rematch vars at 0x40AA..0x40AD
and the map layout id to 0x40AE. That zeroed LIBERTY (0x40AC), the police deal state (0x40AB), Hall of Justice species slot 0 (0x40AD) and the REMAP mask (0x40AE).
The literals are moved to the unused vars 0x40A2..0x40A5 (rematch array) and 0x40A6 (layout)."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
def install(r):
    b=r.b
    for o,old,new in ((0x110E1C,0x40AA,0x40A2),(0x1116D4,0x40AA,0x40A2),(0x110E34,0x40AE,0x40A6),(0x111754,0x40AE,0x40A6)):
        assert struct.unpack('<I',b[o:o+4])[0]==old,hex(o)
        b[o:o+4]=struct.pack('<I',new)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
