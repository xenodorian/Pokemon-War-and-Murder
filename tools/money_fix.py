"""Money bug in THREATEN (usage: money_fix.py IN.gba OUT.gba), run through tools/patch.sh.
Cause of 'my money randomly maxed out': the bystander THREATEN native (story/bystander_native.c by_threat, ROM 0x8FEFC61) added its 50..200 reward straight onto the raw money word
at SaveBlock1+0x290. Money is stored XOR the save's encryption key (the key is non-zero in this ROM: item counts show it as 0x1587), so adding to or clamping the raw word makes the real
amount random and usually huge. Every other money writer (rob, sell, JRA pay) goes through the game's own AddMoney (0x0809FDA0), as does this fix.
The patch replaces the raw read-compare-store block (0xFEFCB6..0xFEFCD9) with: compute the amount, call a helper (free space) that runs AddMoney on SB1+0x290 and stores the amount for the message (GSV0)."""
import sys,os,struct
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
A=0xFEFCB6; B=0xFEFCDA
EXPECT_HEAD=bytes.fromhex('29210901')          # movs r1,#0x29 ; lsls r1,r1,#4
def install(r):
    b=r.b
    assert bytes(b[A:A+4])==EXPECT_HEAD,bytes(b[A:A+4]).hex()
    assert bytes(b[B-2:B])==bytes.fromhex('0880'),bytes(b[B-2:B]).hex()   # strh r0,[r1] (GSV0 = amount) is the last instruction of the block
    helper=r.asm('''
push {r4,lr}
movs r4,r0
ldr r1,=0x03005008
ldr r1,[r1]
movs r2,#0x29
lsls r2,r2,#4
adds r0,r1,r2
movs r1,r4
ldr r3,=0x0809fda1
bl callr3
ldr r1,=0x020370b8
strh r4,[r1]
pop {r4}
pop {r0}
bx r0
callr3: bx r3
.ltorg
''',(r.cur+3)&~3)
    h=r.alloc(helper,4)
    # amount = 0x32 + ((rnd*0x97)>>16)  (rnd is in r0 here), then bl helper, nops to the end of the block
    code=bytes.fromhex('9723'+'4343'+'1b0c'.replace('1b0c','180c'))   # movs r3,#0x97 ; muls r3,r0,r3 ; lsrs r0,r3,#16
    code+=struct.pack('<H',0x3000|(0<<8)|0x32)                          # adds r0,#0x32
    pad=b'\xc0\x46'
    blk=bytearray(code)+bytearray(4)+bytearray(pad*((B-A-len(code)-4)//2))
    b[A:B]=blk
    r.bl(A+len(code),h)
    print('helper at',hex(h),'block',hex(A),'..',hex(B))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
