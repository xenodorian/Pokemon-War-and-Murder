"""Mt. Moon B2F: the Rocket at (35,12) (local id 6, FLAG_HIDE_MISC_KANTO_ROCKETS) has a script pointer of 0x08000000 in the Outlaw base ROM
(the pointer was lost). Talking to him would run the ROM header as a script. The original FireRed script for this grunt (0x08160829, trainerbattle
trainer 354, intact in the Outlaw ROM) is put back. usage: mtmoon_fix.py IN.gba OUT.gba"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
r=Rom(sys.argv[1])
T=0x3ae718+24*3            # object template 4 of map (1,3) MtMoon_B2F
assert r.b[T]==6 and r.b[T+1]==0x31 and r.r32(T+16)==0x08000000, 'template changed'
assert r.b[0x160829]==0x5c, 'original script missing'
r.w32(T+16,0x08160829)
r.save(sys.argv[2]); print('mtmoon_fix: grunt script restored')
