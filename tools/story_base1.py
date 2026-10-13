"""Shinigami storyline part 1 (usage: story_base1.py IN.gba OUT.gba)
 - new game init (player's home transition): story crime scenes hidden, Lavender plaza scene held back, Tower Shinigami object hidden
 - crime scenes (bodies, feathers, cops who talk about feathers) get HIDE_STORY; they appear once Shinigami is freed
 - Shinigami is locked in the first JRA base (Pewter, map 2,69): talking to him before the Captain falls (flag 0x4C0) gets his plea, after it frees him
 - freeing: scroll, rewards, F_FREED, HIDE_STORY cleared, VAR_SCENE 0 (Lavender plaza scene armed), VAR_STORY 2
 - League: Shinigami's line there says you freed him"""
import sys,struct
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,'/home/user/Pokemon-Outlaw-Mod/tools')
from inc import *
import leg1,shinigami,leg1b
from leg1 import r32,header,free_tile
from shinigami import SB,put_script,add_obj,TR_ID,VAR_SCENE,F_SHINI_GONE,ITEM_SPELL_TAG,ITEM_MASTER_BALL,ITEM_NUGGET,ITEM_TM30
from g3 import ENC
import story_ids as I
import story_text as ST
INV={v:k for k,v in ENC.items()}
GFX_SHINI=0x9a; GFX_FEATHER=0x9b; GFX_BODY=0x99
HOME_TRANSITION_LIST=0x350d58
def dec(b):
    return ''.join(INV.get(c,'?') for c in b)
def first_text(r,script_ptr):
    a=script_ptr-0x08000000
    if not 0<=a<len(r.b)-8: return ''
    if r.b[a]==0x0f and r.b[a+1]==0:
        t=r32(r,a+2)-0x08000000; e=t
        while r.b[e]!=0xff: e+=1
        return dec(r.b[t:e])
    return ''
def new_game_init(r):
    """the player's home map transition script gets a one-time init guarded by VAR_STORY == 0"""
    lst=r32(r,HOME_TRANSITION_LIST)-0x08000000; assert r.b[lst]==3
    old=r32(r,lst+1)-0x08000000; e=old
    while r.b[e]!=0x02: e+=1
    inner=bytes(r.b[old:e])
    S=SB(); S._add(inner); S.compare(I.VAR_STORY,0); S.goto_if(1,'init'); S.end()
    S.lab('init'); S.setvar(I.VAR_STORY,1); S.setflag(I.HIDE_STORY); S.setflag(I.F_TOWER_HIDE); S.setvar(VAR_SCENE,5); S.end()
    r.w32(lst+1,0x08000000+put_script(r,S))
def gate_crime_scenes(r):
    n=0
    for g in range(0,4):
        gp=r32(r,0x3526A8+4*g)-0x08000000
        for m in range(60):
            try: h=r32(r,gp+4*m)-0x08000000
            except Exception: break
            if not 0x08000000<=r32(r,gp+4*m)<0x0a000000: break
            if g!=3 and (g,m) not in ((1,42),): continue
            ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
            bodies=[]
            for i in range(r.b[ev]):
                t=po+24*i; gfx=r.b[t+1]; flag=struct.unpack('<H',r.b[t+20:t+22])[0]
                sp=r32(r,t+16)
                if flag!=0: continue
                if gfx in (GFX_BODY,GFX_FEATHER) or 'feather' in first_text(r,sp).lower():
                    r.b[t+20:t+22]=struct.pack('<H',I.HIDE_STORY); n+=1; print('gated',(g,m),struct.unpack('<hh',r.b[t+4:t+8]),hex(gfx))
                    if gfx==GFX_BODY: bodies.append(struct.unpack('<hh',r.b[t+4:t+8]))
            for i in range(r.b[ev]):     # the cop who explains the scene stands within 3 tiles of the body
                t=po+24*i
                if r.b[t+1]==60 and struct.unpack('<H',r.b[t+20:t+22])[0]==0:
                    p=struct.unpack('<hh',r.b[t+4:t+8])
                    if any(abs(p[0]-b[0])+abs(p[1]-b[1])<=3 for b in bodies):
                        r.b[t+20:t+22]=struct.pack('<H',I.HIDE_STORY); n+=1; print('gated cop',(g,m),p)
    return n
def lavender_hold(r):
    """Lavender transition: before Shinigami is freed (or after the plaza scene ran) keep the plaza quiet"""
    h=header(r,3,4); ms=r32(r,h+8)-0x08000000; assert r.b[ms]==3
    old=r32(r,ms+1)-0x08000000; e=old
    pat=bytes([0x21])+struct.pack('<HH',VAR_SCENE,1)
    while r.b[e:e+5]!=pat: e+=1
    inner=bytes(r.b[old:e])
    T_=SB(); T_._add(inner)
    T_.compare(VAR_SCENE,1); T_.goto_if(1,'done')
    T_.compare(VAR_SCENE,5); T_.goto_if(1,'quiet')
    T_.setflag(shinigami.F_SPLAT_HIDDEN); T_.clearflag(shinigami.F_POLICE_GONE); T_.end()
    T_.lab('done'); T_.clearflag(shinigami.F_SPLAT_HIDDEN); T_.setflag(shinigami.F_POLICE_GONE); T_.end()
    T_.lab('quiet'); T_.setflag(shinigami.F_SPLAT_HIDDEN); T_.setflag(shinigami.F_POLICE_GONE); T_.end()
    r.w32(ms+1,0x08000000+put_script(r,T_))
def tower_object(r):
    h=header(r,2,66); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000; k=0
    for i in range(r.b[ev]):
        t=po+24*i
        if r.b[t+1]==GFX_SHINI:
            assert struct.unpack('<H',r.b[t+20:t+22])[0]==F_SHINI_GONE
            r.b[t+20:t+22]=struct.pack('<H',I.F_TOWER_HIDE); k+=1
    assert k==1
def league(r):
    h=header(r,1,78); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    cp=r32(r,ev+12)-0x08000000; k=0
    for i in range(r.b[ev+2]):
        c=cp+16*i
        if struct.unpack('<HH',r.b[c:c+4])==(23,12):
            a=r32(r,c+12)-0x08000000
            # find the message that starts 'SHINIGAMI: You beat me'
            e=a
            while True:
                if r.b[e]==0x0f and r.b[e+1]==0 and first_text(r,0x08000000+e).startswith('SHINIGAMI: You beat me'): break
                e+=1
            r.w32(e+2,ST.ptr_s(r,["SHINIGAMI: You freed me, so I will\nnot stand in your way.","LANCE gave the orders that killed\nmy PIKACHU. Make him pay."]))
            k+=1
    assert k==1
def captive(r):
    g,n=2,69
    # the new object must be free of the soldiers' cleared flag; it is hidden after the freeing by HIDE_CELL
    x,y=free_tile(r,g,n,21,4); print('captive at',x,y)
    S=SB(); S.lock(); S.faceplayer()
    S.raw(0x2b); S._add(struct.pack('<H',I.F_CAPTAIN_DOWN)); S.goto_if(1,'free')
    S.msg(ST.ptr(r,'shinigami_captive_talk'),4); S.release(); S.end()
    S.lab('free')
    S.msg(ST.ptr(r,'captain_defeat_win'),4)
    S.msg(ST.ptr(r,'free_shinigami'),4)
    S.setflag(I.F_SCROLL)
    for it in (ITEM_SPELL_TAG,ITEM_MASTER_BALL,ITEM_NUGGET,ITEM_TM30): S.giveitem(it)
    S.msg(ST.ptr(r,'shinigami_leaves'),4)
    S.playse(39); S.fadescreen(3); S.setflag(I.HIDE_CELL)
    oid=0  # patched below to the new object's local id
    S.raw(0x53); S.raw(0xFE,0xFF)   # removeobject placeholder, local id patched
    S.fadescreen(2)
    S.setflag(I.F_FREED); S.setflag(F_SHINI_GONE); S.clearflag(I.HIDE_STORY); S.setvar(VAR_SCENE,0); S.setvar(I.VAR_STORY,2)
    S.release(); S.end()
    sc_pos=r.cur
    lid_holder=[]
    # build the script after the object id is known: object ids are max+1
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    lid=max(r.b[po+24*i] for i in range(r.b[ev]))+1
    code=bytearray(S.build((r.cur+3)&~3)); 
    i=code.index(bytes([0x53,0xFE,0xFF])); code[i+1:i+3]=struct.pack('<H',lid)
    r.cur=(r.cur+3)&~3; base=r.cur; a=r.alloc(bytes(code),1); assert a==base
    got=add_obj(r,g,n,x,y,GFX_SHINI,0x08000000+a,8,I.HIDE_CELL); assert got==lid
def install(r):
    new_game_init(r); print('gated',gate_crime_scenes(r))
    lavender_hold(r); tower_object(r); league(r); captive(r)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
