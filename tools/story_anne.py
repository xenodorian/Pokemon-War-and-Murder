"""Shinigami storyline part 2 (usage: story_anne.py IN.gba OUT.gba)
 - Anne waits outside the Pewter base (frame script on Pewter while VAR_STORY == 2): her news, then the choice (YES = wake Father, NO = call YVELTAL).
 - FATHER: F_FATHER_ALIVE set, VAR_CHOICE 1, Father's second team (box 14) is created at the player's party level.
 - YVELTAL: VAR_CHOICE 2 (the Tower grave script is in story_yveltal.py).
 - Quest menu gets a FATHER'S TEAM entry (swap the party with box 14 FATHER). Native code in story_party.py."""
import sys,struct
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,'/home/user/Pokemon-Outlaw-Mod/tools')
from inc import *
from leg1 import r32,header
from shinigami import SB,put_script,add_obj
import story_ids as I
import story_text as ST
import story_party
GFX_LASS=22
GFX_LITTLE_GIRL=17   # Anne is a child (pret OBJ_EVENT_GFX_LITTLE_GIRL)
RESULT=0x800D
ANNE_START=(37,7); ANNE_STOP=(35,7)
def callnative(S,fn): S.raw(0x23); S.ptr(fn)
def yesno(S,p): S.raw(0x0f,0); S.ptr(p); S.raw(0x09,5)
def set_frame(r,g,n,var,val,script):
    h=header(r,g,n); p=r32(r,h+8); ents=[]
    a=p-0x08000000
    while r.b[a]!=0: ents.append((r.b[a],struct.unpack('<I',r.b[a+1:a+5])[0])); a+=5
    assert not any(t==2 for t,_ in ents)
    tab=r.alloc(struct.pack('<HHI',var,val,script)+b'\0\0',4)
    ents.append((2,0x08000000+tab))
    r.w32(h+8,0x08000000+r.alloc(b''.join(bytes([t])+struct.pack('<I',s) for t,s in ents)+b'\x00',4))
def anne_scene(r,nat):
    g,n=3,2
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    aid=max(r.b[po+24*i] for i in range(r.b[ev]))+1
    T=SB(); T.lock(); T.faceplayer(); T.msg(ST.ptr_s(r,"ANNE: I am here if you need me."),4); T.release(); T.end()
    got=add_obj(r,g,n,ANNE_START[0],ANNE_START[1],GFX_LITTLE_GIRL,0x08000000+put_script(r,T),8,I.HIDE_ANNE); assert got==aid
    left=0x08000000+r.alloc(bytes([0x12,0xFE]),1); right=0x08000000+r.alloc(bytes([0x13,0x13,0xFE]),1)
    S=SB(); S.lockall()
    S.clearflag(I.HIDE_ANNE); S.addobject(aid)
    S.applymovement(aid,left); S.waitmovement(aid)
    S.msg(ST.ptr(r,'anne_news'),4)
    S.msg(ST.ptr_s(r,["Use the scroll on Father,\nor speak YVELTAL's name?"]),4)
    yesno(S,ST.ptr_s(r,["YES: Wake Father\nNO: Call YVELTAL"]))
    S.compare(RESULT,1); S.goto_if(1,'father')
    S.setvar(I.VAR_CHOICE,2); S.msg(ST.ptr(r,'choice_yveltal'),4); S.goto('done')
    S.lab('father')
    S.setvar(I.VAR_CHOICE,1); S.setvar(I.VAR_YV,9); S.setflag(I.F_FATHER_ALIVE); S.msg(ST.ptr(r,'choice_father'),4)
    callnative(S,nat['make']); S.msg(ST.ptr(r,'father_revived_talk'),4)
    S.lab('done')
    S.setvar(I.VAR_STORY,3)
    S.applymovement(aid,right); S.waitmovement(aid); S.removeobject(aid); S.setflag(I.HIDE_ANNE)
    S.releaseall(); S.end()
    set_frame(r,g,n,I.VAR_STORY,2,0x08000000+put_script(r,S))
def father_menu(r,nat):
    entry=r32(r,0xa01a38)-0x08000000
    assert r.b[entry]==0x69 and r.b[entry+1]==0x6f
    mid=r.b[entry+4]
    tab=r32(r,0x9cb58)-0x08000000
    # new 6 item list
    items=['CURRENT QUEST','STORY QUEST','THE REAPER','SIDE QUESTS',"FATHER'S TEAM",'CLOSE']
    ls=b''.join(struct.pack('<II',0x08000000+r.alloc(ST.enc_boxes([t]),1),0) for t in items)
    r.b[tab+8*mid:tab+8*mid+8]=struct.pack('<IBBBB',0x08000000+r.alloc(ls,4),len(items),0,0,0)
    # the final 'goto m_exit' after the four result tests
    g=entry+6+4*11; assert r.b[g]==0x05,(r.b[g],hex(g)); m_exit=r32(r,g+1)
    S=SB(); S.compare(RESULT,4); S.goto_if(1,'f'); S.raw(0x05); S.ptr(m_exit)
    S.lab('f'); S.raw(0x2b); S._add(struct.pack('<H',I.F_FATHER_ALIVE)); S.goto_if(1,'have')
    S.msg(ST.ptr_s(r,["Nobody travels with you."]),4); S.raw(0x68); S.raw(0x05); S.ptr(0x08000000+entry+1)
    S.lab('have'); yesno(S,ST.ptr_s(r,["Swap your party with\nFATHER's team?"])); S.compare(RESULT,1); S.goto_if(5,'no')
    callnative(S,nat['swap']); S.msg(ST.ptr_s(r,["Your party and FATHER's\nteam traded places."]),4)
    S.lab('no'); S.raw(0x68); S.raw(0x05); S.ptr(0x08000000+entry+1)
    code=put_script(r,S); r.b[g+1:g+5]=struct.pack('<I',0x08000000+code); r.b[g]=0x05
def install(r):
    nat=story_party.install(r); anne_scene(r,nat); father_menu(r,nat); return nat
if __name__=='__main__':
    r=Rom(sys.argv[1]); print({k:hex(v) for k,v in install(r).items()}); r.save(sys.argv[2]); print('end',hex(r.cur))
