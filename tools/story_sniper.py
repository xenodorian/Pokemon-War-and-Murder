"""MAX is shot by a sniper at the final base (usage: story_sniper.py IN.gba OUT.gba), owner spec 2026-10-16.
Final base = Nero's camp, map (2,79) (tools/story_nero.py CAMP). Stepping onto the first row of the camp (y 15, any x) while MAX is alive (F_VWON, not F_MAXDEAD) and VAR_SNIPE == 0:
 MAX stands in the camp waiting for LEAF (she says nothing), a shot rings out, she falls and stays as a blood splatter (F_MAXDEAD, VAR_SNIPE = 2), a box explains it, then LEAF walks to the sniper
 (a scripted walk to the gap at x 23, up to y 10, left to the sniper at (3,10)), calls him a child murderer and the battle starts (trainer SNIPER, JRA, Lv 45..48).
 A lost fight follows the normal run mode rules; talking to the sniper again restarts the fight. After the win he flees (F_SNIPEDONE) and the splatter stays."""
import sys,struct,os
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from inc import *
from leg1 import r32,header,enc
from shinigami import SB,put_script,add_obj,add_coord
import story_ids as I, story_text as ST
import story_viridian as V
from story_afterlife import add_mapscript
G,N=2,79
ROW=15; MAXSPOT=(15,13); SNIPER_SPOT=(3,10); GAP_X=23
def trainer(r):
    b=r.b; tid=None
    for t in range(700,760):
        e=b[V.T_TABLE+40*t:V.T_TABLE+40*t+40]
        if e[4]==0xFF and struct.unpack('<I',e[36:40])[0] in (0,0xFFFFFFFF): tid=t; break
    assert tid
    e=bytearray(b[V.T_TABLE+40*326:V.T_TABLE+40*327])
    e[0]=0; e[1]=V.CLS_SOLDIER; e[2]=0; e[3]=V.PIC_SOLDIER
    nm=enc('SNIPER')[:-1]; e[4:16]=nm+b'\xff'*(12-len(nm)); e[16:28]=bytes(12)
    e[24:28]=struct.pack('<I',0)
    lv=int(os.environ.get('SNIPER_LV','0'))      # TEST ONLY
    team=[(212,47),(142,46),(215,45),(248,48)]
    e[32:36]=struct.pack('<I',len(team))
    party=b''.join(struct.pack('<HBBHH',0,lv or L,0,sp,0) for sp,L in team)
    e[36:40]=struct.pack('<I',0x08000000+r.alloc(party,4))
    b[V.T_TABLE+40*tid:V.T_TABLE+40*tid+40]=e
    return tid
def install(r):
    T=lambda t: ST.ptr_s(r,V.wrap(t))
    tid=trainer(r)
    M=add_obj(r,G,N,MAXSPOT[0],MAXSPOT[1],V.GFX_GIRL,0,0,I.HIDE_SMAX)
    SPL=add_obj(r,G,N,MAXSPOT[0],MAXSPOT[1],V.GFX_SPLAT,0,0,I.HIDE_SSPL)
    # ---- the sniper: fight script (also the object's talk script)
    S=add_obj(r,G,N,SNIPER_SPOT[0],SNIPER_SPOT[1],V.GFX_SOLDIER,0,0,I.HIDE_SNIPER)
    Fi2=SB()
    Fi2.lock(); Fi2.faceplayer()
    Fi2.raw(0x5c,1); Fi2._add(struct.pack('<HH',tid,0)); Fi2.ptr(T(["SNIPER: You shouldn't have come this far.\nA soldier does his job."])); Fi2.ptr(ST.battle_ptr(r,"SNIPER: ...Not today.")); Fi2.ref('won')
    Fi2.msg(T(["SNIPER: ...Nothing left to say."]),4); Fi2.release(); Fi2.end()
    Fi2.lab('won')
    Fi2.msg(T(["SNIPER: The Commander will hear of this. Run while you can.","The sniper drops his rifle and runs."]),4)
    Fi2.setflag(I.F_SNIPEDONE); Fi2.setflag(I.HIDE_SNIPER); Fi2.removeobject(S); Fi2.release(); Fi2.end()
    fight=0x08000000+put_script(r,Fi2)
    # the sniper object's talk script is the fight (patch the object template)
    h=header(r,G,N); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    for i in range(r.b[ev]):
        if r.b[po+24*i]==S: r.w32(po+24*i+16,fight)
    # ---- the shared scene part 1: MAX waits, the shot
    C1=SB()
    C1.clearflag(I.HIDE_SMAX); C1.addobject(M)
    C1.msg(T(["A girl stands alone in the middle of the camp, waiting for you. It is Max.","She does not say a word."]),4)
    C1.playse(V.SE_SHOT); C1.raw(0x30)
    C1.setflag(I.HIDE_SMAX); C1.removeobject(M); C1.clearflag(I.HIDE_SSPL); C1.addobject(SPL)
    C1.setflag(I.F_MAXDEAD); C1.setvar(I.VAR_SNIPE,2)
    C1.msg(T(["A sniper on the camp wall fired. Max was hit in the chest and fell.","She does not get up. She is a blood splatter on the ground now."]),4)
    C1.raw(0x68)
    C1.raw(0x03)       # return
    call1=0x08000000+put_script(r,C1)
    # part 2: the sniper steps into view, LEAF's lines, the fight
    C2=SB()
    C2.clearflag(I.HIDE_SNIPER); C2.addobject(S)
    C2.msg(T(["LEAF: You shot a child."]),4)
    C2.msg(T(["LEAF: You're a child murderer."]),4)
    C2.msg(T(["SNIPER: She carried a rifle in a war. That makes her a soldier.","SNIPER: I only did what I was ordered to do."]),4)
    C2.raw(0x04); C2.ptr(fight); C2.releaseall(); C2.end()
    scene2=0x08000000+put_script(r,C2)
    # ---- per-x triggers on the first row of the camp
    walk_tail=V.mv(r,*([UP]*(ROW-10)+[LEFT]*(GAP_X-SNIPER_SPOT[0]-1)))
    for x in range(0,30):
        sc=SB()
        sc.lockall(); sc.setvar(I.VAR_SNIPE,1)
        sc.raw(0x2b); sc._add(struct.pack('<H',I.F_VWON)); sc.goto_if(0,'no')
        sc.raw(0x2b); sc._add(struct.pack('<H',I.F_MAXDEAD)); sc.goto_if(1,'no')
        sc.raw(0x04); sc.ptr(call1)
        if x!=GAP_X:
            sc.applymovement(0xFF,V.mv(r,*([RIGHT if x<GAP_X else LEFT]*abs(GAP_X-x)))); sc.waitmovement(0xFF)
        sc.applymovement(0xFF,walk_tail); sc.waitmovement(0xFF)
        sc.raw(0x05); sc.ptr(scene2)
        sc.lab('no'); sc.releaseall(); sc.end()
        a=0x08000000+put_script(r,sc)
        add_coord(r,G,N,x,ROW,I.VAR_SNIPE,0,a)
    ev=r32(r,h+4)-0x08000000; cp=r32(r,ev+12)-0x08000000
    for k in range(r.b[ev+2]):
        if struct.unpack('<HH',r.b[cp+16*k:cp+16*k+4])[1]==ROW and r.b[cp+16*k+4]==3: r.b[cp+16*k+4]=0
    # ---- map load: Max and the sniper only exist during the scene, the splatter stays once she died
    L=SB()
    L.setflag(I.HIDE_SMAX)
    L.compare(I.VAR_SNIPE,2); L.goto_if(1,'dead'); L.setflag(I.HIDE_SSPL); L.setflag(I.HIDE_SNIPER); L.end()
    L.lab('dead'); L.clearflag(I.HIDE_SSPL)
    L.raw(0x2b); L._add(struct.pack('<H',I.F_SNIPEDONE)); L.goto_if(1,'gone'); L.clearflag(I.HIDE_SNIPER); L.end()
    L.lab('gone'); L.setflag(I.HIDE_SNIPER); L.end()
    add_mapscript(r,G,N,3,0x08000000+put_script(r,L))
    print('sniper trainer',tid,'objects',M,SPL,S)
UP,LEFT,RIGHT=V.UP,V.LEFT,V.RIGHT
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
