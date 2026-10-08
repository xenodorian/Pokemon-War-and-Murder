# Story police: one officer beside each Shinigami victim. Comment, kill count check, then a fight if the player has shot 10 or more trainers.
import sys,struct,subprocess
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import leg1,shinigami
from leg1 import r32,header
from shinigami import SB,put_script,text,T
W='/home/claude/work/police'
CLASS_POLICE=91; PIC_POLICE=126
# (group,num, cop x,y, trainer id, species, level, name, crime scene comment)
COPS=[
 (3,0,11,14,50,58,5,'OFFICER KEN',"POLICE: A dead ROCKET GRUNT, and a black feather in the blood. Odd.\n\nWho leaves a feather behind? Probably nothing."),
 (3,1,24,22,51,58,10,'OFFICER ROY',"POLICE: Another ROCKET GRUNT, and another black feather. Same as PALLET TOWN.\n\nTwo in a row is no accident."),
 (3,2,25,10,52,58,15,'OFFICER BEN',"POLICE: Another ROCKET grunt, and another black feather. Whoever kills them leaves one behind every time.\n\nA calling card, maybe? I do not know what it means."),
 (3,3,25,14,53,59,20,'OFFICER LEE',"POLICE: There was a black feather by that body too, just like in PALLET, VIRIDIAN and PEWTER.\n\nA killer who signs their work. Maybe the feather means something to them."),
 (3,5,24,22,54,59,25,'OFFICER CAL',"POLICE: Fifth dead ROCKET GRUNT, fifth black feather. One per town, always on the same road.\n\nA calling card, and whoever leaves it is moving east."),
]
def build_native(r):
    r.cur=(r.cur+3)&~3; base=0x08000000+r.cur
    open(W+'/kills.ld','w').write('ENTRY(kill_check)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%base)
    subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-c',W+'/kills.c','-o',W+'/kills.o'],check=True)
    subprocess.run(['ld.lld','-T',W+'/kills.ld',W+'/kills.o','-o',W+'/kills.elf'],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',W+'/kills.elf',W+'/kills.bin'],check=True)
    blob=open(W+'/kills.bin','rb').read(); a=r.alloc(blob,4); assert 0x08000000+a==base
    sym=subprocess.run(['nm',W+'/kills.elf'],capture_output=True,text=True,check=True).stdout
    for ln in sym.split('\n'):
        f=ln.split()
        if len(f)==3 and f[2]=='kill_check': return (int(f[0],16)&~1)|1
def trainer(r,tid,species,level,name):
    b=r.b; o=T+40*tid; assert b[o+4]==0xff
    e=bytearray(40); e[0]=0; e[1]=CLASS_POLICE; e[2]=0; e[3]=PIC_POLICE
    nm=bytes(leg1.ENC[c] for c in name); e[4:16]=nm+b'\xff'*(12-len(nm)); e[28:32]=struct.pack('<I',1); e[32]=1
    pd=struct.pack('<HBBHH',160,level,0,species,0); e[36:40]=struct.pack('<I',0x08000000+r.alloc(pd,4)); b[o:o+40]=e
def install(r):
    fn=build_native(r)
    t_wanted=text(r,"POLICE: Wait, I recognize you! You're wanted for mass murder!")
    t_lost=text(r,"POLICE: Argh! Fine. You win this time. But I will remember your face.")
    t_after=text(r,"POLICE: Move along. And stay out of trouble.")
    for g,n,x,y,tid,sp,lv,name,comment in COPS:
        trainer(r,tid,sp,lv,name)
        h=header(r,g,n); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000; obj=None
        for i in range(r.b[ev]):
            if struct.unpack('<hh',r.b[po+24*i+4:po+24*i+8])==(x,y) and r.b[po+24*i+1]==60: obj=po+24*i
        assert obj,(g,n,x,y)
        S=SB(); S.lock(); S.faceplayer()
        S.raw(0x60); S._add(struct.pack('<H',tid)); S.goto_if(1,'done')
        S.msg(text(r,comment)); S.raw(0x23); S.ptr(fn)     # callnative kill_check -> var 0x8007
        S.compare(0x8007,1); S.goto_if(1,'fight')
        S.release(); S.end()
        S.lab('fight'); S.msg(t_wanted); S.raw(0x5c,3); S._add(struct.pack('<HH',tid,0)); S.ptr(t_lost)
        S.msg(t_after); S.release(); S.end()
        S.lab('done'); S.msg(t_after); S.release(); S.end()
        r.w32(obj+16,0x08000000+put_script(r,S))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
