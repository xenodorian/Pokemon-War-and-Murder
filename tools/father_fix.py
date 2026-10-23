"""Leaf's father after the choice (usage: father_fix.py IN.gba OUT.gba), run through tools/patch.sh after story_anne_fix.py.
House (4,0): the bed object (local id 1, gfx 25 at (2,4)) and the two bed bg tiles (2,3), (2,5) talk to the father.
 - choice not made (VAR_CHOICE 0x40F0 == 0) or VAR_CHOICE 2: "Your father is dead." / "Your father is dead, and you chose power over family." (2 = YVELTAL)
 - father revived (F_FATHER_ALIVE 0x4FC, set by the choice scene): no interaction, and the sprite is gone. The object template's hide flag is 0x4FC (applies on every map load) and the
   choice scene now also runs removeobject 1 so the bed is empty at once.
The choice scene (frame script of VAR_STORY == 7) is rebuilt as in story_anne_fix.py with the removeobject added; the old native 'make' address is read from the old script."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
from leg1 import r32,header
from shinigami import SB,put_script
import story_ids as I
import story_text as ST
import story_anne as A
from story_anne_fix import old_script,ITEM_SCROLL,HOUSE,VAR_STORY_GO_HOME
FATHER_OBJ=1
def install(r):
    b=r.b
    h=header(r,*HOUSE); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    assert b[ev]==1 and b[po]==FATHER_OBJ and b[po+1]==25
    # --- the choice scene, rebuilt with the father leaving the bed
    tab=old_script(r,HOUSE[0],HOUSE[1],I.VAR_STORY,VAR_STORY_GO_HOME)
    old=r32(r,tab+4)-0x08000000
    make=None
    for i in range(old,old+400):
        if b[i]==0x23:
            p=r32(r,i+1)
            if 0x08000000<=p<0x0a000000 and p&1: make=p; break
    assert make,'native make not found'
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
    H.removeobject(FATHER_OBJ)
    H.lab('done')
    H.setvar(I.VAR_STORY,3)
    H.releaseall(); H.end()
    r.w32(tab+4,0x08000000+put_script(r,H))
    # --- father interaction
    N=SB(); N.raw(0x2b); N._add(struct.pack('<H',I.F_FATHER_ALIVE)); N.goto_if(1,'gone')
    N.lock(); N.compare(I.VAR_CHOICE,2); N.goto_if(1,'power')
    N.msg(ST.ptr_s(r,["Your father is dead."]),4); N.release(); N.end()
    N.lab('power')
    N.msg(ST.ptr_s(r,["Your father is dead, and you chose\npower over family."]),4); N.release(); N.end()
    N.lab('gone'); N.end()
    scr=0x08000000+put_script(r,N)
    b[po+16:po+20]=struct.pack('<I',scr)
    b[po+20:po+22]=struct.pack('<H',I.F_FATHER_ALIVE)       # hide flag
    bg=r32(r,ev+16)-0x08000000; n=0
    for i in range(b[ev+3]):
        o=bg+12*i
        if struct.unpack('<HH',b[o:o+4]) in ((2,3),(2,5)):
            r.w32(o+8,scr); n+=1
    assert n==2,n
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
