"""Mason's overworld sprite in Cerulean and Silph Co (usage: mason_gfx.py IN.gba OUT.gba), run through tools/patch.sh.
The Cerulean (3,3) and Silph Co rival objects (hide flags FLAG_HIDE_CERULEAN_RIVAL 0x3C and FLAG_HIDE_SILPH_RIVAL 0x4E) carried gfx 7, the base hack's girlfriend, which
looks like LEAF. Every other rival object (SS Anne, Tower, Route 22, lab) uses gfx 72, the Gary sprite. Those two objects now use gfx 72 as well."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
HIDE={0x3C,0x4E}; OLD,NEW=7,72
TARGETS=((1,53,1),(3,3,8))     # SilphCo_7F object 1, CeruleanCity object 8
def install(r):
    b=r.b; r32=lambda o: struct.unpack('<I',b[o:o+4])[0]
    for g,m,obj in TARGETS:
        gp=r32(0x3526A8+4*g)-0x08000000; mp=r32(gp+4*m)-0x08000000
        ev=r32(mp+4)-0x08000000; po=r32(ev+4)-0x08000000; o=po+24*(obj-1)
        assert b[o]==obj and b[o+1]==OLD and struct.unpack('<H',b[o+20:o+22])[0] in HIDE,(g,m)
        b[o+1]=NEW
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
