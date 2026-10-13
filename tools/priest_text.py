"""The CONFESSION quest log entry no longer states the price formula (1,000 per kill, 9,999 at most). The priest names the current price himself,
so the quest log only says that he does. The entry exists three times in the ROM (the quest log table is copied); all copies are rewritten in place,
padded with spaces to the old length.
usage: priest_text.py IN.gba OUT.gba"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
from g3 import ENC
enc=lambda s: bytes(ENC[c] for c in s)
OLD_HEAD=enc('QUEST: CONFESSION')
PAGES=["QUEST: CONFESSION","GO TO: The CHURCH in PALLET\nTOWN, south of the lab.","TO DO: Talk to the PRIEST. He\nnames a price for your kills.","Pay it and your KILL COUNT\ndrops to zero."]
def text(p): return b''.join(bytes([0xFE]) if c=='\n' else bytes([ENC[c]]) for c in p)
def apply(r):
    d=r.b; body=b'\xfb'.join(text(p) for p in PAGES); n=0; i=0
    while True:
        i=d.find(OLD_HEAD+b'\xfb',i)
        if i<0: break
        j=i
        while d[j]!=0xff: j+=1
        old=bytes(d[i:j])
        assert enc('1,000 per kill') in old and len(body)<=len(old),(len(body),len(old))
        d[i:j+1]=body+bytes([0x00])*(len(old)-len(body))+b'\xff'; n+=1; i=j+1
    assert n==3,n
    return n
if __name__=='__main__':
    r=Rom(sys.argv[1]); print('copies',apply(r)); r.save(sys.argv[2])
