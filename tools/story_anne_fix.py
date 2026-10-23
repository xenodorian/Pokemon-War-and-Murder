"""Anne scene and father choice fix (usage: story_anne_fix.py IN.gba OUT.gba), run through tools/patch.sh after shinigami_scene.py.
Before: Anne's news and the scroll choice both ran outside the Pewter base, so the player could wake Father from the street, and the news text named Shinigami.
Now: Pewter (3,2), VAR_STORY == 2: Anne tells the news (no Shinigami in it), walks away, Leaf runs home: VAR_STORY 7, warp to the house (4,0) at Father's bedside (3,4).
House frame script, VAR_STORY == 7: Leaf faces Father, the choice (YES wake Father, NO call YVELTAL), no Anne or Shinigami in the text.
FATHER: SCROLL key item and F_SCROLL removed, F_FATHER_ALIVE, VAR_CHOICE 1, VAR_YV 9, Father's second team made in PC box 14 (native 'make' from story_party, address read from the old Anne script). YVELTAL keeps the scroll. Both end with VAR_STORY 3."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
from leg1 import r32,header
from shinigami import SB,put_script
import story_ids as I
import story_text as ST
import story_anne as A
ITEM_SCROLL=90
HOUSE=(4,0); BEDSIDE=(3,4); VAR_STORY_GO_HOME=7
def old_script(r,g,n,var,val):
    h=header(r,g,n); a=r32(r,h+8)-0x08000000
    while r.b[a]!=0:
        if r.b[a]==2:
            tab=r32(r,a+1)-0x08000000
            if struct.unpack('<HH',r.b[tab:tab+4])==(var,val): return tab
        a+=5
    raise SystemExit('frame script not found')
def find_make(r,tab):
    s=r32(r,tab+4)-0x08000000
    for i in range(s,s+600):
        if r.b[i]==0x23:
            p=r32(r,i+1)
            if 0x08000000<=p<0x0a000000 and p&1 and r.b[i+5]!=0x23: return p
    raise SystemExit('native make not found')
def anne_object(r):
    h=header(r,3,2); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    for i in range(r.b[ev]):
        t=po+24*i
        if r.b[t+1]==A.GFX_LITTLE_GIRL and struct.unpack('<H',r.b[t+20:t+22])[0]==I.HIDE_ANNE: return r.b[t]
    raise SystemExit('Anne object not found')
def install(r):
    tab=old_script(r,3,2,I.VAR_STORY,2); make=find_make(r,tab); aid=anne_object(r)
    right=0x08000000+r.alloc(bytes([0x13,0x13,0xFE]),1); left=0x08000000+r.alloc(bytes([0x12,0xFE]),1)
    S=SB(); S.lockall()
    S.clearflag(I.HIDE_ANNE); S.addobject(aid)
    S.applymovement(aid,left); S.waitmovement(aid)
    S.msg(ST.ptr(r,'anne_news'),4)
    S.applymovement(aid,right); S.waitmovement(aid); S.removeobject(aid); S.setflag(I.HIDE_ANNE)
    S.setvar(I.VAR_STORY,VAR_STORY_GO_HOME)
    S.fadescreen(1)
    S.raw(0x39,HOUSE[0],HOUSE[1],0xff); S._add(struct.pack('<hh',*BEDSIDE)); S.raw(0x27)
    S.end()
    r.w32(tab+4,0x08000000+put_script(r,S))
    face_left=0x08000000+r.alloc(bytes([0x02,0xFE]),1)
    H=SB(); H.lockall()
    H.applymovement(0xFF,face_left); H.waitmovement(0xFF)
    H.msg(ST.ptr(r,'father_bedside'),4)
    H.msg(ST.ptr(r,'choice_prompt'),4)
    H.raw(0x0f,0); H.ptr(ST.ptr_s(r,["YES: Wake Father\nNO: Call YVELTAL"])); H.raw(0x09,5)
    H.compare(A.RESULT,1); H.goto_if(1,'father')
    H.setvar(I.VAR_CHOICE,2); H.msg(ST.ptr(r,'choice_yveltal'),4); H.goto('done')
    H.lab('father')
    H.setvar(I.VAR_CHOICE,1); H.setvar(I.VAR_YV,9); H.setflag(I.F_FATHER_ALIVE)
    H.raw(0x45); H._add(struct.pack('<HH',ITEM_SCROLL,1)); H.clearflag(I.F_SCROLL)
    H.msg(ST.ptr(r,'choice_father'),4)
    A.callnative(H,make); H.msg(ST.ptr(r,'father_revived_talk'),4)
    H.lab('done')
    H.setvar(I.VAR_STORY,3)
    H.releaseall(); H.end()
    A.set_frame(r,HOUSE[0],HOUSE[1],I.VAR_STORY,VAR_STORY_GO_HOME,0x08000000+put_script(r,H))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
