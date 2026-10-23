"""Gym leader defeat guard (usage: gym_guard.py IN.gba OUT.gba), run through tools/patch.sh.
Each gym leader script is `trainerbattle type 1 (continue script)`: if the leader's trainer flag (0x500 + trainer id) is already set the battle is skipped and the
continue script runs at once, which sets FLAG_DEFEATED_<leader> and the badge. So any stray write of that one trainer flag hands out the badge and shows the leader as defeated.
Audit result (every ROM script, every native, every stage source): the only writers of the leader trainer flags, DEFEATED flags 0x4B0..0x4B7 and badges 0x820..0x827 are the leaders' own win scripts.
Guard: the trainerbattle opcode of each leader (8 scripts, 18 bytes each) is replaced by a goto to a new script that, when the badge is NOT owned, clears the trainer flag, then runs the
original trainerbattle record (copied byte for byte) and goes on at the old next opcode. A stray flag can no longer skip the fight; a real win sets the badge in the same visit."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
from shinigami import SB,put_script
LEADERS=[(0x16a5a0,414,0x820),(0x16aaae,415,0x821),(0x16b957,416,0x822),(0x16d06e,417,0x823),(0x16d55b,418,0x824),(0x16ede5,420,0x825),(0x16d9e1,419,0x826),(0x169ed7,350,0x827)]
def install(r):
    b=r.b
    for a,tid,badge in LEADERS:
        assert b[a]==0x5c and b[a+1]==1 and struct.unpack('<H',b[a+2:a+4])[0]==tid,hex(a)
        rec=bytes(b[a:a+18]); nxt=0x08000000+a+18
        S=SB(); S.raw(0x2b); S._add(struct.pack('<H',badge)); S.goto_if(1,'go')
        S.clearflag(0x500+tid)
        S.lab('go'); S._add(rec); S.raw(0x05); S.ptr(nxt)
        new=0x08000000+put_script(r,S)
        b[a]=0x05; b[a+1:a+5]=struct.pack('<I',new)
        b[a+5:a+18]=bytes([0x00])*13       # unreachable filler (nop)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
