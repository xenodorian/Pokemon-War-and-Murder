"""Shinigami storyline part 5: NERO replaces the JRA General (usage: story_nero.py IN.gba OUT.gba)
 - trainer 530 'GORE' becomes NERO with the Nero picture (story_assets/chars/nero_pic.png), trainer class stays JRA GENERAL
 - his script: intro (nero_spot), battle, nero_defeated, then ARREST / EXECUTE / CROWN (two yes/no boxes), father reaction, epilogue cards with titles, then the old warp to the Hall of Justice
 - VAR_NERO 1 arrested, 2 executed, 3 crowned; VAR_STORY 5 afterwards; F_ENDED set after the cards"""
import sys,struct,os
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,'/home/user/Pokemon-Outlaw-Mod/tools')
from inc import *
from leg1 import r32,header
from shinigami import SB,put_script,quant
from g3 import ENC
import gfx
import story_ids as I
import story_text as ST
import story_native as SN
RESULT=0x800D
A=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','story_assets')
TRAINER_ID=530; PIC=68; CAMP=(2,79)
def yesno(S,p): S.raw(0x0f,0); S.ptr(p); S.raw(0x09,5)
def msgs(S,r,*keys):
    for k in keys: S.msg(ST.ptr(r,k),4)
def card(S,r,text): S.msg(ST.ptr_s(r,text),4)
_n=[0]
def lab(p): _n[0]+=1; return '%s%d'%(p,_n[0])
def rep_add(S,n):
    """story reputation adjustment (VAR_REPADJ is 1000 + adjustment; rep_calc folds it into VAR_REP)"""
    S.raw(0x17 if n>=0 else 0x18); S._add(struct.pack('<HH',I.VAR_REPADJ,abs(n)))
def epilogue(r):
    """subroutine (ends with return): the closing cards"""
    S=SB()
    S.msg(ST.ptr(r,'epi_war'),4)
    s_a,s_b=lab('n'),lab('n')
    S.compare(I.VAR_NERO,1); S.goto_if(5,s_a); S.msg(ST.ptr(r,'epi_trial'),4); S.lab(s_a)
    S.compare(I.VAR_NERO,3); S.goto_if(5,s_b); S.msg(ST.ptr(r,'epi_crowned'),4); S.lab(s_b)
    # Father path: VAR_CHOICE 1
    S.compare(I.VAR_CHOICE,1); S.goto_if(1,'fa')
    S.compare(I.VAR_YV,2); S.goto_if(1,'tamed'); S.compare(I.VAR_YV,3); S.goto_if(1,'slain')
    S.msg(ST.ptr(r,'epi_none'),4); S.goto('title')
    S.lab('tamed'); S.msg(ST.ptr(r,'epi_tamed'),4); S.goto('title')
    S.lab('slain'); S.msg(ST.ptr(r,'epi_godslayer'),4); S.goto('title')
    S.lab('fa')
    S.compare(I.VAR_NERO,1); S.goto_if(1,'tried')
    msgs(S,r,'father_end_monster'); S.clearflag(I.F_FATHER_ALIVE); S.msg(ST.ptr(r,'epi_father_gone'),4); S.goto('title')
    S.lab('tried')
    S.compare(I.VAR_REP,100); S.goto_if(0,'sacr')
    msgs(S,r,'father_end_proud'); S.msg(ST.ptr(r,'epi_father_stays'),4); S.goto('title')
    S.lab('sacr'); msgs(S,r,'father_end_sacrifice'); S.msg(ST.ptr(r,'epi_father_stays'),4)
    S.lab('title')
    # one title: Godslayer, Kingslayer, Bloody (very low reputation), Kind (high reputation)
    S.compare(I.VAR_YV,3); S.goto_if(1,'t_god')
    S.compare(I.VAR_NERO,2); S.goto_if(4,'t_king')
    S.compare(I.VAR_REP,I.REP_BLOODY); S.goto_if(3,'t_blood')
    S.compare(I.VAR_REP,I.REP_KIND); S.goto_if(4,'t_kind')
    S.goto('fin')
    for name,key in (('t_god','title_godslayer'),('t_king','title_kingslayer'),('t_blood','title_bloody'),('t_kind','title_kind')):
        S.lab(name); S.msg(ST.ptr_s(r,['Title earned:\n'+ST._J[key][0]]),4); S.goto('fin')
    S.lab('fin'); S.msg(ST.ptr(r,'epi_end'),4); S.setflag(I.F_ENDED); S.raw(0x03)
    return 0x08000000+put_script(r,S)
def nero_pic(r):
    from PIL import Image
    im=Image.open(os.path.join(A,'chars','nero_pic.png')).convert('RGBA'); assert im.size==(64,64)
    rep,pal=quant(im,15)
    idx=[[(pal.index(rep[im.getpixel((x,y))[:3]])+1) if im.getpixel((x,y))[3]>=128 else 0 for x in range(64)] for y in range(64)]
    fa=0x23957c+8*PIC; pa=0x239a1c+8*PIC
    assert struct.unpack('<HH',r.b[fa+4:fa+8])==(0x800,PIC)
    r.w32(fa,0x08000000+r.alloc(gfx.lz_comp(gfx.pixels_to_tiles(idx)),4))
    r.w32(pa,0x08000000+r.alloc(gfx.lz_comp(gfx.rgb_to_pal([(115,197,164)]+pal+[(0,0,0)]*(15-len(pal)))),4))
def rename_gore(r):
    """every text that names GENERAL GORE (quest log, Hall of Justice, the old camp lines) says NERO (same length, edited in place; 'GOREBYSS' is left alone)"""
    pat=bytes(ENC[c] for c in 'GORE'); new=bytes(ENC[c] for c in 'NERO'); n=0; i=0
    while True:
        i=bytes(r.b).find(pat,i+1)
        if i<0: break
        nxt=r.b[i+4]
        if 0xBB<=nxt<=0xEE: continue      # GOREBYSS
        r.b[i:i+4]=new; n+=1
    print('GORE -> NERO in',n,'texts')
def install(r):
    rename_gore(r)
    e=0x798790+40*TRAINER_ID
    assert bytes(r.b[e+4:e+8])==bytes(ENC[c] for c in 'NERO')      # renamed by rename_gore with the texts
    r.b[e+4:e+16]=bytes(ENC[c] for c in 'NERO')+b'\xff'*8
    nero_pic(r)
    if os.environ.get('NERO_TEST'):      # TEST BUILDS ONLY: a single level 2 CATERPIE
        pd=r32(r,e+36)-0x08000000; r.b[e+32]=1; r.b[pd:pd+8]=struct.pack('<HBBHH',255,2,0,10,0)
    # find the General's object and its old script
    h=header(r,*CAMP); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000; obj=None
    for i in range(r.b[ev]):
        t=po+24*i; sp=r32(r,t+16)-0x08000000
        if r.b[sp]==0x5c and r.b[sp+1]==1 and struct.unpack('<H',r.b[sp+2:sp+4])[0]==TRAINER_ID: obj=t
    assert obj
    old=r32(r,obj+16)-0x08000000
    cont=r32(r,old+0x0e)-0x08000000                # trainerbattle continue pointer
    assert r.b[cont]==0x2b
    flag_cleared=struct.unpack('<H',r.b[cont+1:cont+3])[0]; again=r32(r,cont+5)
    flags=[]; a=cont+9
    while r.b[a]==0x29: flags.append(struct.unpack('<H',r.b[a+1:a+3])[0]); a+=3
    assert len(flags)==11,flags
    while r.b[a]==0x0f: a+=8                        # the three old messages
    assert r.b[a:a+2]==bytes([0x97,1]) and r.b[a+2]==0x39
    warp=bytes(r.b[a:a+11]); print('warp tail',warp.hex(' '))
    epi=epilogue(r)
    S=SB()
    S.raw(0x5c,1); S._add(struct.pack('<HH',TRAINER_ID,0)); S.ptr(ST.ptr(r,'nero_spot')); S.ptr(ST.battle_ptr(r,"NERO: Then finish it. ")); S.ref('cont')
    S.msg(ST.ptr_s(r,["NERO: I have nothing left to command.\nGo."]),6); S.end()
    S.lab('cont')
    S.raw(0x2b); S._add(struct.pack('<H',flag_cleared)); S.goto_if(1,'again')
    for f in flags: S.setflag(f)
    S.msg(ST.ptr(r,'nero_defeated'),4); S.msg(ST.ptr(r,'nero_choice_prompt'),4)
    yesno(S,ST.ptr_s(r,["ARREST him for trial?\nYES: arrest. NO: other."]))
    S.compare(RESULT,1); S.goto_if(1,'arrest')
    yesno(S,ST.ptr_s(r,["EXECUTE him?\nYES: execute. NO: be crowned."]))
    S.compare(RESULT,1); S.goto_if(1,'execute')
    S.setvar(I.VAR_NERO,3); S.msg(ST.ptr(r,'nero_crowned'),4); rep_add(S,-10); S.goto('after')
    S.lab('execute'); S.setvar(I.VAR_NERO,2); S.msg(ST.ptr(r,'nero_execute'),4); rep_add(S,-30); S.goto('after')
    S.lab('arrest'); S.setvar(I.VAR_NERO,1); S.msg(ST.ptr(r,'nero_arrest'),4); rep_add(S,20)
    S.lab('after')
    S.setvar(I.VAR_STORY,5)
    S.raw(0x23); S.ptr(SN.addrs(r)['rep_calc'])
    S.raw(0x04); S.ptr(epi)
    S.setvar(I.VAR_STORY,6)
    S._add(warp); S.end()
    S.lab('again'); S.msg(ST.ptr_s(r,["NERO: I have nothing left to command.\nGo."]),6); S.end()
    r.w32(obj+16,0x08000000+put_script(r,S))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
