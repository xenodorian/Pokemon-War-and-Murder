"""MAX's later double battles with her RAICHU (usage: story_ambush.py IN.gba OUT.gba). Spec section 9: placed at two story points (decision, 2026-10-16):
 A Cerulean City (3,3) road, soldiers Lv 22, RAICHU Lv 24;  B Vermilion City (3,5) road, soldiers Lv 30, RAICHU Lv 32.
 Only after the Viridian fight was won (F_VWON: MAX is alive). A coord event on the road plays the scene once: MAX and two JRA soldiers appear, the double battle starts at once with
 MAX's RAICHU as the AI partner (native viri_prepare with VAR 0x4093/0x4094 = species/level, partner AI of viri_native.c). Win: the soldiers flee, MAX gives a RARE CANDY. Loss: heal and carry on
 (trainerbattle mode 9), the soldiers leave, MAX survives (only the Viridian loss kills her)."""
import sys,struct,os
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from inc import *
from leg1 import r32,header,enc
from shinigami import SB,put_script,add_obj,add_coord
import story_ids as I, story_text as ST, story_native as SN, story_viri_native as SV
import story_viridian as V
G=3
RAICHU=26; ITEM_RARE_CANDY=68
SITES=[dict(n=3,name='CERULEAN',trig=[(28,21),(28,22),(28,23)],spots=[(24,22),(25,22),(26,22)],hide=(I.HIDE_AS1,I.HIDE_AM,I.HIDE_AS2),done=I.F_ADONE,var=I.VAR_AMB_A,lv=22,rlv=24,spl=I.HIDE_SPLA,
            team=[58,17,20,24],line="Max steps out, RAICHU at her side.\nShe says nothing."),
       dict(n=5,name='VERMILION',trig=[(30,18),(30,19),(30,20),(30,21)],spots=[(33,19),(34,19),(35,19)],hide=(I.HIDE_BS1,I.HIDE_BM,I.HIDE_BS2),done=I.F_BDONE,var=I.VAR_AMB_B,lv=30,rlv=32,spl=I.HIDE_SPLB,
            team=[59,85,112,103],line="Max steps out, RAICHU at her side.\nShe says nothing."),
       dict(n=2,name='PEWTER',trig=[(36,14),(36,15),(36,16)],spots=[(32,15),(33,15),(34,15)],hide=(I.HIDE_CS1,I.HIDE_CM,I.HIDE_CS2),done=I.F_CDONE,var=I.VAR_AMB_C,lv=14,rlv=16,
            team=[16,19,41,74],line="Max steps out, PIKACHU at her side.\nShe says nothing.",spl=I.HIDE_SPLC,mon=25),
       dict(n=4,name='LAVENDER',trig=[(30,14),(30,15),(30,16)],spots=[(26,15),(27,15),(28,15)],hide=(I.HIDE_DS1,I.HIDE_DM,I.HIDE_DS2),done=I.F_DDONE,var=I.VAR_AMB_D,lv=36,rlv=36,
            team=[93,42,97,24],line="Max steps out, RAICHU at her side.\nShe says nothing.",spl=I.HIDE_SPLD),
       dict(n=6,name='CELADON',trig=[(24,14),(24,15),(24,16)],spots=[(20,15),(21,15),(22,15)],hide=(I.HIDE_ES1,I.HIDE_EM,I.HIDE_ES2),done=I.F_EDONE,var=I.VAR_AMB_E,lv=40,rlv=40,
            team=[45,71,103,114],line="Max steps out, RAICHU at her side.\nShe says nothing.",spl=I.HIDE_SPLE),
       dict(n=7,name='FUCHSIA',trig=[(29,23),(29,24),(29,25)],spots=[(25,24),(26,24),(27,24)],hide=(I.HIDE_FS1,I.HIDE_FM,I.HIDE_FS2),done=I.F_FDONE,var=I.VAR_AMB_F,lv=46,rlv=46,
            team=[112,143,131,142],line="Max steps out, RAICHU at her side.\nShe says nothing.",spl=I.HIDE_SPLF)]
def trainer(r,team,lv,name):
    b=r.b; tid=None
    for t in range(700,760):
        e=b[V.T_TABLE+40*t:V.T_TABLE+40*t+40]
        if e[4]==0xFF and struct.unpack('<I',e[36:40])[0] in (0,0xFFFFFFFF): tid=t; break
    assert tid
    e=bytearray(b[V.T_TABLE+40*326:V.T_TABLE+40*327])
    e[0]=0; e[1]=V.CLS_SOLDIER; e[2]=0; e[3]=V.PIC_SOLDIER
    nm=enc(name)[:-1]; e[4:16]=nm+b'\xff'*(12-len(nm)); e[16:28]=bytes(12)
    e[24:28]=struct.pack('<I',1)
    seq=[team[0],team[2],team[1],team[3]]            # soldier 1 and 2 lead with their first, then their second
    e[32:36]=struct.pack('<I',len(seq))
    party=b''.join(struct.pack('<HBBHH',0,lv,0,sp,0) for sp in seq)
    e[36:40]=struct.pack('<I',0x08000000+r.alloc(party,4))
    b[V.T_TABLE+40*tid:V.T_TABLE+40*tid+40]=e
    return tid
def site(r,s,nat2):
    n=s['n']; T=lambda t: ST.ptr_s(r,V.wrap(t))
    tid=trainer(r,s['team'],int(os.environ.get('AMB_LV',s['lv'])),'ESCORT')      # AMB_LV: TEST ONLY
    h=header(r,G,n)
    ids=[]
    for (x,y),gfx,fl in zip(s['spots'],(V.GFX_SOLDIER,V.GFX_GIRL,V.GFX_SOLDIER),s['hide']):
        ids.append(add_obj(r,G,n,x,y,gfx,0,0,fl))
    S1,M,S2=ids
    SPL=add_obj(r,G,n,s['spots'][1][0],s['spots'][1][1],V.GFX_SPLAT,0,0,s['spl'])
    F=SB(); F.raw(0x2b); F._add(struct.pack('<H',I.F_VWON)); F.goto_if(0,'no')
    F.raw(0x2b); F._add(struct.pack('<H',I.F_MAXDEAD)); F.goto_if(1,'no')
    F.raw(0x2b); F._add(struct.pack('<H',s['done'])); F.goto_if(1,'no')
    F.lockall(); F.setvar(s['var'],1); F.setflag(s['done'])
    for f in s['hide']: F.clearflag(f)
    for o in ids: F.addobject(o)
    F.msg(T([s['line']]),4)
    F.setvar(0x4093,s.get('mon',RAICHU)); F.setvar(0x4094,s['rlv'])
    V.callnative(F,nat2['viri_prepare'])
    F.raw(0x5c,9); F._add(struct.pack('<HH',tid,1)); F.ptr(ST.battle_ptr(r,"Tch. We lost.")); F.ptr(ST.battle_ptr(r,"Fall back!"))
    V.callnative(F,nat2['viri_cleanup'])
    F.compare(V.RESULT,1); F.goto_if(1,'lost')
    F.msg(T(["SOLDIER: Retreat! Tell the captain she has a RAICHU now!"]),4)
    F.setflag(s['hide'][0]); F.removeobject(S1); F.setflag(s['hide'][2]); F.removeobject(S2)
    F.msg(T(["Max nods once, without a word.","She holds out something she took\nfrom a soldier."]),4)
    F.giveitem(ITEM_RARE_CANDY)
    F.setflag(s['hide'][1]); F.removeobject(M); F.releaseall(); F.end()
    F.lab('lost')
    F.msg(T(["SOLDIER: The little traitor is done running."]),4)
    F.playse(V.SE_SHOT); F.raw(0x30)
    F.setflag(s['hide'][1]); F.removeobject(M); F.clearflag(s['spl']); F.addobject(SPL)
    F.msg(T(["BANG!","Max goes down. She does not get\nup again."]),4)
    F.setflag(I.F_MAXDEAD); F.setvar(s['var'],2)
    F.setflag(s['hide'][0]); F.removeobject(S1); F.setflag(s['hide'][2]); F.removeobject(S2)
    F.msg(T(["The soldiers leave her where she\nfell."]),4)
    F.releaseall(); F.end()
    F.lab('no'); F.end()
    sc=0x08000000+put_script(r,F)
    for x,y in s['trig']: add_coord(r,G,n,x,y,s['var'],0,sc)
    ev=r32(r,h+4)-0x08000000; cp=r32(r,ev+12)-0x08000000
    for k in range(r.b[ev+2]):
        if r32(r,cp+16*k+12)==sc: r.b[cp+16*k+4]=0
    # map load: the actors are hidden (they exist only during the scene script), then the old on-load script
    L=SB()
    for f in s['hide']: L.setflag(f)
    L.compare(s['var'],2); L.goto_if(1,'ld'); L.setflag(s['spl']); L.goto('ld2'); L.lab('ld'); L.clearflag(s['spl']); L.lab('ld2')
    ms=r32(r,h+8)-0x08000000; a=ms; oldp=None
    while r.b[a]:
        if r.b[a]==3: oldp=r32(r,a+1); newat=a+1; break
        a+=5
    assert oldp,s['name']
    L.raw(0x05); L.ptr(oldp)
    r.w32(newat,0x08000000+put_script(r,L))
    print('ambush',s['name'],'trainer',tid,'objects',ids)
def install(r):
    nat2=SV.addrs2(r)
    for s in SITES: site(r,s,nat2)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
