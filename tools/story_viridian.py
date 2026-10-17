"""Viridian City arrest scene (usage: story_viridian.py IN.gba OUT.gba)
 - Map (3,1). Stepping onto the road from Route 1 (tiles (22..25,36)) while VAR_VIRI == 0 starts the scene: two soldiers escort MAX (girl sprite 17) across the grass at y 33; she shouts.
 - Talking to MAX or either soldier starts a DOUBLE battle (one trainer record holds both soldiers' 3 + 3 POKEMON). MAX's PIKACHU (Lv 10) is put into party slot 1 for the fight (native viri_prepare / viri_cleanup).
 - The battle is run as an 'early rival' battle (mode 9, HEAL_AFTER): a loss heals the party and carries on with the script instead of a white-out.
 - Win: soldier 2 shoots himself (splatter, GLOCK pickup once), soldier 1 runs off, MAX thanks you with an EXP SHARE and leaves. Loss: soldier 2 shoots MAX (splatter stays) and the player; Heaven or Hell by reputation."""
import sys,struct,os
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from inc import *
from leg1 import r32,header,enc
from shinigami import SB,put_script,add_obj,add_coord
import story_ids as I
import story_text as ST
import story_native as SN
import story_viri_native as SV
G,N=3,1
GFX_GIRL,GFX_SOLDIER,GFX_SPLAT,GFX_BALL=17,60,0x98,92
RESULT=0x800D
T_TABLE=0x798790; CLS_SOLDIER,PIC_SOLDIER=48,64
SPOT_S1,SPOT_M,SPOT_S2=(22,33),(23,33),(24,33)      # stopped positions (the object templates)
SPOT_GUN=(25,33)                                   # the dropped GLOCK, on the tile beside the splatter
START_DX=7                                         # they walk in from 7 tiles to the right
ITEM_EXP_SHARE,ITEM_GLOCK=182,52
SE_SHOT=347
LEFT,UP,DOWN,RIGHT=0x12,0x11,0x10,0x13
def wrap(paras):
    import textwrap
    out=[]
    for p in paras:
        ls=textwrap.wrap(p,33)
        for i in range(0,len(ls),2): out.append('\n'.join(ls[i:i+2]))
    return out
def mv(r,*b): return 0x08000000+r.alloc(bytes(b)+b'\xfe',1)
def callnative(S,fn): S.raw(0x23); S.ptr(fn)
def trainer(r):
    b=r.b
    tid=None
    for t in range(700,760):
        e=b[T_TABLE+40*t:T_TABLE+40*t+40]
        if e[4]==0xFF and struct.unpack('<I',e[36:40])[0] in (0,0xFFFFFFFF): tid=t; break
    assert tid
    e=bytearray(b[T_TABLE+40*326:T_TABLE+40*327])
    e[0]=0; e[1]=CLS_SOLDIER; e[2]=0; e[3]=PIC_SOLDIER
    nm=enc('ESCORT')[:-1]; e[4:16]=nm+b'\xff'*(12-len(nm)); e[16:28]=bytes(12)
    e[24:28]=struct.pack('<I',1)                     # doubleBattle
    LV=int(os.environ.get('VIRI_LEVEL','5'))     # TEST ONLY: VIRI_LEVEL raises the soldiers' level to test the loss branch; never set for a release build
    team=[158,7,155,4,152,1]                          # soldier 1: Totodile, Cyndaquil, Chikorita; soldier 2: Squirtle, Charmander, Bulbasaur (interleaved so each leads)
    e[32:36]=struct.pack('<I',len(team))
    party=b''.join(struct.pack('<HBBHH',0,LV,0,sp,0) for sp in team)
    e[36:40]=struct.pack('<I',0x08000000+r.alloc(party,4))
    b[T_TABLE+40*tid:T_TABLE+40*tid+40]=e
    return tid
def fix_tutorial_check(r):
    """StartTrainerBattle sets BATTLE_TYPE_FIRST_BATTLE (Oak's tutorial prompts, no running) when (rival flags & 3) != 0, so HEAL_AFTER (1) alone also turned it on. Compare with == 3 instead."""
    a=0x8047c
    assert bytes(r.b[a:a+8])==bytes.fromhex('0321'+'0140'+'0029'+'03d0'),bytes(r.b[a:a+8]).hex()
    r.b[a:a+8]=bytes.fromhex('0328'+'c046'+'c046'+'03d1')       # cmp r0,#3; nop; nop; bne (skip the flag)
def install(r):
    fix_tutorial_check(r)
    nat=SN.addrs(r); nat2=SV.addrs2(r)
    h=header(r,G,N); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    nid=max(r.b[po+24*i] for i in range(r.b[ev]))+1
    S1,M,S2,SPL2,SPLM,GUN=nid,nid+1,nid+2,nid+3,nid+4,nid+5
    tid=trainer(r)
    T=lambda s: ST.ptr_s(r,wrap(s))
    # ---- the fight (shared by MAX and both soldiers)
    F=SB(); F.lockall()
    if os.environ.get('VIRI_FORCE'):      # TEST ONLY: VIRI_FORCE=win|lose skips the battle and sets the result; never set for a release build
        F.setvar(RESULT,1 if os.environ['VIRI_FORCE']=='lose' else 0)
    else:
        callnative(F,nat2['viri_prepare'])
        # trainerbattle mode 9 (early rival): id, flags (1 = heal and carry on after a loss), defeat text, victory text (the script simply carries on after the command)
        F.raw(0x5c,9); F._add(struct.pack('<HH',tid,1)); F.ptr(ST.battle_ptr(r,"Tch. We lost.")); F.ptr(ST.battle_ptr(r,"Target neutralized."))
        callnative(F,nat2['viri_cleanup'])
    F.msg(T(["Max stares at the soldier in\nsilence. She does not say a word."]),4)
    F.msg(T(["SOLDIER: A child could never understand the burdens of a soldier."]),4)
    F.compare(RESULT,1); F.goto_if(1,'lost')
    # ---- win
    F.playse(SE_SHOT); F.raw(0x30)
    F.setflag(I.HIDE_VS2); F.removeobject(S2); F.clearflag(I.HIDE_VSPL2); F.addobject(SPL2); F.clearflag(I.HIDE_VGUN); F.addobject(GUN)
    F.msg(T(["SOLDIER: Arceus in heaven, he actually shot himself! I have to alert the captain!"]),4)
    F.applymovement(S1,mv(r,*([UP]*7))); F.waitmovement(S1)
    F.setflag(I.HIDE_VS1); F.removeobject(S1)
    F.msg(T(["Max looks at the body, then at you.\nShe says nothing.","She presses an EXP. SHARE into\nyour hand and turns away."]),4)
    F.giveitem(ITEM_EXP_SHARE)
    F.applymovement(M,mv(r,*([LEFT]*7))); F.waitmovement(M)
    F.setflag(I.HIDE_VMAX); F.removeobject(M)
    F.setflag(I.F_VWON); F.releaseall(); F.end()
    # ---- loss
    F.lab('lost')
    F.playse(SE_SHOT); F.raw(0x30)
    F.setflag(I.HIDE_VMAX); F.removeobject(M); F.clearflag(I.HIDE_VSPLM); F.addobject(SPLM)
    F.msg(T(["BANG!","MAX goes down."]),4)
    F.playse(SE_SHOT); F.raw(0x30)
    F.msg(T(["BANG!","You were shot!"]),4)
    F.setflag(I.F_VLOST); F.setflag(I.F_MAXDEAD); F.setvar(I.VAR_SOUL,1)
    # both run modes visit the afterlife (spec 5b); story_afterlife.py plays MAX's soul once, then a NORMAL run is white-out-restored, a PLAYABLE run stays dead
    F.lab('afterlife')
    callnative(F,nat['rep_calc']); F.compare(I.VAR_REP,100); F.goto_if(0,'hell')
    F.msg(T(["The world goes white.","Something warm lifts you up."]),4); F.raw(0x97,1); F.raw(0x39,2,80,0xff); F._add(struct.pack('<HH',8,25)); F.raw(0x27); F.releaseall(); F.end()
    F.lab('hell')
    F.msg(T(["Your soul falls.","Flames rise to meet you."]),4); F.raw(0x97,1); F.raw(0x39,2,68,0xff); F._add(struct.pack('<HH',11,23)); F.raw(0x27); F.releaseall(); F.end()
    fight=0x08000000+put_script(r,F)
    # ---- gun pickup: an item-ball sprite on soldier 2's tile (the splatter objects are walkable, so they cannot be talked to)
    P=SB(); P.lock(); P.raw(0x2b); P._add(struct.pack('<H',I.F_GUNTAKEN)); P.goto_if(1,'taken')
    P.msg(T(["A GLOCK lies in the blood."]),4); P.giveitem(ITEM_GLOCK); P.setflag(I.F_GUNTAKEN); P.setflag(I.HIDE_VGUN); P.removeobject(GUN); P.release(); P.end()
    P.lab('taken'); P.release(); P.end()
    pick=0x08000000+put_script(r,P)
    # ---- objects (templates sit at the stopped positions)
    got=[add_obj(r,G,N,SPOT_S1[0],SPOT_S1[1],GFX_SOLDIER,fight,0,I.HIDE_VS1),
         add_obj(r,G,N,SPOT_M[0],SPOT_M[1],GFX_GIRL,fight,0,I.HIDE_VMAX),
         add_obj(r,G,N,SPOT_S2[0],SPOT_S2[1],GFX_SOLDIER,fight,0,I.HIDE_VS2),
         add_obj(r,G,N,SPOT_S2[0],SPOT_S2[1],GFX_SPLAT,0,0,I.HIDE_VSPL2),
         add_obj(r,G,N,SPOT_M[0],SPOT_M[1],GFX_SPLAT,0,0,I.HIDE_VSPLM),
         add_obj(r,G,N,SPOT_GUN[0],SPOT_GUN[1],GFX_BALL,pick,0,I.HIDE_VGUN)]
    assert got==[S1,M,S2,SPL2,SPLM,GUN],got
    # ---- the arrival scene
    A=SB(); A.raw(0x2b); A._add(struct.pack('<H',I.F_ARREST)); A.goto_if(1,'skip'); A.lockall(); A.setvar(I.VAR_VIRI,1); A.setflag(I.F_ARREST)
    for oid,(x,y) in ((S1,SPOT_S1),(M,SPOT_M),(S2,SPOT_S2)):
        A.raw(0x63); A._add(struct.pack('<HHH',oid,x+START_DX,y))
    A.clearflag(I.HIDE_VS1); A.clearflag(I.HIDE_VMAX); A.clearflag(I.HIDE_VS2)
    for oid in (S1,M,S2): A.addobject(oid)
    for oid in (S1,M,S2): A.applymovement(oid,mv(r,*([LEFT]*START_DX)))
    for oid in (S1,M,S2): A.waitmovement(oid)
    for oid in (S1,M,S2): A.raw(0x64); A._add(struct.pack('<H',oid))
    A.msg(T(["Max twists in the soldiers' grip,\nPIKACHU clutched to her chest.","She does not say a word."]),4)
    A.releaseall(); A.end()
    A.lab('skip'); A.end()
    arrive=0x08000000+put_script(r,A)
    for x in (22,23,24,25): add_coord(r,G,N,x,36,I.VAR_VIRI,0,arrive)
    cp=r32(r,ev+12)-0x08000000
    for k in range(r.b[ev+2]):
        if struct.unpack('<HH',r.b[cp+16*k:cp+16*k+4])[1]==36 and r32(r,cp+16*k+12)==arrive: r.b[cp+16*k+4]=0      # elevation 0 = any
    # ---- every Viridian load: objects follow the scene state (runs before the old on-load script)
    allf=(I.HIDE_VS1,I.HIDE_VS2,I.HIDE_VMAX,I.HIDE_VSPL2,I.HIDE_VSPLM,I.HIDE_VGUN)
    states=(('F_VLOST',I.F_VLOST,(I.HIDE_VS1,I.HIDE_VS2,I.HIDE_VMAX,I.HIDE_VSPL2,I.HIDE_VGUN)),
            ('F_VWON',I.F_VWON,(I.HIDE_VS1,I.HIDE_VS2,I.HIDE_VMAX,I.HIDE_VSPLM)),
            ('F_ARREST',I.F_ARREST,(I.HIDE_VSPL2,I.HIDE_VSPLM,I.HIDE_VGUN)))
    L=SB()
    for nm,fl,hide in states: L.raw(0x2b); L._add(struct.pack('<H',fl)); L.goto_if(1,'s_'+nm)
    for f in allf: L.setflag(f)
    L.goto('old')
    for nm,fl,hide in states:
        L.lab('s_'+nm)
        for f in allf:
            (L.setflag if f in hide else L.clearflag)(f)
        if nm=='F_VWON': L.raw(0x2b); L._add(struct.pack('<H',I.F_GUNTAKEN)); L.goto_if(0,'old'); L.setflag(I.HIDE_VGUN)      # taken: the gun stays gone
        L.goto('old')
    ms=r32(r,h+8)-0x08000000; a=ms; oldp=None
    while r.b[a]:
        if r.b[a]==3: oldp=r32(r,a+1); newat=a+1; break
        a+=5
    assert oldp
    L.lab('old'); L.raw(0x05); L.ptr(oldp)
    r.w32(newat,0x08000000+put_script(r,L))
    print('viridian trainer',tid,'objects',S1,M,S2,SPL2,SPLM,GUN,'end',hex(r.cur))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
