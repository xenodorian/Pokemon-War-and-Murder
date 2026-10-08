# usage: leg2.py in.gba out.gba
# Leg 2, part 1: Kill Count start-menu entry (kills / bless / karma), BLESS TAG item sold in every PokeMart, and the Bless option on defeated trainers.
import sys,struct,subprocess
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import leg1,shinigami,qconsts
from g3 import ENC
from shinigami import SB,put_script
W='/home/claude/work/leg2'
FLAGS,VARS,ITEMS=qconsts.consts()
BLESS_ITEM=56; ITEM_BASE=0x3db028; ICONT=0x3d4294
ITEM_GLOCK=52
SYM={'rob_info':0x08a09939,'rob_pay':0x08a09a49,'shoot_do':0x08a09b61}
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
def etxt(s): return bytes(ENC[c] for c in s)+b'\xff'
# consumable pool: vitamins count three times
VIT=['ITEM_HP_UP','ITEM_PROTEIN','ITEM_IRON','ITEM_CARBOS','ITEM_CALCIUM','ITEM_ZINC']
ONE=['ITEM_POTION','ITEM_SUPER_POTION','ITEM_HYPER_POTION','ITEM_MAX_POTION','ITEM_FULL_RESTORE','ITEM_REVIVE','ITEM_MAX_REVIVE','ITEM_ANTIDOTE','ITEM_BURN_HEAL','ITEM_ICE_HEAL','ITEM_AWAKENING','ITEM_PARALYZE_HEAL','ITEM_FULL_HEAL','ITEM_ETHER','ITEM_MAX_ETHER','ITEM_ELIXIR','ITEM_MAX_ELIXIR','ITEM_REPEL','ITEM_SUPER_REPEL','ITEM_MAX_REPEL','ITEM_ESCAPE_ROPE','ITEM_X_ATTACK','ITEM_X_DEFEND','ITEM_X_SPEED','ITEM_X_ACCURACY','ITEM_X_SPECIAL','ITEM_GUARD_SPEC','ITEM_DIRE_HIT','ITEM_RARE_CANDY','ITEM_PP_UP','ITEM_PP_MAX','ITEM_FRESH_WATER','ITEM_SODA_POP','ITEM_LEMONADE','ITEM_MOOMOO_MILK','ITEM_ENERGY_POWDER','ITEM_ENERGY_ROOT','ITEM_HEAL_POWDER','ITEM_REVIVAL_HERB']
def pool():
    p=[]
    for n in ONE: p.append(ITEMS[n])
    for n in VIT: p+= [ITEMS[n]]*3
    p+=[54,55]                    # the two MUTAGENs from this hack
    return p
def build_native(r):
    pl=pool()
    import os
    sg=os.environ.get('SIGNSEQ','174,0').split(','); open(W+'/leg2_data.h','w').write('#define SIGN0 %s\n#define SIGN1 %s\n'%(sg[0],sg[1])+'static const u8 T_KILLS[]={%s};\nstatic const u8 T_BLESS[]={%s};\nstatic const u8 T_KARMA[]={%s};\n#define NPOOL %d\nstatic const u16 ITEM_POOL[]={%s};\n'%
        (','.join(map(str,etxt('KILL COUNT: '))),','.join(map(str,etxt('BLESS COUNT: '))),','.join(map(str,etxt('KARMA: '))),len(pl),','.join(map(str,pl))))
    r.cur=(r.cur+3)&~3; base=0x08000000+r.cur
    open(W+'/leg2.ld','w').write('ENTRY(kc_show)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%base)
    subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-c',W+'/leg2.c','-o',W+'/leg2.o'],check=True)
    subprocess.run(['ld.lld','-T',W+'/leg2.ld',W+'/leg2.o','-o',W+'/leg2.elf'],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',W+'/leg2.elf',W+'/leg2.bin'],check=True)
    a=r.alloc(open(W+'/leg2.bin','rb').read(),4); assert 0x08000000+a==base
    out={}
    for ln in subprocess.run(['nm',W+'/leg2.elf'],capture_output=True,text=True,check=True).stdout.split('\n'):
        f=ln.split()
        if len(f)==3 and f[2] in ('kc_show','karma_check','bless_do'): out[f[2]]=(int(f[0],16)&~1)|1
    assert len(out)==3
    return out
# ---------------------------------------------------------------- start menu entry
def menu_entry(r,fns):
    b=r.b
    thunk1=r.alloc(bytes([0x08,0x47]),4); thunk2=r.alloc(bytes([0x10,0x47]),4)
    def call(t): return 'ldr r1,=%d\nbl %d\n'%(0x08000000+t+1,0x08000000+thunk1)
    t_name=0x08000000+r.alloc(etxt('KILL COUNT'),1)
    t_desc=0x08000000+r.alloc(etxt('See your kills, blessings\nand karma.').replace(bytes([ENC[' '],0xff]),b'') if False else bytes(ENC[c] if c!='\n' else 0xFE for c in 'See your kills, blessings\nand karma.')+b'\xff',1)
    # the script
    S=SB(); S.lockall(); S.raw(0x23); S.ptr(fns['kc_show']); S.msg(0x02021cd0); S.releaseall(); S.end()
    entry=put_script(r,S)
    cb=r.fn('push {lr}\n'+call(0x6ef18)+call(0xf7998)+call(0x6fea0)+'ldr r0,=%d\n'%(0x08000000+entry)+call(0x69ae4)+'movs r0,#1\npop {r1}\nbx r1\n')
    # relocate the action and description tables with one more entry each
    acts_old=r32(r,0x6ef9c)-0x08000000; assert r32(r,0x6f374)==0x08000000+acts_old and r32(r,0x6f3f8)==0x08000000+acts_old
    acts=bytes(b[acts_old:acts_old+88])+struct.pack('<II',t_name,0x08000000+cb+1)
    na=r.alloc(acts,4)
    for lit in (0x6ef9c,0x6f374,0x6f3f8): r.w32(lit,0x08000000+na)
    desc_old=r32(r,0x6f138)-0x08000000; assert r32(r,0x6f368)==0x08000000+desc_old
    nd=r.alloc(bytes(b[desc_old:desc_old+44])+struct.pack('<I',t_desc),4)
    for lit in (0x6f138,0x6f368): r.w32(lit,0x08000000+nd)
    # menu tail: add action 11 after RENAME (action 10)
    def ac(n): return 'movs r0,#%d\n'%n+call(0x6ed94)
    tail=r.fn(ac(2)+ac(9)+ac(10)+ac(11)+ac(3)+ac(4)+ac(5)+ac(6)+'pop {r0}\nbx r0\n')
    assert r32(r,0x6edec)!=0
    r.w32(0x6edec,0x08000000+tail+1)
    # fade exemption: our callbacks keep the menu from fading out
    cb_q=struct.unpack('<I',acts[72+4:72+8])[0]; cb_r=struct.unpack('<I',acts[80+4:80+8])[0]
    fade=r.fn('push {lr}\nldr r0,=0x20370f0\nldr r1,[r0]\n'+
      ''.join('ldr r0,=%d\ncmp r1,r0\nbeq done\n'%v for v in (cb_q,cb_r,0x08000000+cb+1,0x0806f4e9,0x0806f541,0x0806f555))+
      call(0x0ccb68)+'movs r0,#1\nmovs r1,#0\nldr r2,=%d\nbl %d\n'%(0x0807a818+1,0x08000000+thunk2)+'done:\npop {r0}\nbx r0\n')
    assert r32(r,0x6f398)!=0
    r.w32(0x6f398,0x08000000+fade+1)
# ---------------------------------------------------------------- BLESS TAG item in every PokeMart
def bless_item(r):
    b=r.b; o=ITEM_BASE+44*BLESS_ITEM
    assert b[o:o+9]==bytes([0xac])*8+b'\xff' and struct.unpack('<H',b[o+14:o+16])[0]==0
    src=ITEM_BASE+44*ITEMS['ITEM_CLEANSE_TAG']
    rec=bytearray(b[src:src+44]); name=etxt('BLESS TAG')
    rec[0:14]=name.ljust(14,b'\x00'); rec[14:16]=struct.pack('<H',BLESS_ITEM); rec[16:18]=struct.pack('<H',1000); rec[18]=0; rec[19]=0
    rec[20:24]=struct.pack('<I',0x08000000+r.alloc(bytes(ENC[c] if c!='\n' else 0xFE for c in 'A blessed charm. Use it on a\ndefeated TRAINER to bless them.')+b'\xff',1))
    b[o:o+44]=rec
    ic=ICONT+8*BLESS_ITEM; ics=ICONT+8*ITEMS['ITEM_CLEANSE_TAG']
    r.w32(ic,r32(r,ics)); r.w32(ic+4,r32(r,ics+4))
def marts(r):
    b=r.b; sig=[52,53,54,55,64,67,68]; lists={}
    for q in range(0,len(b)-8):
        if b[q]==0x86 and b[q+4]==0x08:
            p=r32(r,q+1)
            if not(0x08000000<=p<0x08000000+len(b)-100): continue
            a=p-0x08000000; ids=[]; k=a
            while len(ids)<40:
                v=struct.unpack('<H',b[k:k+2])[0]
                if v==0: break
                ids.append(v); k+=2
            if len(ids)>=8 and ids[-7:]==sig and ids[0] in (2,3,4): lists.setdefault(p,[]).append(q)
    print('mart lists',len(lists),'sites',sum(len(v) for v in lists.values())); assert len(lists)>=14
    for p,sites in lists.items():
        a=p-0x08000000; ids=[]; k=a
        while struct.unpack('<H',b[k:k+2])[0]: ids.append(struct.unpack('<H',b[k:k+2])[0]); k+=2
        new=r.alloc(struct.pack('<%dH'%(len(ids)+2),*(ids+[BLESS_ITEM,0])),4)
        for q in sites: r.w32(q+1,0x08000000+new)
# ---------------------------------------------------------------- defeated-trainer script with the Bless option
def trainer_script(r,fns):
    b=r.b
    assert b[0x1a4ed7:0x1a4ed9]==bytes([0x06,0x05]),b[0x1a4ed7:0x1a4edd].hex()
    T=lambda s: 0x08000000+r.alloc(leg1.enc(s),1)
    t_askrob=T('Point your GLOCK at this\nTRAINER and rob them?')
    t_dont=T("Don't shoot! Here, take\neverything I have!")
    t_took=0x08000000+r.alloc(leg1.enc('You took $')[:-1]+b'\xfd\x02'+leg1.enc('!'),1)
    t_nothing=T("They've got nothing left\nto give.")
    t_askshoot=T('Shoot them anyway?\nThis uses one 9MM ROUND.')
    t_mons=T('You took their POKéMON!')
    t_ask=T('Bless this TRAINER with a\nBLESS TAG?')
    t_thanks=T('Thank you for the blessings, my sins feel cleansed! Here, as a token of my gratitude, have an item!')
    ITEM_9MM=53; SE_SHOT=347; pk=lambda v: struct.pack('<H',v)
    S=SB()
    S.raw(0x23); S.ptr(SYM['rob_info'])
    S.compare(0x8006,0); S.goto_if(1,'normal')
    S.raw(0x47); S._add(pk(BLESS_ITEM)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'rob')
    S.compare(0x8004,1); S.goto_if(1,'rob')
    S.compare(0x8005,0); S.goto_if(1,'rob')
    S.msg(t_ask,5); S.compare(0x800d,0); S.goto_if(1,'rob')
    S.raw(0x45); S._add(pk(BLESS_ITEM)+pk(1))
    S.raw(0x23); S.ptr(fns['bless_do'])
    S.msg(t_thanks); S.raw(0x09,0); S.goto('done')
    S.lab('rob')
    S.raw(0x47); S._add(pk(ITEM_GLOCK)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'normal')
    S.compare(0x8004,1); S.goto_if(1,'already')
    S.msg(t_askrob,5); S.compare(0x800d,0); S.goto_if(1,'normal')
    S.raw(0x23); S.ptr(SYM['rob_pay'])
    S.msg(t_dont); S.msg(t_took); S.goto('shootask')
    S.lab('already'); S.msg(t_nothing)
    S.lab('shootask')
    S.compare(0x8005,0); S.goto_if(1,'done')
    S.raw(0x47); S._add(pk(ITEM_9MM)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'done')
    S.msg(t_askshoot,5); S.compare(0x800d,0); S.goto_if(1,'done')
    S.raw(0x45); S._add(pk(ITEM_9MM)+pk(1))
    S.playse(SE_SHOT); S.raw(0x30)
    S.raw(0x53); S._add(pk(0x800f))
    S.raw(0x23); S.ptr(SYM['shoot_do'])
    S.raw(0x55); S._add(pk(0x800f))
    S.compare(0x8007,0); S.goto_if(1,'noprt'); S.raw(0x53); S._add(pk(0x8007)); S.raw(0x55); S._add(pk(0x8007))
    S.lab('noprt'); S.msg(t_mons)
    S.lab('done'); S.release(); S.end()
    S.lab('normal'); S.raw(0x5e)
    r.w32(0x1a4ed9,0x08000000+put_script(r,S))
if __name__=='__main__':
    r=Rom(sys.argv[1])
    fns=build_native(r); bless_item(r); marts(r); trainer_script(r,fns)
    import json; json.dump(fns,open(W+'/fns.json','w'))
    r.save(sys.argv[2]); print('fns',{k:hex(v) for k,v in fns.items()},'end',hex(r.cur))
