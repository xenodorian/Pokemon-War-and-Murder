"""Viridian arrest: native code (usage: story_viri_native.py IN.gba OUT.gba), source story/viri_native.c. Table 'VIRIFN01' = viri_prepare, viri_cleanup (see addrs2)."""
import sys,struct,subprocess,os
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from inc import *
HERE=os.path.dirname(os.path.abspath(__file__)); SRC=os.path.join(HERE,'..','story'); WORK='/tmp/viri_build'
MAGIC=b'VIRIFN01'
def addrs2(r):
    i=bytes(r.b).find(MAGIC,0xA00000); assert i>0,'story_viri_native not applied'
    return dict(zip(('viri_prepare','viri_cleanup'),struct.unpack('<2I',r.b[i+8:i+16])))
def install(r):
    os.makedirs(WORK,exist_ok=True)
    r.cur=(r.cur+3)&~3; base=0x08000000+r.cur
    ld=os.path.join(WORK,'v.ld')
    open(ld,'w').write('ENTRY(viri_prepare)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%base)
    o=os.path.join(WORK,'v.o'); e=os.path.join(WORK,'v.elf'); bn=os.path.join(WORK,'v.bin')
    subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-c',os.path.join(SRC,'viri_native.c'),'-o',o],check=True)
    subprocess.run(['ld.lld','-T',ld,o,'-o',e],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',e,bn],check=True)
    a=r.alloc(open(bn,'rb').read(),4); assert 0x08000000+a==base
    sym={}
    for ln in subprocess.run(['nm',e],capture_output=True,text=True,check=True).stdout.split('\n'):
        f=ln.split()
        if len(f)==3: sym[f[2]]=int(f[0],16)
    fn=lambda n:(sym[n]&~1)|1
    r.alloc(MAGIC+struct.pack('<2I',fn('viri_prepare'),fn('viri_cleanup')),4)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
