"""Rename the pre-existing LEAF character to TWIG (usage: rename_twig.py IN.gba OUT.gba), run through tools/patch.sh.
The protagonist is LEAF now. The Outlaw ROM already had a LEAF: the girlfriend who flirts and battles (trainers 292, 427, 436, her Trainer Tower record 515)
and her text. Found by decoding every string with LEAF in the Outlaw original and checking the same addresses in the current ROM. Same length, so it is done in place.
Not touched: move and species names with LEAF in them (RAZOR LEAF, NUZLEAF ...), the protagonist's own text, species slot 255 (the protagonist stand-in)."""
import sys,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
from g3 import ENC
LEAF=bytes(ENC[c] for c in 'LEAF'); TWIG=bytes(ENC[c] for c in 'TWIG')
TEXTS=[0x176710,0x176727,0x17a3cd,0x17ead7,0x17eb95,0x198629,0x19c235,0x71e4b8,0x71eb09,0x71ec60,0x71eea1,0x71eff5,0x71f039,0x71f056,0x71f1ae,0x71f1f2,0x71f20f]
TRAINERS=[292,427,436,515]; T=0x798790
def install(r):
    b=r.b; n=0
    for a in TEXTS:
        e=b.index(b'\xff',a); seg=bytes(b[a:e])
        assert LEAF in seg,hex(a)
        k=seg.count(LEAF); b[a:e]=seg.replace(LEAF,TWIG); n+=k
    for t in TRAINERS:
        o=T+40*t+4; assert bytes(b[o:o+4])==LEAF,t
        b[o:o+4]=TWIG; n+=1
    print('renamed',n)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2])
