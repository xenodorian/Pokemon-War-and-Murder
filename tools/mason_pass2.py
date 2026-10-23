"""Mason second pass (usage: mason_pass2.py IN.gba OUT.gba), run through tools/patch.sh after mason_fix2.py.
The opening fight in Pallet Town was a direct port from CryMon and still used CryMon's nouns, which do not exist in this story: 'the Prison', 'the Weeping Army', 'Calder', and 'You're eight'.
It now speaks about the JRA and its bases, and Mason no longer spits or threatens: he stops LEAF to take her home. Also: the Oak lab line 'Of course he did' was petty, now it worries about the war.
Character: MASON is the protective one who wants LEAF to stay out of the war. Plot: Shinigami is the necromancer held in a JRA base (as in the story text), the JRA holds the roads."""
import sys,struct,os,re
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
from g3 import ENC
def e(s): return bytes(0xFE if c=='\n' else ENC[c] for c in s)
PL=b'\xfd\x01'       # the player's name
CH=[ # (old string address, new bytes without terminator)
 (0xf3f6b7, PL+e(": To the JRA base.")),
 (0xf3f6ca, e("MASON: The JRA holds every road.\nNobody walks into their base.")),
 (0xf3f777, e("MASON: You're just a kid.\nYou cannot win this war.")),
 (0xf3f7eb, e("MASON: Then I stop you here.\nI'm taking you home.")),
 (0xf3f863, e("MASON: Fine. The soldiers are\nstill out there.")),
 (0xf3f8a2, e("Mason kneels in the dirt.\nHis POKéMON won't rise.")),
 (0xf3f8d3, e("MASON: Go, then. But the JRA\nguards the road.")),
 (0xf3f90a, e("MASON: And its bases guard\nthemselves.")),
 (0xf3f953, e("MASON: You didn't need it.\nJust stay alive, LEAF.")),
 (0x16958d, None),   # Oak lab, written below as a message box pointer location
]
def install(r):
    b=r.b; n=0
    for addr,new in CH[:-1]:
        old=bytes(b[addr:b.index(b'\xff',addr)])
        assert old, hex(addr)
        refs=[m.start() for m in re.finditer(re.escape(struct.pack('<I',0x08000000+addr)),bytes(b[:0x1200000]))]
        assert refs,hex(addr)
        p=0x08000000+r.alloc(new+b'\xff',1)
        for x in refs: r.w32(x,p) if hasattr(r,'w32') else None
        n+=len(refs)
    # Oak lab: 0x16958d is the location of the pointer to 'The Professor gave you a POKéMON? Of course he did.'
    old=struct.unpack('<I',b[0x16958d:0x169591])[0]
    assert old>=0x08f00000
    b[0x16958d:0x169591]=struct.pack('<I',0x08000000+r.alloc(e("MASON: So the Professor gave you a\nPOKéMON. He should know better.")+b'\xff',1))
    # battle intro showed 'YOUNG COUPLE MASON': the rival records still carry class 52. Class 89 is RIVAL (429, 432 and 435 already use it).
    T=0x798790; MASON=e('MASON'); k=0
    for tid in range(0,760):
        o=T+40*tid
        if bytes(b[o+4:o+9])==MASON and b[o+9]==0xFF and b[o+1]==52: b[o+1]=89; k+=1
    # other trainers that the TERRY->MASON rename and the army name pool also called MASON: the soldier 311 and the two jugglers 590 and 719 (named MASON in the Outlaw ROM itself)
    for tid,new in ((311,'MALLORY'),(590,'MARCO'),(719,'MARCO')):
        o=T+40*tid+4; assert bytes(b[o:o+5])==MASON,tid
        b[o:o+12]=e(new)+b'\xff'*(12-len(new))
    print('repointed',n,'refs; rival class fixed on',k,'records')
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
