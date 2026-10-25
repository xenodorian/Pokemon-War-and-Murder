"""Lt. Surge crash fix (usage: surge_fix.py IN.gba OUT.gba), run through tools/patch.sh.
Surge's object script (VermilionCity_Gym obj 1, ROM 0x16B94A) is: trainerbattle (type 1, trainer 416, continue script 0x0816B97C), checkflag
FLAG_GOT_TM34_FROM_SURGE (0x231), goto_if set -> 0x0816B9AF, then a post-battle msgbox (8 bytes: `loadword; callstd 4`, since bystander_story.py:
`goto wrapper` + 3 nops) and then, at 0x16B97A, the two bytes `04 a0`. Vanilla has `release; end` (6c 02) there; the Outlaw base lost them, so after the msgbox
the script runs `call 0x800416a0` (04 a0 16 04 80) and jumps into non-ROM memory. The bystander wrapper goes back to 0x16B97A explicitly, which turns the
undefined jump into a hard crash (undefined instruction vector, pc 0x00000008). It happens on every talk to Surge once he gave TM34 (flag 0x231 set), i.e. after every fight.
Fix: write 6c 02 (release, end) at 0x16B97A. The continue script at 0x16B97C is untouched. Located by the script pattern; idempotent."""
import sys,os,struct
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
from leg1 import r32,header
def install(r):
    b=r.b
    h=header(r,9,6); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    assert b[ev]>=1 and b[po]==1 and b[po+1]==82      # obj 1, gfx 82 (Surge)
    s=r32(r,po+16)-0x08000000
    i=s
    while b[i]!=0x5c and i<s+40: i+=1
    assert b[i]==0x5c and struct.unpack('<HH',b[i+2:i+6])==(416,0)
    j=i+18
    assert b[j:j+3]==bytes([0x2b,0x31,0x02]) and b[j+3]==0x06       # checkflag 0x231; goto_if 1
    k=j+17                                                          # end of the 8-byte msgbox (or wrapper goto + 3 nops)
    assert b[k:k+2] in (b'\x04\xa0',b'\x6c\x02'),b[k:k+2].hex()
    assert b[k+2:k+7]==bytes([0x16,0x04,0x80,0x04,0x00])           # the continue script (setvar 0x8004, 4) follows
    assert k==0x16B97A
    b[k:k+2]=b'\x6c\x02'
    print('surge: release;end written at',hex(k))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
