"""Police deal offer reads LIBERTY as signed (usage: deal_signed.py IN.gba OUT.gba), run through tools/patch.sh.
deal_info (gun.c, ROM 0xf22cd0) tested `liberty > 10` on the raw u16, so a negative liberty (blessing costs 1, shop markup below 0) such as -5 = 0xFFFB passed and
the officer offered the deal to a player with no standing. ldrh -> ldrsh and blo -> blt make the compare signed."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
def install(r):
    b=r.b; o=0xf22d12
    assert bytes(b[o:o+6])==bytes.fromhex('c05a0b283bd3'),bytes(b[o:o+6]).hex()
    b[o:o+6]=bytes.fromhex('c05e0b283bdb')
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
