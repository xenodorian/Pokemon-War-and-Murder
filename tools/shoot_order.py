"""Shoot order (usage: shoot_order.py IN.gba OUT.gba), run through tools/patch.sh after ordinary_shoot.py.
Owner rule: gunshot, blood splatter, then the money, then the Pokemon. Three shoot flows existed:
 - JRA troopers, captains (live front script at 0x08F8CEC0): gunshot, MONEY, splatter and party. The money pair (JRA_PAY + 'You took $') and the splatter group (removeobject, shoot native, addobject) are swapped in place.
 - ordinary trainers (ordinary_shoot.py script): money was first, with the plea 'Don't shoot! Here, take everything I have!'. The shoot section is rebuilt: gunshot, splatter and party (silent), the money if they still had some, 'You took their POKeMON!'. The plea is gone: it made no sense after the shot.
 - the old script (0x08F31D67..0x08F31DAB, still used for officers and unknown trainers): same new order, rearranged in place (same length), no plea.
The shoot native takes the party and makes the splatter in one call, so the party text comes last and the money text before it."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
from shinigami import SB,put_script
JRA_PAY=0x08F22E85; ROB_PAY=0x08A09A49; SHOOT_DO=0x08F87085; DEAL_STATE=0x08F22DED
def r32(b,o): return struct.unpack('<I',b[o:o+4])[0]
def install(r):
    b=r.b
    OLDB=0x0F31D3C
    t_pay2=r32(b,OLDB+0x43+2); t_took=r32(b,OLDB+0x70+2); t_cant=r32(b,OLDB+0x8a+2); t_police=r32(b,OLDB+0x97+2); t_need=r32(b,OLDB+0xa4+2)     # read before the old block is rearranged
    # --- JRA flow: swap A (money) and B (splatter group)
    pat=bytes.fromhex('2f5b0130')+bytes([0x23])+struct.pack('<I',JRA_PAY)
    i=bytes(b).find(pat,0xf8cec0,0xf8cec0+0x700); assert i>0
    o=i+4; A=bytes(b[o:o+13]); B=bytes(b[o+13:o+24])
    assert A[0]==0x23 and A[5]==0x0f and A[13-2:]==bytes([0x09,0x04]) and B[0]==0x53 and B[3]==0x23 and B[8]==0x55,(A.hex(),B.hex())
    b[o:o+24]=B+A
    # --- old script
    OLD=0xf31d67
    chk=bytes(b[OLD:OLD+69])
    assert chk[0]==0x21 and chk[5]==0x06 and r32(b,OLD+7)==0x08f31d87 and chk[11]==0x23 and r32(b,OLD+12)==ROB_PAY,'old block changed'
    pay1=bytes(b[OLD+16:OLD+24]); pay2=bytes(b[OLD+24:OLD+32]); R=bytearray(b[OLD+32:OLD+69])
    assert pay1[0]==0x0f and pay2[0]==0x0f and R[0]==0x45 and R[20:25]==bytes([0x21,0x07,0x80,0x00,0x00]) and r32(b,OLD+32+27)==0x08f31dac,R.hex()
    base=0x08000000+OLD
    M=bytes([0x21,0x04,0x80,0x00,0x00,0x06,0x05])+struct.pack('<I',0x08f31dac)+bytes([0x23])+struct.pack('<I',ROB_PAY)+pay2   # 5+6+5+8 = 24, then 8 filler
    M=M+bytes(8)
    R[27:31]=struct.pack('<I',base+37)          # partner skip goes to the money
    b[OLD:OLD+37]=bytes(R); b[OLD+37:OLD+69]=M
    assert len(M)==32
    # --- ordinary flow
    s1=bytes(b).find(bytes.fromhex('233999a008'+'230d2ef208'+'2104800000'+'0601'),0x1100000)
    assert s1>0
    top=0x08000000+s1
    k=bytes(b).find(bytes.fromhex('210d8002000601'),s1,s1+0x200); assert k>0
    S=SB()
    S.compare(0x8005,0); S.goto_if(1,'cant')
    for item in (52,53):
        S.raw(0x47); S._add(struct.pack('<HH',item,1)); S.compare(0x800D,0); S.goto_if(1,'need')
    S.raw(0x45); S._add(struct.pack('<HH',53,1))
    S.raw(0x2F); S._add(struct.pack('<H',347)); S.raw(0x30)
    S.raw(0x53); S._add(struct.pack('<H',0x800F)); S.raw(0x23); S.ptr(SHOOT_DO); S.raw(0x55); S._add(struct.pack('<H',0x800F))
    S.compare(0x8007,0); S.goto_if(1,'nopart')
    S.raw(0x53); S._add(struct.pack('<H',0x8007)); S.raw(0x55); S._add(struct.pack('<H',0x8007))
    S.lab('nopart')
    S.compare(0x8004,0); S.goto_if(5,'paid')
    S.raw(0x23); S.ptr(ROB_PAY); S.msg(t_pay2,4)
    S.lab('paid'); S.msg(t_took,4); S.raw(0x6C); S.raw(0x02)
    S.lab('cant'); S.raw(0x23); S.ptr(DEAL_STATE); S.compare(0x8007,1); S.goto_if(1,'police')
    S.msg(t_cant,4); S.raw(0x05); S.ptr(top)
    S.lab('police'); S.msg(t_police,4); S.raw(0x05); S.ptr(top)
    S.lab('need'); S.msg(t_need,4); S.raw(0x05); S.ptr(top)
    new=0x08000000+put_script(r,S)
    r.w32(k+7,new)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
