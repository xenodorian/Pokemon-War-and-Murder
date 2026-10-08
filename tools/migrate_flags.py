# usage: migrate_flags.py in.gba out.gba
# The Dark Spirit flags (0x3F0-0x3F9) and the Spirit Witch intro flag (0x3FA) were chosen inside the vanilla hidden-item flag block (FLAG_HIDDEN_ITEM_*), so
# picking up a hidden item changed spirit state. They move to the unused block 0x4D0-0x4DA.
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
from leg1 import r32,header
OLD=0x3F0; NEW=0x4D0; INTRO_OLD=0x3FA; INTRO_NEW=0x4DA
def mapf(f):
    if OLD<=f<OLD+10: return NEW+(f-OLD)
    if f==INTRO_OLD: return INTRO_NEW
    return None
def patch_range(b,lo,hi,counts):
    i=lo
    while i<hi-3:
        op=b[i]
        if op in (0x29,0x2a,0x2b):
            f=struct.unpack('<H',b[i+1:i+3])[0]; n=mapf(f)
            ok=False
            if n is not None:
                if op==0x29 and (b[i+3:i+6]==bytes([0x53,0x0f,0x80]) or f==INTRO_OLD): ok=True
                if op==0x2b and b[i+3:i+5]==bytes([0x06,0x01]): ok=True
            if ok:
                b[i+1:i+3]=struct.pack('<H',n); counts[(op,'intro' if f==INTRO_OLD else 'spirit')]=counts.get((op,'intro' if f==INTRO_OLD else 'spirit'),0)+1; i+=3; continue
        i+=1
if __name__=='__main__':
    r=Rom(sys.argv[1]); b=r.b; counts={}
    SPIRIT_MAPS=[(3,0),(3,1),(3,2),(3,3),(3,5),(3,4),(3,6),(3,10),(3,7),(3,8)]
    for g,n in SPIRIT_MAPS+[(3,6)]:
        h=header(r,g,n); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
        for i in range(b[ev]):
            t=po+24*i
            gfx=b[t+1]; fl=struct.unpack('<H',b[t+0x14:t+0x16])[0]; sc=struct.unpack('<I',b[t+0x10:t+0x14])[0]
            if gfx==0x9d and OLD<=fl<OLD+10:
                b[t+0x14:t+0x16]=struct.pack('<H',mapf(fl)); counts['template']=counts.get('template',0)+1
                patch_range(b,sc-0x08000000,sc-0x08000000+0x100,counts)
            if gfx in (0x9a,0x9e) and (g,n)==(3,6) and sc>=0x08a00000:
                patch_range(b,sc-0x08000000,sc-0x08000000+0x1800,counts)
    print(counts)
    assert counts.get('template',0)==10 and counts.get((0x29,'spirit'),0)==10 and counts.get((0x2b,'spirit'),0)==10,counts
    assert counts.get((0x29,'intro'),0)>=1 and counts.get((0x2b,'intro'),0)>=1,counts
    r.save(sys.argv[2])
