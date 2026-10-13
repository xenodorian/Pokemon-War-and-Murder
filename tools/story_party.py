"""Native routines for FATHER's second team (usage: story_party.py IN.gba OUT.gba; also importable: install(r) -> dict(make=addr, swap=addr)).
Father's team lives in PC box 14 (slots 1..6, named FATHER), so it is saved and visible in the PC.
 make: creates six POKeMON at the player's average party level (min 10) into box 14. Called once when Father is revived.
 swap: swaps the party with the six box 14 slots (80 byte BoxPokemon copy), then zeroes the 20 byte party tail and runs CalculateMonStats on each non-empty slot
       (mons arrive at full HP), recounts gPlayerPartyCount. Call from a script with callnative.
FireRed addresses: gPlayerParty 0x02024284, gPlayerPartyCount 0x02024029, gPokemonStoragePtr 0x03005010 (boxes at +4, 30*80 bytes each, names at +0x8344),
CreateMon 0x0803DA55, ZeroMonData 0x0803D995, CalculateMonStats 0x0803E47D, GetMonData 0x0803FBE9."""
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
from g3 import ENC
FATHER_TEAM=[28,34,59,53,112,65]       # SANDSLASH NIDOKING ARCANINE PERSIAN RHYDON ALAKAZAM
BOX14=4+13*30*80
NAME_OFF=0x8344+13*9
COMMON='''
copy80: movs r2,#20
c80: ldmia r1!,{r3}
stmia r0!,{r3}
subs r2,#1
bne c80
bx lr
callr3: bx r3
callr7: bx r7
'''
def make_src(table,name):
    return '''
push {r4-r7,lr}
sub sp,#120
movs r6,#0
movs r4,#0
ldr r0,=0x02024029
ldrb r5,[r0]
cmp r5,#0
beq lvdef
al: cmp r4,r5
bge ad
movs r0,#100
muls r0,r4
ldr r1,=0x02024284
adds r0,r0,r1
movs r1,#0x38
movs r2,#0
ldr r3,=0x0803FBE9
bl callr3
adds r6,r6,r0
adds r4,#1
b al
ad: movs r0,#0
ad2: cmp r6,r5
blt ad3
subs r6,r6,r5
adds r0,#1
b ad2
ad3: cmp r0,#10
bge ok
lvdef: movs r0,#10
ok: str r0,[sp,#116]
ldr r4,=0x03005010
ldr r4,[r4]
ldr r0,=%d
adds r4,r4,r0
ldr r5,=%d
movs r6,#0
mk: cmp r6,#6
bge done
movs r0,#0
str r0,[sp,#0]
str r0,[sp,#4]
str r0,[sp,#12]
movs r0,#1
str r0,[sp,#8]
add r0,sp,#16
ldrh r1,[r5]
ldr r2,[sp,#116]
movs r3,#32
ldr r7,=0x0803DA55
bl callr7
adds r0,r4,#0
add r1,sp,#16
bl copy80
adds r4,#80
adds r5,#2
adds r6,#1
b mk
done: ldr r0,=0x03005010
ldr r0,[r0]
ldr r1,=%d
adds r0,r0,r1
ldr r1,=%d
movs r2,#9
nm: ldrb r3,[r1]
strb r3,[r0]
adds r0,#1
adds r1,#1
subs r2,#1
bne nm
add sp,#120
pop {r4-r7}
pop {r0}
bx r0
%s
.ltorg
'''%(BOX14,table,NAME_OFF,name,COMMON)
def swap_src():
    return '''
push {r4-r7,lr}
sub sp,#80
ldr r4,=0x03005010
ldr r4,[r4]
ldr r0,=%d
adds r4,r4,r0
ldr r5,=0x02024284
movs r6,#0
sw: cmp r6,#6
bge sdone
mov r0,sp
adds r1,r5,#0
bl copy80
adds r0,r5,#0
adds r1,r4,#0
bl copy80
adds r0,r4,#0
mov r1,sp
bl copy80
adds r5,#100
adds r4,#80
adds r6,#1
b sw
sdone: movs r6,#0
movs r7,#0
ldr r5,=0x02024284
fx: cmp r6,#6
bge fdone
movs r0,#0
movs r1,#80
adds r1,r5,r1
movs r2,#5
zt: stmia r1!,{r0}
subs r2,#1
bne zt
adds r0,r5,#0
movs r1,#0x0b
movs r2,#0
ldr r3,=0x0803FBE9
bl callr3
cmp r0,#0
bne have
adds r0,r5,#0
ldr r3,=0x0803D995
bl callr3
b nxt
have: adds r0,r5,#0
ldr r3,=0x0803E47D
bl callr3
adds r7,#1
nxt: adds r5,#100
adds r6,#1
b fx
fdone: ldr r0,=0x02024029
strb r7,[r0]
add sp,#80
pop {r4-r7}
pop {r0}
bx r0
%s
.ltorg
'''%(BOX14,COMMON)
def install(r):
    table=r.alloc(b''.join(struct.pack('<H',s) for s in FATHER_TEAM),2)
    name=r.alloc(bytes(ENC[c] for c in 'FATHER')+b'\xff\xff\xff',1)
    out={}
    for k,src in (('make',make_src(0x08000000+table,0x08000000+name)),('swap',swap_src())):
        r.cur=(r.cur+3)&~3
        a=r.cur; code=r.asm(src,a)
        import capstone
        for i in capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB).disasm(code[:code.index(b'\x70\x47')+2],a):
            assert i.size==2 or i.mnemonic=='bl',(i.mnemonic,i.op_str)
        r.alloc(code,4); out[k]=0x08000000+a+1
    return out
if __name__=='__main__':
    r=Rom(sys.argv[1]); print({k:hex(v) for k,v in install(r).items()}); r.save(sys.argv[2])
