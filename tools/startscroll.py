# usage: startscroll.py in.gba out.gba
# Scrolling pause menu: at most 7 rows above the description box, one-row scroll at the ends of the view, KILL COUNT as a top-level entry.
import sys,struct,subprocess,json
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import leg2
W='/home/claude/work/scroll'
ACTARR=0x20370f6            # sCurrentStartMenuActions grows from 9 to 11 bytes by moving the 2-byte draw state into the padding at 0x2037102
VEN=0x3b21d8                # free padding inside BL range of the start menu code
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
def build(r,tbl):
    open(W+'/scroll_data.h','w').write('#define TBL 0x%08x\n#define ACTARR 0x%08x\n'%(tbl,ACTARR))
    r.cur=(r.cur+3)&~3; base=0x08000000+r.cur
    open(W+'/scroll.ld','w').write('ENTRY(psm)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%base)
    subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-c',W+'/scroll.c','-o',W+'/scroll.o'],check=True)
    subprocess.run(['ld.lld','-T',W+'/scroll.ld',W+'/scroll.o','-o',W+'/scroll.elf'],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',W+'/scroll.elf',W+'/scroll.bin'],check=True)
    a=r.alloc(open(W+'/scroll.bin','rb').read(),4); assert 0x08000000+a==base
    out={}
    for ln in subprocess.run(['nm',W+'/scroll.elf'],capture_output=True,text=True,check=True).stdout.split('\n'):
        f=ln.split()
        if len(f)==3 and f[2] in ('psm','init_cursor','scroll_move','win_h'): out[f[2]]=(int(f[0],16)&~1)|1
    assert len(out)==4
    return out
def veneer(r,slot,target):
    # Thumb to ARM veneer that keeps r0-r3 and the stack intact: bx pc / nop / ldr ip,[pc] / bx ip / .word target
    at=VEN+16*slot
    r.put(at,struct.pack('<HHIII',0x4778,0x46c0,0xe59fc000,0xe12fff1c,target))
    return at
def patch_bl(r,at,old,veneer_at):
    h1,h2=struct.unpack('<HH',r.b[at:at+4])
    off=((h1&0x7FF)<<12)|((h2&0x7FF)<<1)
    if off&0x400000: off-=0x800000
    assert at+4+off==old,(hex(at),hex(at+4+off))
    r.bl(at,veneer_at)
if __name__=='__main__':
    r=Rom(sys.argv[1]); b=r.b
    fns=json.load(open('/home/claude/work/leg2/fns.json'))
    leg2.menu_entry(r,fns)                                   # KILL COUNT becomes action 11, after RENAME
    n0=n1=0
    for o in range(0,0xa00000,4):
        v=r32(r,o)
        if v==0x020370ff: r.w32(o,0x02037102); n0+=1
        elif v==0x02037100: r.w32(o,0x02037103); n1+=1
    assert (n0,n1)==(7,1),(n0,n1)
    tbl=r32(r,0x6ef9c); assert tbl==r32(r,0x6f374)==r32(r,0x6f3f8)
    f=build(r,tbl)
    v={k:veneer(r,i,f[k]) for i,k in enumerate(('init_cursor','scroll_move','win_h'))}
    patch_bl(r,0x6f0e2,0x10f7d8,v['init_cursor'])
    patch_bl(r,0x6f298,0x10f904,v['scroll_move']); patch_bl(r,0x6f2e6,0x10f904,v['scroll_move'])
    patch_bl(r,0x6f074,0xf78e0,v['win_h'])
    assert bytes(b[0x6ef44:0x6ef46])==bytes([0xf0,0xb5])
    b[0x6ef44:0x6ef50]=struct.pack('<HHHHI',0x4a01,0x4710,0x46c0,0x46c0,f['psm'])
    r.save(sys.argv[2]); print('ok',{k:hex(x) for k,x in f.items()},'end',hex(r.cur))
