"""Shinigami cell scene as in CryMon (usage: shinigami_scene.py IN.gba OUT.gba), run through tools/patch.sh after shinigami_cage.py.
CryMon source (xenodorian/CryMon): content/dialogue.json talk.shinigamiSpot (cell talk), trainers.json shinigami (three monsters at 15/14/13, fought once, no mercy), talk.shinigamiAfter (win lines, the scroll).
 - species 265 SHINIGAMI (Ghost/Dark, his own battle picture, donor HAUNTER). CryMon fights three CryMare; here the namesake monster takes that place: SHINIGAMI at 15, 14, 13.
 - trainer 49 (SHINIGAMI) party becomes those three. The tower-top fight object is hidden for good, and the League fight only runs if he was never freed.
 - item 90 becomes the key item SCROLL (Scroll of Resurrection); the Father branch of the choice removes it.
 - the cell talk script (object 6 in map 2,69): CryMon cell lines, then the battle, then the win lines, the scroll and the old rewards, then he leaves."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
import leg1,shinigami
from leg1 import r32,header
from shinigami import SB,put_script,text,TR_ID,F_SHINI_GONE,ITEM_SPELL_TAG,ITEM_MASTER_BALL,ITEM_NUGGET,ITEM_TM30,VAR_SCENE
from g3 import ENC
import species_add as SA
import story_text as ST
import story_ids as I
from PIL import Image
GFX_SHINI=0x9a
SP_SHINIGAMI=265; ITEM_SCROLL=90; OLD_AMBER=354
ITEM_BASE=0x3db028; ICONT=0x3d4294
GHOST,DARK=7,17
ART=os.path.join(HERE,'..','shinigami_art')
def add_scroll(r):
    b=r.b; o=ITEM_BASE+44*ITEM_SCROLL
    assert b[o:o+9]==bytes([0xac])*8+b'\xff' and struct.unpack('<H',b[o+14:o+16])[0]==0,b[o:o+16].hex()
    src=ITEM_BASE+44*OLD_AMBER
    rec=bytearray(b[src:src+44]); name=bytes(ENC[c] for c in 'SCROLL')+b'\xff'
    rec[0:14]=name.ljust(14,b'\x00'); rec[14:16]=struct.pack('<H',ITEM_SCROLL); rec[16:18]=struct.pack('<H',0)
    desc="The SCROLL OF RESURRECTION.\nIt wakes what is already dead."
    rec[20:24]=struct.pack('<I',0x08000000+r.alloc(bytes(ENC[c] if c!='\n' else 0xFE for c in desc)+b'\xff',1))
    b[o:o+44]=rec
    ic=ICONT+8*ITEM_SCROLL; ics=ICONT+8*OLD_AMBER
    r.w32(ic,r32(r,ics)); r.w32(ic+4,r32(r,ics+4))
def add_species(r):
    im=Image.open(os.path.join(ART,'battle.png')).convert('RGBA'); assert im.size==(64,64)
    front=os.path.join(ART,'shinigami_front.png'); back=os.path.join(ART,'shinigami_back.png')
    im.save(front); im.transpose(Image.FLIP_LEFT_RIGHT).save(back)
    LICK,NIGHT_SHADE,CONFUSE_RAY,CURSE,FAINT_ATTACK,SHADOW_BALL,CRUNCH,PSYCHIC=122,101,109,174,185,247,242,94
    learn=[(1,LICK),(1,NIGHT_SHADE),(5,CONFUSE_RAY),(9,CURSE),(13,FAINT_ATTACK),(20,SHADOW_BALL),(26,CRUNCH),(32,PSYCHIC)]
    SA.add_species(r,SP_SHINIGAMI,'SHINIGAMI',front,back,93,[55,65,55,70,85,70],(GHOST,DARK),
        catch=3,exp_yield=120,ev_yield=0,gender=255,egg_groups=(15,15),growth=0,abilities=(26,0),learnset=learn,
        dex_national=None,tm_donors=[93],shiny_shift=0.0)
def trainer_party(r):
    b=r.b; o=shinigami.T+40*TR_ID
    party=[(SP_SHINIGAMI,15),(SP_SHINIGAMI,14),(SP_SHINIGAMI,13)]
    pd=b''.join(struct.pack('<HBBHH',255,lvl,0,sp,0) for sp,lvl in party)
    b[o+32]=len(party); b[o+36:o+40]=struct.pack('<I',0x08000000+r.alloc(pd,4))
def find_obj(r,po,no,gfx):
    for i in range(no):
        t=po+24*i
        if r.b[t+1]==gfx and struct.unpack('<hh',r.b[t+4:t+8])==(21,3): return t
    raise SystemExit('Shinigami object not found at (21,3): run shinigami_cage.py first')
def cell_script(r,lid):
    T=lambda *boxes: ST.ptr_s(r,list(boxes))
    S=SB(); S.lock(); S.faceplayer()
    S.raw(0x2b); S._add(struct.pack('<H',I.F_CAPTAIN_DOWN)); S.goto_if(1,'talk')
    S.msg(T("SHINIGAMI: Beat the Captain.\nOpen this door."),4); S.release(); S.end()
    S.lab('talk')
    S.msg(T("SHINIGAMI: Three names. Three\ngraves.","SHINIGAMI: I keep them while this\ncage keeps me.","LEAF: I can get you out. I need\nyour power to bring Father back.",
            "SHINIGAMI: Then we have a bargain,\nif you can survive the bargain.","LEAF: The door is open. Come out."),4)
    t_intro=text(r,"SHINIGAMI: My shade first. Talking later.")
    t_def=text(r,"SHINIGAMI: Fine. You hit harder than a door should.")
    S.trainerbattle(TR_ID,t_intro,t_def)
    S.msg(T("Shinigami kneels. His shade will\nnot rise again.","LEAF: Give me the power. That was\nthe deal.","SHINIGAMI: Take the scroll, then.\nThe Scroll of Resurrection."),4)
    S.setflag(I.F_SCROLL)
    S.raw(0x44); S._add(struct.pack('<HH',ITEM_SCROLL,1)); S.msg(T("Leaf got the SCROLL.\nIt is a key item."),4)
    S.msg(T("SHINIGAMI: It wakes what is\nalready dead. Human or POKéMON.","SHINIGAMI: Use it well, or don't."),4)
    for it in (ITEM_SPELL_TAG,ITEM_MASTER_BALL,ITEM_NUGGET,ITEM_TM30): S.giveitem(it)
    S.msg(T("SHINIGAMI: This prison held me a\nlong time.","SHINIGAMI: Team Rocket killed my\nPikachu. I hunt their grunts now.","Shinigami walks out past you\nwithout another word.","Shinigami is gone. A black feather\nfalls where he stood."),4)
    S.playse(39); S.fadescreen(3); S.setflag(I.HIDE_CELL)
    S.raw(0x53); S.raw(0xFE,0xFF)
    S.fadescreen(2)
    S.setflag(I.F_FREED); S.setflag(F_SHINI_GONE); S.clearflag(I.HIDE_STORY); S.setvar(VAR_SCENE,0); S.setvar(I.VAR_STORY,2)
    S.release(); S.end()
    r.cur=(r.cur+3)&~3; base=r.cur
    code=bytearray(S.build(base)); i=code.index(bytes([0x53,0xFE,0xFF])); code[i+1:i+3]=struct.pack('<H',lid)
    a=r.alloc(bytes(code),1); assert a==base
    return 0x08000000+a
def install(r):
    add_scroll(r); add_species(r); trainer_party(r)
    h=header(r,2,69); ev=r32(r,h+4)-0x08000000; no=r.b[ev]; po=r32(r,ev+4)-0x08000000
    t=find_obj(r,po,no,GFX_SHINI)
    r.w32(t+16,cell_script(r,r.b[t]))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
