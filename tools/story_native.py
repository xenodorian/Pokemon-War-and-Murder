"""Shinigami storyline: native code (usage: story_native.py IN.gba OUT.gba), source story/story_native.c
 - reputation: rep_calc() = clamp(100 + blessings - kills + (VAR_REPADJ - 1000), 0..200), written to VAR_REP. Shop prices (the item price getter at 0x9a916) are scaled
   +1%/point below 100 and -1%/point above; at 0 the pokemart script command (table entry 0x86) refuses with the shopkeeper's line.
 - MAX fights as herself: before every battle (hook at the CreateTask call of the battle start task 0x7f6a2) with no usable POKeMON in the party MAX (species 255, Lv 1) joins
   if there is room; she leaves again once a usable POKeMON exists, and in the white-out script.
 - the table 'STORYFN1' (rep_calc, max_remove, max_prepare) tells later steps the addresses (addrs(r))."""
import sys,struct,subprocess,os
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from inc import *
from shinigami import SB,put_script
import story_text as ST
HERE=os.path.dirname(os.path.abspath(__file__)); SRC=os.path.join(HERE,'..','story'); WORK='/tmp/story_build'
PRICE_SITE=0x9a916; BATTLE_SITE=0x7f6a2; CMD_TABLE=0x15F9B4; POKEMART=0x86
TRAMP_FREE=[0x3b2450,0x3b2480,0x3b24b0]      # free padding runs inside BL range of the hook sites (see CURRENT_WORK.md)
MAGIC=b'STORYFN1'
def addrs(r):
    i=bytes(r.b).find(MAGIC,0xA00000)
    assert i>0,'story_native not applied'
    return dict(zip(('rep_calc','max_remove','max_prepare'),struct.unpack('<3I',r.b[i+8:i+20])))
def tramp(r,at,target):
    assert bytes(r.b[at:at+8])==b'\xff'*8,hex(at)
    r.b[at:at+8]=bytes([0x00,0x4b,0x18,0x47])+struct.pack('<I',target)
def install(r):
    os.makedirs(WORK,exist_ok=True)
    S=SB(); S.msg(ST.ptr(r,'rep_refuse'),4); S.releaseall(); S.end(); refuse=0x08000000+put_script(r,S)
    orig=r32(r,CMD_TABLE+4*POKEMART)
    assert orig==0x806c3ad,hex(orig)
    open(os.path.join(SRC,'story_gen.h'),'w').write('#define ORIG_POKEMART 0x%08x\n#define REFUSE_SCRIPT 0x%08x\n'%(orig,refuse))
    r.cur=(r.cur+3)&~3; base=0x08000000+r.cur
    ld=os.path.join(WORK,'story.ld')
    open(ld,'w').write('ENTRY(rep_calc)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%base)
    o=os.path.join(WORK,'story.o'); e=os.path.join(WORK,'story.elf'); bn=os.path.join(WORK,'story.bin')
    subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-c',os.path.join(SRC,'story_native.c'),'-o',o],check=True)
    subprocess.run(['ld.lld','-T',ld,o,'-o',e],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',e,bn],check=True)
    a=r.alloc(open(bn,'rb').read(),4); assert 0x08000000+a==base
    sym={}
    for ln in subprocess.run(['nm',e],capture_output=True,text=True,check=True).stdout.split('\n'):
        f=ln.split()
        if len(f)==3: sym[f[2]]=int(f[0],16)
    fn=lambda n:(sym[n]&~1)|1
    # price hook: replaces 'ldrh r0,[r0,#0x10]; pop {r4}' of the item price getter
    assert bytes(r.b[PRICE_SITE:PRICE_SITE+4])==bytes([0x00,0x8a,0x10,0xbc]),bytes(r.b[PRICE_SITE:PRICE_SITE+4]).hex()
    r.cur=(r.cur+3)&~3; p1=r.cur
    r.alloc(r.asm('ldrh r0,[r0,#0x10]\npush {lr}\nbl 0x%x\npop {r3}\npop {r4}\nbx r3\n'%(sym['scale_price']&~1),p1),4)
    tramp(r,TRAMP_FREE[0],0x08000000+p1+1); r.bl(PRICE_SITE,TRAMP_FREE[0])
    # battle start hook
    assert bytes(r.b[BATTLE_SITE:BATTLE_SITE+4])==struct.pack('<HH',0xF000|((0x7741c-(BATTLE_SITE+4))>>12&0x7FF),0xF800|(((0x7741c-(BATTLE_SITE+4))>>1)&0x7FF))
    r.cur=(r.cur+3)&~3; p2=r.cur
    r.alloc(r.asm('push {r0,r1,lr}\nbl 0x%x\npop {r0,r1,r3}\npush {r3}\nldr r2,=0x0807741D\nbl callr2\npop {r3}\nbx r3\ncallr2: bx r2\n.ltorg\n'%(sym['max_prepare']&~1),p2),4)
    tramp(r,TRAMP_FREE[1],0x08000000+p2+1); r.bl(BATTLE_SITE,TRAMP_FREE[1])
    # shop command
    r.w32(CMD_TABLE+4*POKEMART,fn('shop_cmd'))
    r.alloc(MAGIC+struct.pack('<3I',fn('rep_calc'),fn('max_remove'),fn('max_prepare')),4)
    return dict(rep_calc=fn('rep_calc'))
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
if __name__=='__main__':
    r=Rom(sys.argv[1]); print(install(r)); r.save(sys.argv[2]); print('end',hex(r.cur))
