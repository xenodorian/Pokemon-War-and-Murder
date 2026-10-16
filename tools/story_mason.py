"""MASON is the rival everywhere (usage: story_mason.py IN.gba OUT.gba), owner spec 2026-10-16.
Every stock rival encounter of the ROM (SS Anne 426, Pokemon Tower 429, Route 22 early 332 and late 435, Cerulean 333, Silph 432, Oak's lab scenes, the Sevii and Route 22 talks) now has MASON
trying to stop LEAF from going to war with Johto and to bring her home safe. His battle records are all named MASON (Cerulean and Silph, which the base hack gave to a LEAF girlfriend character,
become MASON records with the same parties). A lost battle against any MASON record never white-outs nor visits the afterlife (native max_after + MASON_KO_SCRIPT in story_native)."""
import sys,struct,os,textwrap
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from inc import *
import story_text as ST
from leg1 import enc
T_TABLE=0x798790
def boxes(paras,w=33):
    out=[]
    for p in paras:
        ls=[]
        for part in p.split('\n'): ls+=textwrap.wrap(part,w)
        for i in range(0,len(ls),2): out.append('\n'.join(ls[i:i+2]))
    return out
def msg(r,*paras): return ST.ptr_s(r,boxes(paras))
def bt(r,t):
    assert len(t.split('\n'))<=2 and all(len(l)<=30 for l in t.split('\n')),t
    return ST.battle_ptr(r,t)
# (pointer location, kind, text) kind m = message box paragraphs, b = battle text (single box)
TEXTS=[
 # Route 22 early (script 0x16836d, mode 9: defeat text then the text for a MASON win)
 (0x1682ed,'m',["MASON: LEAF. Stop right there. I've been looking for you since Pallet.","MASON: I know what you are doing. You want to march on the Johto army. They will kill you.","MASON: I am not letting you go. If I have to put you on the ground to get you home, I will."]),
 (0x168316,'m',["MASON: You won this time.","MASON: Next time I will not ask. Go home, LEAF. Please."]),
 ((0x168373,0x168382,0x168391),'b',"MASON: Not yet. I won't stop\ntrying, LEAF."),
 ((0x168377,0x168386,0x168395),'b',"MASON: Stay down. I'm taking\nyou home."),
 # SS Anne (426)
 (0x160945,'m',["MASON: LEAF. I followed you aboard. Don't look at me like that.","MASON: The Johto army is not a game. Max is already out there bleeding for it.","MASON: Turn around. I'm taking you home, and I'll carry you if I have to."]),
 (0x160973,'m',["MASON: You don't understand. I am not your enemy.","MASON: Whatever you do next, I'll be right behind you, trying to stop you."]),
 ((0x1609e2,0x1609ed,0x1609f8),'b',"MASON: Not done. I'll keep\nstopping you, LEAF."),
 # Pokemon Tower (429)
 (0x1632d9,'m',["MASON: LEAF. This place is full of graves. I don't want yours here.","MASON: Soldiers burn what they don't steal. You cannot fight that.","MASON: Come home. Please. Don't make me fight you again."]),
 (0x163307,'m',["MASON: You keep winning, and it keeps scaring me.","MASON: Somebody has to be the one who says stop. I'll keep saying it."]),
 ((0x163363,0x16336e,0x163379),'b',"MASON: You win. I'm still not\nletting go."),
 # Route 22 late (435)
 (0x16844b,'m',["MASON: LEAF. This is the last road to the war. The Johto army waits past this gate.","MASON: I'm done asking. Lose to me here, and you wake up safe at home."]),
 (0x168479,'m',["MASON: ...You really mean to do it.","MASON: Then I'll be there when it goes wrong. Go. And stay alive."]),
 ((0x1684bf,0x1684ca,0x1684d5),'b',"MASON: Then go. Just stay\nalive, LEAF."),
 # Cerulean (333)
 (0x1664e2,'m',["MASON: LEAF. Stop. I heard where you are headed.","MASON: Johto soldiers shot a kid in Viridian. You cannot take that army on.","MASON: I am bringing you home. Safe. Whether you like it or not."]),
 (0x16651d,'m',["MASON: You really are going to do this.","MASON: Then listen. The soldiers do not take prisoners. Not from us."]),
 (0x166547,'m',["MASON: One more thing. Take this. Don't make me regret it."]),
 (0x166563,'m',["It's a RARE CANDY. It might keep you alive.","MASON: Come home when you can."]),
 ((0x166588,0x166593,0x16659e),'b',"MASON: Fine. But I'll keep\nfollowing you."),
 # Silph Co (432)
 (0x1619f3,'m',["MASON: LEAF. This building is crawling with Rocket men and Johto soldiers.","MASON: You have no business in here. I'm taking you out, one way or another."]),
 (0x161a11,'m',["MASON: Last chance. Walk out with me, or I make you."]),
 (0x161a3f,'m',["MASON: Look at yourself. You're shaking.","MASON: The boss and the president are up ahead, and soldiers behind them.","MASON: I won't stop you from here. But I'll never stop trying to bring you home."]),
 ((0x161a86,0x161a91,0x161a9c),'b',"MASON: You're too stubborn.\nI'll see you soon."),
 # Sevii and the Route 22 talk
 (0x167d20,'m',["MASON: LEAF. Even out here?","MASON: The war isn't yours to fight. I'm still trying to get you home.","MASON: I'll keep after you. Be careful."]),
 (0x171dcb,'m',["MASON: LEAF. How far will you take this?","MASON: I cannot stop you by talking. I tried.","MASON: So I'll keep trying. Come home when you've had enough."]),
 # Oak's lab scenes
 (0x16906c,'m',["MASON: Hold on, Professor. You are sending LEAF out there?","MASON: She is a kid. The war is no place for her."]),
 (0x169132,'m',["MASON: ...Fine. I'll keep an eye on her. Someone has to."]),
 (0x169648,'m',["MASON: Professor!"]),
 (0x16967e,'m',["MASON: Why did you call me over, Professor?"]),
 (0x1697b9,'m',["MASON: I don't like this. But I'll look after her."]),
 (0x16926f,'m',["MASON: These are for the road. I'm taking them with me."]),
 (0x16929b,'m',["MASON: No. I'm not leaving her side."]),
 (0x169579,'m',["MASON: Don't touch those. They are not toys, LEAF."]),
 (0x169583,'m',["MASON: I won't risk them in a fight with you. Not today."]),
 (0x16958d,'m',["MASON: The Professor gave you a POKéMON? Of course he did."]),
 (0x1694c7,'m',["FEMALE AIDE: I will still protest!\nOAK: No one cares.","MASON: I'm going after LEAF. Someone has to."]),
]
def install(r):
    n=0
    for loc,kind,t in TEXTS:
        locs=loc if isinstance(loc,tuple) else (loc,)
        p=msg(r,*t) if kind=='m' else bt(r,t)
        for a in locs:
            old=r32(r,a); assert 0x08100000<=old<0x08f50000,hex(a)
            r.w32(a,p); n+=1
    # Cerulean (333) and Silph (432): the base hack's LEAF girlfriend records become MASON (class RIVAL, Gary picture), parties kept
    for tid,cls in ((333,81),(432,89)):
        o=T_TABLE+40*tid; e=r.b
        e[o+1]=cls; e[o+2]=0; e[o+3]=106 if cls==81 else 124
        nm=enc('MASON')[:-1]; e[o+4:o+16]=nm+b'\xff'*(12-len(nm))
    if os.environ.get('MASON_TEST_LV'):      # TEST ONLY: raise every MASON party to this level so a test can lose to him; never set for a release build
        for tid in list(range(326,335))+[426,429,432,435,743]:
            o=T_TABLE+40*tid; cnt=struct.unpack('<I',bytes(r.b[o+32:o+36]))[0]; pp=struct.unpack('<I',bytes(r.b[o+36:o+40]))[0]-0x08000000
            for k in range(cnt): r.b[pp+8*k+2]=int(os.environ['MASON_TEST_LV']); r.b[pp+8*k+4:pp+8*k+6]=struct.pack('<H',int(os.environ.get('MASON_TEST_SPECIES',r.b[pp+8*k+4])))
    print('mason texts',n)
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
