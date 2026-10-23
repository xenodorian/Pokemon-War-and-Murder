"""Mason town map line (usage: mason_fix2.py IN.gba OUT.gba), run through tools/patch.sh after mason_fix.py.
The scene script goes on to 'LEAF received a TOWN MAP from DAISY.', so Mason must not say he hands it over himself."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
import story_text as ST
def install(r):
    ref=0x168ef8; old=struct.unpack('<I',r.b[ref:ref+4])[0]; assert old>=0x09000000,hex(old)
    r.b[ref:ref+4]=struct.pack('<I',ST.ptr_s(r,["MASON: The Professor means well.\nHe cannot see the war coming.","MASON: DAISY has a TOWN MAP for\nyou. Use it to find home, LEAF."]))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
