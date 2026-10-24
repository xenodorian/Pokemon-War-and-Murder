"""Restore SHOOT for ordinary trainers (usage: ordinary_shoot.py IN.gba OUT.gba), run through tools/patch.sh.
liberty.py gave ordinary trainers a three-row BLESS / THREATEN / LEAVE menu ('never shoot'), which removed the shoot option the base game had for them (a misunderstanding; the owner wants it back).
The ordinary menu entry ('omenu' in the live post-battle front script at 0x08F8CEC0) now jumps to a new script that picks the original rows again (78 all live, 79 shoot grey when the trainer cannot be shot,
80 bless and threaten grey after one was used, 81 all grey) after the original deal gate (the police deal makes civilians unshootable), and sends BLESS and THREATEN to the live liberty handlers unchanged.
SHOOT is the original shoot block of the old script (0x08F31D3C, texts and natives read from it): needs GLOCK and 9MM ROUND, takes the trainer's money first if not already robbed, takes the round,
gunshot, the shoot native (their party is taken), partner removed. Failure texts return to the new menu. JRA troopers and captains are unchanged."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
from shinigami import SB,put_script
FRONT=0xF8CEC0
ROB_INFO=0x08A09939; DEAL_GATE=0x08F22E0D; DEAL_STATE=0x08F22DED; ROB_PAY=0x08A09A49; SHOOT_DO=0x08F87085
OLD=0x0F31D3C
def r32(b,o): return struct.unpack('<I',b[o:o+4])[0]
def install(r):
    b=r.b
    # texts of the old shoot block (loadword = 0f 00 ptr)
    def txt(o):
        assert b[o]==0x0f and b[o+1]==0,hex(o); return r32(b,o+2)
    t_pay1=txt(OLD+0x3b); t_pay2=txt(OLD+0x43); t_took=txt(OLD+0x70); t_cant=txt(OLD+0x8a); t_police=txt(OLD+0x97); t_need=txt(OLD+0xa4)
    assert b[OLD+0x36]==0x23 and r32(b,OLD+0x37)==ROB_PAY and b[OLD+0x57]==0x23 and r32(b,OLD+0x58)==SHOOT_DO,'old shoot block changed'
    # the live ordinary menu in the front script
    hay=bytes(b[FRONT:FRONT+0x700])
    pat=bytes([0x23])+struct.pack('<I',ROB_INFO)+bytes([0x21,0x04,0x80,0x00,0x00,0x06,0x01])
    i=hay.find(pat); assert i>0 and hay.find(pat,i+1)<0,'omenu not found'
    k=i+12
    # after the two menu pushes: compare 800D 0 -> bless, 1 -> threaten, goto leave
    pb=bytes([0x21,0x0D,0x80,0x00,0x00,0x06,0x01]); pt=bytes([0x21,0x0D,0x80,0x01,0x00,0x06,0x01])
    jb=hay.find(pb,k); assert 0<jb<k+80
    jt=hay.find(pt,jb); assert jt==jb+11
    assert hay[jt+11]==0x05
    bless=r32(hay,jb+7); threat=r32(hay,jt+7); leave=r32(hay,jt+12)
    S=SB(); S.lab('top')
    S.raw(0x23); S.ptr(ROB_INFO); S.raw(0x23); S.ptr(DEAL_GATE)
    S.compare(0x8004,0); S.goto_if(1,'fresh')
    S.compare(0x8005,0); S.goto_if(1,'d_ns')
    S.raw(0x6F,0,0,80,0); S.goto('res')
    S.lab('d_ns'); S.raw(0x6F,0,0,81,0); S.goto('res')
    S.lab('fresh'); S.compare(0x8005,0); S.goto_if(1,'f_ns')
    S.raw(0x6F,0,0,78,0); S.goto('res')
    S.lab('f_ns'); S.raw(0x6F,0,0,79,0)
    S.lab('res')
    S.compare(0x800D,0); S.raw(0x06,1); S.ptr(bless)
    S.compare(0x800D,1); S.raw(0x06,1); S.ptr(threat)
    S.compare(0x800D,2); S.goto_if(1,'shoot')
    S.raw(0x05); S.ptr(leave)
    S.lab('shoot')
    S.compare(0x8005,0); S.goto_if(1,'cant')
    for item in (52,53):
        S.raw(0x47); S._add(struct.pack('<HH',item,1)); S.compare(0x800D,0); S.goto_if(1,'need')
    S.compare(0x8004,0); S.goto_if(5,'paid')
    S.raw(0x23); S.ptr(ROB_PAY); S.msg(t_pay1,4); S.msg(t_pay2,4)
    S.lab('paid')
    S.raw(0x45); S._add(struct.pack('<HH',53,1))
    S.raw(0x2F); S._add(struct.pack('<H',347)); S.raw(0x30)
    S.raw(0x53); S._add(struct.pack('<H',0x800F)); S.raw(0x23); S.ptr(SHOOT_DO); S.raw(0x55); S._add(struct.pack('<H',0x800F))
    S.compare(0x8007,0); S.goto_if(1,'nopart')
    S.raw(0x53); S._add(struct.pack('<H',0x8007)); S.raw(0x55); S._add(struct.pack('<H',0x8007))
    S.lab('nopart'); S.msg(t_took,4); S.raw(0x6C); S.raw(0x02)
    S.lab('cant'); S.raw(0x23); S.ptr(DEAL_STATE); S.compare(0x8007,1); S.goto_if(1,'police')
    S.msg(t_cant,4); S.goto('top')
    S.lab('police'); S.msg(t_police,4); S.goto('top')
    S.lab('need'); S.msg(t_need,4); S.goto('top')
    new=0x08000000+put_script(r,S)
    o=FRONT+i; b[o]=0x05; b[o+1:o+5]=struct.pack('<I',new)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
