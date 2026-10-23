"""SUPERSEDED by gvars_fix2.py (this intermediate step wrongly treated table positions 27..31 and 59..63 as unused and used army vars 0x40E0..0x40E3).
g_vars (9 compiled copies in the ROM, source stage2/data.h, pool tools/build.py VARS_POOL) maps bit>>4 to a saved var. Bits 0..416 (shot) and 512..928 (killed) are in use,
so table positions 0..26 and 32..58 are live. Positions 0..12 sat on the story vars 0x4090..0x409C (VAR_VIRI, BSTART, PARTNER, PSPECIES, PLEVEL, AMB, SOUL, SNIPE)
and positions 17..21 on 0x40A2..0x40A6 (quest-log backup after qlvars_fix). A shot-trainer write could flip a story var and a story write could mark trainers shot.
Those 18 positions now point at vars no code uses: 0x4029..0x402F, 0x408C..0x408F, 0x40BF..0x40C3 (old unused table positions 27..31), 0x40E0..0x40E3 (59..62).
Positions 27..31 and 59..63 are never read; they now hold the displaced vars. Shot marks of the 18 moved positions start empty (their old content was story values)."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
OLD=(list(range(0x4090,0x40A0))+list(range(0x40A1,0x40AA))+list(range(0x40BD,0x40CF))+list(range(0x40D0,0x40E6)))[:64]
BAD=[i for i,v in enumerate(OLD) if 0x4090<=v<=0x409C or 0x40A2<=v<=0x40A6]
SPARE=list(range(0x4029,0x4030))+list(range(0x408C,0x4090))+list(range(0x40BF,0x40C4))+list(range(0x40E0,0x40E4))
def new_pool():
    new=list(OLD); assert len(BAD)==18 and all(i<27 for i in BAD)
    spare=list(SPARE); moved=spare[:18]; left=spare[18:]
    for i,v in zip(BAD,moved): new[i]=v
    free_pos=list(range(27,32))+list(range(59,64))
    pool_left=[v for v in OLD if v not in new]
    for i,v in zip(free_pos,pool_left+left+[0x40E4]*10): new[i]=v
    assert len(set(new[:27]+new[32:59]))==54
    return new
def install(r):
    pack=lambda l: b''.join(struct.pack('<H',v) for v in l)
    old=pack(OLD); new=pack(new_pool()); assert len(old)==len(new)==128
    n=0; i=0
    while True:
        i=r.b.find(old,i)
        if i<0: break
        r.b[i:i+128]=new; i+=128; n+=1
    assert n==9,n
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
