"""Viridian arrest: native code (usage: story_viri_native.py IN.gba OUT.gba), source story/viri_native.c. Table 'VIRIFN01' = viri_prepare, viri_cleanup (see addrs2)."""
import sys,struct,subprocess,os
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from inc import *
HERE=os.path.dirname(os.path.abspath(__file__)); SRC=os.path.join(HERE,'..','story'); WORK='/tmp/viri_build'
MAGIC=b'VIRIFN01'
def addrs2(r):
    i=bytes(r.b).find(MAGIC,0xA00000); assert i>0,'story_viri_native not applied'
    return dict(zip(('viri_prepare','viri_cleanup'),struct.unpack('<2I',r.b[i+8:i+16])))
def max_header():
    from PIL import Image
    im=Image.open(os.path.join(HERE,'..','story_assets','chars','max_back.png')).convert('RGBA')
    pal=[]
    for q in im.getdata():
        if q[3]>0 and q[:3] not in pal: pal.append(q[:3])
    assert len(pal)<=15,len(pal)
    px=list(im.getdata()); idx=[0 if q[3]==0 else pal.index(q[:3])+1 for q in px]
    t=bytearray()
    for ty in range(8):
        for tx in range(8):
            for y in range(8):
                for x in range(0,8,2):
                    t.append(idx[(ty*8+y)*64+tx*8+x]|(idx[(ty*8+y)*64+tx*8+x+1]<<4))
    cols=[(0,0,0)]+pal+[(0,0,0)]*(15-len(pal))
    w=[(c[0]>>3)|((c[1]>>3)<<5)|((c[2]>>3)<<10) for c in cols]
    return 'const unsigned char max_pic[2048]={%s};\nconst unsigned short max_pal[16]={%s};\n'%(','.join(map(str,t)),','.join(map(str,w)))
def install(r):
    os.makedirs(WORK,exist_ok=True); open(os.path.join(WORK,'max_pic.h'),'w').write(max_header())
    os.makedirs(WORK,exist_ok=True)
    r.cur=(r.cur+3)&~3; base=0x08000000+r.cur
    ld=os.path.join(WORK,'v.ld')
    open(ld,'w').write('ENTRY(viri_prepare)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%base)
    o=os.path.join(WORK,'v.o'); e=os.path.join(WORK,'v.elf'); bn=os.path.join(WORK,'v.bin')
    subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-I',WORK,'-c',os.path.join(SRC,'viri_native.c'),'-o',o],check=True)
    subprocess.run(['ld.lld','-T',ld,o,'-o',e],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',e,bn],check=True)
    a=r.alloc(open(bn,'rb').read(),4); assert 0x08000000+a==base
    sym={}
    for ln in subprocess.run(['nm',e],capture_output=True,text=True,check=True).stdout.split('\n'):
        f=ln.split()
        if len(f)==3: sym[f[2]]=int(f[0],16)
    fn=lambda n:(sym[n]&~1)|1
    r.alloc(MAGIC+struct.pack('<2I',fn('viri_prepare'),fn('viri_cleanup')),4)
    # the player controller's command table (sPlayerBufferCommands): CHOOSEACTION (18) and CHOOSEMOVE (20) go through the partner wrappers
    T=0x25089c
    assert struct.unpack('<I',r.b[T+72:T+76])[0]==0x08032bd5 and struct.unpack('<I',r.b[T+80:T+84])[0]==0x08032c91
    r.w32(T+72,fn('partner_choose_action')); r.w32(T+80,fn('partner_choose_move'))
    assert struct.unpack('<I',r.b[T+28:T+32])[0]==0x0803227d
    r.w32(T+28,fn('partner_draw_pic'))     # DRAWTRAINERPIC (7): LEAF's pic, plus MAX's back pic beside it while MAX is the partner
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
