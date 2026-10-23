"""Correct gvars_fix.py (usage: gvars_fix2.py IN.gba OUT.gba), run through tools/patch.sh.
gvars_fix.py assumed table positions 27..31 and 59..63 were unused. They are not: g_vars is read for bits 0..416 (shot), 417..510 (JRA shot, liberty_native), 512..928 (killed),
929..1022 (JRA blessed) and 1023 (shop price flag), so all 64 positions are live.
Pool vars that other code already owns (grep of every stage, native and script source): 0x4090..0x409C story, 0x40A2..0x40A6 quest-log backup, 0x40E0..0x40E2 army victims,
0x40E3 army coord trigger, 0x40E4 rob.c LASTTALKED (that one cleared bits 1008..1023: blessed JRA 79..93 and the shop price flag on every talk).
Those 23 positions (0..12, 17..21, 59..63) now point at vars with no reader or writer anywhere (not in the Outlaw scripts, the natives or the stage sources):
0x4029..0x402F, 0x408C..0x408F, 0x4034 0x403C 0x403F 0x4041 0x4072 0x4077 0x407A 0x4087, and the vanilla record counters 0x403D 0x4040 0x404C 0x404F.
The positions' bits restart at zero (they held story values). The existing pool lives in tools/gvars_fix.py (intermediate) and is replaced here."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
import gvars_fix as G
BAD=list(range(0,13))+list(range(17,22))+list(range(59,64))
EXT=list(range(0x4029,0x4030))+list(range(0x408C,0x4090))+[0x4034,0x403C,0x403F,0x4041,0x4072,0x4077,0x407A,0x4087]+[0x403D,0x4040,0x404C,0x404F]
def final_pool():
    OLD=G.OLD; new=list(OLD)
    assert len(EXT)==len(BAD)==23
    for i,v in zip(BAD,EXT): new[i]=v
    assert len(set(new))==64 and all(v in EXT or v in OLD for v in new)
    return new
def install(r):
    pack=lambda l: b''.join(struct.pack('<H',v) for v in l)
    old=pack(G.new_pool()); new=pack(final_pool())
    n=0; i=0
    while True:
        i=r.b.find(old,i)
        if i<0: break
        r.b[i:i+128]=new; i+=128; n+=1
    assert n==9,n
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
