"""Bystander lines that recognize LEAF (usage: bystander_story.py IN.gba OUT.gba), run through tools/patch.sh.
Replaces old vulgar, shock-value bystander lines (drugs, sex, slurs, spam jokes) with townspeople who know LEAF: they ask her to defeat the JRA, or thank her once it is beaten.
Data: story_assets/text/bystander_story.json (ptr, the msgbox pointer locations 'at' with their map, the ask and thanks boxes). Triage by Haiku agents, reviewed by hand.
Gate: in a town map, the town's base cleared flag (0x4C0 + base index); anywhere else, FLAG_GENERAL 0x4CA (the General is beaten).
Each msgbox `0f 00 ptr 09 std` is overwritten by `goto new_script` (5 bytes) and three nops; the new script checks the flag, shows one of the two texts, and jumps back to the byte after the msgbox.
The bless/threaten menu of bystander.py is untouched: it wraps these scripts."""
import sys,os,json,struct
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
from shinigami import SB,put_script
import story_text as ST
GENERAL=0x4CA
TOWN_FLAG={(3,0):0x4C1,(3,1):0x4C2,(3,2):0x4C0,(3,3):0x4C3,(3,5):0x4C4,(3,4):0x4C5,(3,6):0x4C6,(3,10):0x4C7,(3,7):0x4C8,(3,8):0x4C9}
def install(r):
    b=r.b; data=json.load(open(os.path.join(HERE,'..','story_assets','text','bystander_story.json'))); n=0
    for e in data:
        ptr=int(e['ptr'],16); ask=ST.ptr_s(r,e['ask']); thx=ST.ptr_s(r,e['thanks'])
        done=set()
        for ref in e['refs']:
            if ref['at'] in done: continue
            done.add(ref['at'])
            k=ref['at']-2
            assert b[k]==0x0f and b[k+1]==0 and struct.unpack('<I',b[k+2:k+6])[0]==0x08000000+ptr and b[k+6]==0x09,(hex(k),e['ptr'])
            flag=TOWN_FLAG.get((ref['g'],ref['n']),GENERAL); std=b[k+7]
            S=SB(); S.raw(0x2b); S._add(struct.pack('<H',flag)); S.goto_if(1,'t')
            S.msg(ask,std); S.raw(0x05); S.ptr(0x08000000+k+8)
            S.lab('t'); S.msg(thx,std); S.raw(0x05); S.ptr(0x08000000+k+8)
            sc=0x08000000+put_script(r,S)
            b[k:k+8]=bytes([0x05])+struct.pack('<I',sc)+bytes([0,0,0]); n+=1
    print('patched',n,'msgboxes')
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
