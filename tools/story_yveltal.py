"""Shinigami storyline part 3: YVELTAL (usage: story_yveltal.py IN.gba OUT.gba)
 - Walking onto the grave at the old Shinigami spot in the tower (2,66) at (11,6) with VAR_CHOICE == 2 and VAR_YV == 0 wakes YVELTAL. Level = highest party level + 5, min 45, max 100.
 - Outcome: caught -> VAR_YV 2 (tamed); knocked out -> 3 (Godslayer); ran -> 1 (the grave works again); blackout -> the white-out script is hooked: VAR_YV 4 means the Bloody ending (game over: text, then a soft reset).
 - VAR_STORY becomes 4 on tamed / beaten."""
import sys,struct
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,'/home/user/Pokemon-Outlaw-Mod/tools')
from inc import *
from leg1 import r32,header
from shinigami import SB,put_script,add_coord
import story_ids as I
import story_text as ST
import story_party as SP
import story_native as SN
RESULT=0x800D
WHITEOUT_PTR=0x7f5ec           # literal holding the white-out script address
def native(r,src):
    import capstone
    r.cur=(r.cur+3)&~3; a=r.cur; code=r.asm(src,a)
    for i in capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB).disasm(code,a):
        assert i.size==2 or i.mnemonic=='bl',(i.mnemonic,i.op_str)
        if i.mnemonic=='bx' and i.op_str in ('r3','lr') : break
    r.alloc(code,4); return 0x08000000+a+1
YV_SETUP='''
push {r4-r7,lr}
ldr r0,=0x02024029
ldrb r5,[r0]
movs r6,#0
movs r4,#0
lp: cmp r4,r5
bge ld
movs r0,#100
muls r0,r4
ldr r1,=0x02024284
adds r0,r0,r1
movs r1,#0x38
movs r2,#0
ldr r3,=0x0803FBE9
bl callr3
cmp r0,r6
ble nx
adds r6,r0,#0
nx: adds r4,#1
b lp
ld: adds r6,#5
cmp r6,#45
bge hi
movs r6,#45
hi: cmp r6,#100
ble go
movs r6,#100
go: movs r0,#%d
adds r1,r6,#0
movs r2,#0
ldr r3,=0x080A029D
bl callr3
pop {r4-r7}
pop {r0}
bx r0
callr3: bx r3
.ltorg
'''%I.SP_YVELTAL
RESET='''
movs r0,#0
svc #0
bx lr
'''
def grave(r,yv_setup,reset):
    S=SB(); S.lockall()
    S.compare(I.VAR_CHOICE,2); S.goto_if(1,'chosen'); S.releaseall(); S.end()
    S.lab('chosen')
    S.msg(ST.ptr(r,'yveltal_rise'),4)
    S.setvar(I.VAR_YV,4)
    S.raw(0x23); S.ptr(yv_setup); S.raw(0xb7)
    S.raw(0x26); S._add(struct.pack('<HH',RESULT,0xb4))     # specialvar RESULT, GetBattleOutcome
    S.compare(RESULT,7); S.goto_if(1,'tamed')
    S.compare(RESULT,1); S.goto_if(1,'beaten')
    S.setvar(I.VAR_YV,1); S.msg(ST.ptr_s(r,["YVELTAL sinks back into the grave.\nThe runes still glow."]),4); S.releaseall(); S.end()
    S.lab('tamed'); S.setvar(I.VAR_YV,2); S.setvar(I.VAR_STORY,4); S.msg(ST.ptr(r,'yveltal_tamed'),4); S.releaseall(); S.end()
    S.lab('beaten'); S.setvar(I.VAR_YV,3); S.setvar(I.VAR_STORY,4); S.msg(ST.ptr(r,'yveltal_defeated'),4); S.releaseall(); S.end()
    add_coord(r,2,66,11,6,I.VAR_YV,0,0x08000000+put_script(r,S))
    h=header(r,2,66); ev=r32(r,h+4)-0x08000000; cp=r32(r,ev+12)-0x08000000; r.b[cp+16*(r.b[ev+2]-1)+4]=0      # elevation 0 = any
def whiteout(r,reset):
    orig=r32(r,WHITEOUT_PTR); assert orig==0x081a8dd8,hex(orig)
    fn=SN.addrs(r)
    S=SB(); S.raw(0x23); S.ptr(fn['max_remove'])
    S.compare(I.VAR_YV,4); S.goto_if(1,'dead'); S.raw(0x05); S.ptr(orig)
    S.lab('dead'); S.lockall()
    S.msg(ST.ptr(r,'yveltal_max_dies'),4); S.msg(ST.ptr(r,'epi_bloody'),4); S.msg(ST.ptr(r,'title_bloody'),4); S.msg(ST.ptr(r,'epi_end'),4)
    S.setvar(I.VAR_YV,5); S.raw(0x23); S.ptr(reset); S.end()
    r.w32(WHITEOUT_PTR,0x08000000+put_script(r,S))
def install(r):
    yv=native(r,YV_SETUP); reset=native(r,RESET)
    grave(r,yv,reset); whiteout(r,reset)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
