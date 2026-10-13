"""Pallet no longer has Slums (a new game starts at home). Three lines that mentioned PALLET SLUMS are reworded; the other towns' Slums talk stays.
Each string is rewritten in place, shorter or equal, padded with spaces.
usage: slums_text.py IN.gba OUT.gba"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
from g3 import ENC
def enc(s):
    """text bytes without the terminator; \\n = line break (0xFE), \\p = line scroll (0xFA)"""
    out=bytearray(); i=0
    while i<len(s):
        if s.startswith('\\p',i): out.append(0xFA); i+=2
        elif s[i]=='\n': out.append(0xFE); i+=1
        else: out.append(ENC[s[i]]); i+=1
    return bytes(out)
EDITS=[("Go back to PALLET SLUMS!","Go back to the gutter!"),
       ("Go back to PALLET   \nSLUMS, you bum!","Go back to the gutter,\nyou bum!"),
       ("A homeless from\\pPALLET SLUMS is my only hope!","A homeless kid is\\pmy only hope!")]
def apply(r):
    d=r.b
    for old,new in EDITS:
        ob,nb=enc(old),enc(new); i=bytes(d).find(ob)
        assert i>=0 and bytes(d).find(ob,i+1)<0,old
        assert len(nb)<=len(ob),old
        d[i:i+len(ob)]=nb+bytes([0x00])*(len(ob)-len(nb))
    return len(EDITS)
if __name__=='__main__':
    r=Rom(sys.argv[1]); print('strings',apply(r)); r.save(sys.argv[2])
