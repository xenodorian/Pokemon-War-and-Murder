# usage: church_interior.py in.gba out.gba
# Church interior (group 2 map 67): priest NPC next to a baptismal font, donation dialog that clears the kill count and removes the player's splatters.
import sys,struct,subprocess
sys.path.insert(0,'/home/claude/work/tools')
import numpy as np
from PIL import Image,ImageDraw
from inc import *
import gfx,leg1,shinigami
from leg1 import r32,header
from shinigami import SB,put_script,tiles_from_pixels
W='/home/claude/work/church'
GROUPS=0x3526A8
NEWGRP,NEWNUM=2,67
PRIEST_TAG=0x1121; HIDE_FLAG=0x4AC
SE_FORGIVE=0x1f   # placeholder, replaced below if a fanfare is wanted
# ------------------------------------------------------------------ native code
def build_native(r):
    r.cur=(r.cur+3)&~3; base=0x08000000+r.cur
    open(W+'/church.ld','w').write('ENTRY(kill_price)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%base)
    subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables']+__import__('os').environ.get('CHURCH_CFLAGS','').split()+['-c',W+'/church.c','-o',W+'/church.o'],check=True)
    subprocess.run(['ld.lld','-T',W+'/church.ld',W+'/church.o','-o',W+'/church.elf'],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',W+'/church.elf',W+'/church.bin'],check=True)
    blob=open(W+'/church.bin','rb').read(); a=r.alloc(blob,4); assert 0x08000000+a==base
    sym=subprocess.run(['nm',W+'/church.elf'],capture_output=True,text=True,check=True).stdout
    out={}
    for ln in sym.split('\n'):
        f=ln.split()
        if len(f)==3 and f[2] in ('kill_price','kill_forgive','apply_killed2'): out[f[2]]=(int(f[0],16)&~1)|1
    assert len(out)==3
    return out
def hook_apply_killed(r,fn):
    """the original shot-trainer pass (dead code from here on) jumps straight to the new one; both map-load wrappers keep working"""
    o=0xa0981c; assert r.b[o]==0xb5 or r.b[o+1]==0xb5, r.b[o:o+4].hex()
    r.b[o:o+8]=bytes.fromhex('014b1847c046c046'); r.w32(o+8,fn)
# ------------------------------------------------------------------ art
def load_art():
    fi=np.load(W+'/font_idx.npy'); fc=np.load(W+'/font_col.npy')          # 32x16 canvas, art bottom at row 29, indices 1..9
    rows=np.where(fi.any(1))[0]; art=fi[rows.min():rows.max()+1]
    font=np.zeros((32,16),int); font[32-len(art):]=art
    pi=np.load(W+'/priest_final_idx.npy'); pc=np.load(W+'/priest_final_col.npy')
    return font,[tuple(int(v) for v in c) for c in fc],pi,[tuple(int(v) for v in c) for c in pc]
EXTRA=[(176,40,48),(128,24,40),(224,176,56),(160,116,70),(190,142,90)]       # palette idx 10..14: red, dark red, gold, wood, light wood
def pew_runner():
    im=Image.new('P',(32,16),0); d=ImageDraw.Draw(im)
    d.rectangle([0,3,31,8],fill=13,outline=8); d.line([(3,4),(28,4)],fill=14)
    d.rectangle([0,9,31,13],fill=14,outline=8); d.line([(3,12),(28,12)],fill=13)
    d.rectangle([0,3,2,14],fill=9,outline=8); d.rectangle([29,3,31,14],fill=9,outline=8)
    d.line([(1,15),(30,15)],fill=8)
    pew=np.array(im)
    ru=Image.new('P',(16,16),0); d=ImageDraw.Draw(ru)
    d.rectangle([2,0,13,15],fill=10); d.line([(2,0),(2,15)],fill=12); d.line([(13,0),(13,15)],fill=12)
    d.line([(4,0),(4,15)],fill=11); d.line([(11,0),(11,15)],fill=11)
    for y in range(2,16,6): d.rectangle([6,y,9,y+2],fill=12)
    return pew,np.array(ru)
def tiles_of(a16):
    """16x16 index array -> 4 tiles (tl,tr,bl,br) as 32-byte 4bpp strings"""
    out=[]
    for ty in range(2):
        for tx in range(2):
            t=a16[ty*8:ty*8+8,tx*8:tx*8+8]; b=bytearray(32)
            for y in range(8):
                for x in range(4): b[y*4+x]=int(t[y,2*x])|(int(t[y,2*x+1])<<4)
            out.append(bytes(b))
    return out
# ------------------------------------------------------------------ sprite palette + object graphics
def add_sprite_palette(r,tag,cols):
    b=r.b; pt=r32(r,0x5f4d8)-0x08000000; ents=[]; n=0
    while True:
        e=bytes(b[pt+8*n:pt+8*n+8]); t=struct.unpack('<H',e[4:6])[0]
        if t==0x11ff: term=e; break
        ents.append(e); n+=1
    pal=r.alloc(gfx.rgb_to_pal(([(255,0,255)]+cols+[(0,0,0)]*16)[:16]),4)
    ents.append(struct.pack('<IHH',0x08000000+pal,tag,0))
    new=r.alloc(b''.join(ents)+term,4)
    for lit in (0x5f4d8,0x5f570,0x5f5c8):
        assert r32(r,lit)==0x08000000+pt,hex(lit); r.w32(lit,0x08000000+new)
def add_priest_gfx(r,pi,pc,src=60):
    b=r.b
    add_sprite_palette(r,PRIEST_TAG,pc)
    idx=[[int(v) for v in row] for row in pi]
    t=tiles_from_pixels(idx,2,4)
    ptr=r.alloc(t,4)
    imgt=r.alloc(b''.join(struct.pack('<IHH',0x08000000+ptr,0x100,0) for _ in range(9)),4)
    gt=r32(r,0x5f2f4)-0x08000000; mx=b[0x5f2e0]
    ib=r32(r,gt+4*src)-0x08000000
    info=bytearray(b[ib:ib+36]); info[2:4]=struct.pack('<H',PRIEST_TAG); info[0x1c:0x20]=struct.pack('<I',0x08000000+imgt); info[12]=(info[12]&0xF0)|10
    ia=r.alloc(bytes(info),4)
    new=r.alloc(bytes(b[gt:gt+4*(mx+1)])+struct.pack('<I',0x08000000+ia),4)
    r.w32(0x5f2f4,0x08000000+new); b[0x5f2e0]=mx+1
    return mx+1
# ------------------------------------------------------------------ the map
def install(r,fns,gfx_id):
    b=r.b
    hh=header(r,4,0); hlay=r32(r,hh)-0x08000000
    P=r32(r,hlay+16)-0x08000000; S=r32(r,hlay+20)-0x08000000
    assert b[S+1]==1
    s_tiles=r32(r,S+4)-0x08000000; s_pals=r32(r,S+8)-0x08000000; s_mt=r32(r,S+12)-0x08000000; s_at=r32(r,S+20)-0x08000000
    nmt=(s_at-s_mt)//16; assert nmt==24,nmt
    p_mt=r32(r,P+12)-0x08000000
    font,fcols,pi,pc=load_art(); pew,runner=pew_runner()
    pal_cols=fcols+EXTRA; assert len(pal_cols)==14
    tiles=bytearray(gfx.lz_decomp(b,s_tiles)); nt=len(tiles)//32; assert nt==63
    new=[]; seen={}
    def tid(t):
        if t not in seen: seen[t]=640+nt+len(new); new.append(t)
        return seen[t]
    floor=[struct.unpack('<H',b[p_mt+16*1+2*i:p_mt+16*1+2*i+2])[0] for i in range(4)]
    mts=[]
    def metatile(a16):
        tl=tiles_of(a16); top=[]
        for t in tl:
            top.append(0 if t==bytes(32) else (7<<12)|tid(t))
        mts.append(floor+top); return 640+nmt+len(mts)-1
    MT_FONT_TOP=metatile(font[:16]); MT_FONT_BOT=metatile(font[16:])
    MT_PEW_L=metatile(pew[:, :16]); MT_PEW_R=metatile(pew[:,16:]); MT_RUN=metatile(runner)
    # secondary tileset copy
    ta=r.alloc(gfx.lz_comp(bytes(tiles)+b''.join(new)),4)
    pal=bytearray(b[s_pals:s_pals+512])
    for i,c in enumerate([(0,0,0)]+pal_cols): pal[7*32+2*i:7*32+2*i+2]=gfx.rgb_to_pal([c])
    pa=r.alloc(bytes(pal),4)
    mt=bytearray(b[s_mt:s_mt+16*nmt])
    for m in mts: mt+=struct.pack('<8H',*m)
    ma=r.alloc(bytes(mt),4)
    at=bytearray(b[s_at:s_at+4*nmt])
    for m in mts: at+=struct.pack('<I',0x20000000)
    aa=r.alloc(bytes(at),4)
    H=bytearray(b[S:S+24]); H[4:8]=struct.pack('<I',0x08000000+ta); H[8:12]=struct.pack('<I',0x08000000+pa); H[12:16]=struct.pack('<I',0x08000000+ma); H[20:24]=struct.pack('<I',0x08000000+aa)
    sec=r.alloc(bytes(H),4)
    # blocks
    w,h=9,11
    WALK=0x3000; SOLID=0x0400
    g=[[8|SOLID]*w for _ in range(h)]
    row0=[32,33,34,32,33,34,32]; row1=[40,41,42,40,41,42,40]
    for i in range(7): g[0][1+i]=row0[i]|SOLID; g[1][1+i]=row1[i]|SOLID
    for y in range(2,10):
        for x in range(1,8): g[y][x]=1|WALK
    for x,m in zip((3,4,5),(18,19,20)): g[9][x]=m|WALK
    g[2][1]=71|SOLID; g[2][7]=71|SOLID
    g[2][5]=MT_FONT_TOP|SOLID; g[3][5]=MT_FONT_BOT|SOLID
    for y in (5,7):
        for x,m in ((2,MT_PEW_L),(3,MT_PEW_R),(5,MT_PEW_L),(6,MT_PEW_R)): g[y][x]=m|SOLID
    for y in range(5,9): g[y][4]=MT_RUN|WALK
    blocks=r.alloc(b''.join(struct.pack('<H',v) for row in g for v in row),4)
    border=r.alloc(bytes(b[r32(r,hlay+8)-0x08000000:r32(r,hlay+8)-0x08000000+8]),4)
    lay=r.alloc(struct.pack('<IIIIII',w,h,0x08000000+border,0x08000000+blocks,r32(r,hlay+16),0x08000000+sec)+bytes([2,2,0,0]),4)
    # priest script
    t_none=shinigami.text(r,"PRIEST: Welcome to the church, child.\n\nI see no blood on your hands. Go in peace.")
    t_intro=shinigami.text(r,"PRIEST: Welcome, child. I can see the blood on your hands.\n\nThe church can forgive any sin.\n\nFor a small donation, of course.")
    t_ask=r.alloc(leg1.enc("PRIEST: Your donation is $")[:-1]+b'\xfd\x02'+leg1.enc(".\n\nWill you give it?"),1); t_ask=0x08000000+t_ask
    t_no=shinigami.text(r,"PRIEST: Then the weight stays with you. The church will wait.")
    t_poor=shinigami.text(r,"PRIEST: You cannot afford the donation. Come back when you can.")
    t_bless=shinigami.text(r,"PRIEST: Bless you, child.\n\nYour sins are forgiven, and the dead are laid to rest. Go in peace.")
    S_=SB(); S_.lock(); S_.faceplayer()
    S_.raw(0x23); S_.ptr(fns['kill_price'])
    S_.compare(0x8007,0); S_.goto_if(1,'none')
    S_.msg(t_intro); S_.msg(t_ask,5)
    S_.compare(0x800d,0); S_.goto_if(1,'no')
    for k in range(1,11): S_.compare(0x8007,k); S_.goto_if(1,'p%d'%k)
    for k in range(1,11):
        price=min(1000*k,9999)
        S_.lab('p%d'%k); S_.raw(0x92); S_._add(struct.pack('<IB',price,0)); S_.compare(0x800d,0); S_.goto_if(1,'poor')
        S_.raw(0x91); S_._add(struct.pack('<IB',price,0)); S_.goto('paid')
    S_.lab('paid'); S_.raw(0x23); S_.ptr(fns['kill_forgive']); S_.setflag(HIDE_FLAG); S_.msg(t_bless); S_.release(); S_.end()
    S_.lab('none'); S_.msg(t_none); S_.release(); S_.end()
    S_.lab('no'); S_.msg(t_no); S_.release(); S_.end()
    S_.lab('poor'); S_.msg(t_poor); S_.release(); S_.end()
    sc=put_script(r,S_)
    # events
    ob=bytearray(24); ob[0]=1; ob[1]=gfx_id; ob[4:6]=struct.pack('<h',4); ob[6:8]=struct.pack('<h',3); ob[8]=3; ob[9]=8; ob[16:20]=struct.pack('<I',0x08000000+sc)
    oa=r.alloc(bytes(ob),4)
    PAL_WARP=6
    wb=b''.join(struct.pack('<hhBBBB',x,9,0,PAL_WARP+(0 if x!=5 else 1),0,3) for x in (3,4,5))+struct.pack('<hhBBBB',4,8,0,PAL_WARP,0,3)   # exits on the mat row; warp 3 is the arrival tile one step inside the door
    wa=r.alloc(wb,4)
    ev=r.alloc(bytes([1,4,0,0])+struct.pack('<IIII',0x08000000+oa,0x08000000+wa,0,0),4)
    ms=r.alloc(b'\x00',1)
    hb=bytearray(b[hh:hh+28]); hb[0:4]=struct.pack('<I',0x08000000+lay); hb[4:8]=struct.pack('<I',0x08000000+ev); hb[8:12]=struct.pack('<I',0x08000000+ms); hb[12:16]=bytes(4)
    # layout id + group table
    LT=r32(r,0x55194)-0x08000000; NL=390
    for k in range(383,NL):
        lp=r32(r,LT+4*k)-0x08000000; assert 4<=r32(r,lp)<=40 and 4<=r32(r,lp+4)<=40,k
    # the tower floors were added with 24-byte layout structs (no border size bytes): give them proper 28-byte copies
    g2=r32(r,GROUPS+8)-0x08000000
    ents=bytearray(b[LT:LT+4*NL])
    for k in range(383,NL):
        lp=r32(r,LT+4*k)-0x08000000
        if b[lp+0x18:lp+0x1a]!=bytes([2,2]):
            nl=r.alloc(bytes(b[lp:lp+24])+bytes([2,2,0,0]),4); ents[4*k:4*k+4]=struct.pack('<I',0x08000000+nl)
            hp=r32(r,g2+4*(60+k-383))-0x08000000; assert r32(r,hp)==0x08000000+lp,k; r.w32(hp,0x08000000+nl)
    tab=r.alloc(bytes(ents)+struct.pack('<I',0x08000000+lay),4); r.w32(0x55194,0x08000000+tab)
    hb[18:20]=struct.pack('<H',NL+1)
    SEC=0xb8                                                  # unused Sevii section, renamed
    r.w32(0x3f1cac+4*(SEC-0x58),0x08000000+r.alloc(leg1.enc('CHURCH OF FORGIVENESS'),1))
    hb[20]=SEC
    hb[0x1a]=100                                              # floorNum 100: wide popup window, and the floor suffix is suppressed (patched below)
    hb[25]|=0x04                                              # showMapName: the name popup appears on entering the church
    assert bytes(b[0x98486:0x98488])==bytes([0x00,0x29])
    b[0x98486:0x98488]=bytes([0x64,0x29])                     # MapNamePopupAppendFloorNum: floor 100 appends nothing
    hdr=r.alloc(bytes(hb),4)
    g2=r32(r,GROUPS+8)-0x08000000
    for k in (60,66):
        hp=r32(r,g2+4*k)-0x08000000; assert 0x08000000<=r32(r,hp)<0x0a000000,k
    ntab=r.alloc(bytes(b[g2:g2+4*NEWNUM])+struct.pack('<I',0x08000000+hdr),4); r.w32(GROUPS+8,0x08000000+ntab)
    # ---- Pallet Town: church door warps at (7,15) and (8,15)
    ph=header(r,3,0); pev=r32(r,ph+4)-0x08000000
    # ---- the sign beside the church
    bpp=r32(r,pev+16)-0x08000000
    found=0
    for i in range(b[pev+3]):
        o=bpp+12*i
        if struct.unpack('<HH',b[o:o+4])==(10,11):
            Ssg=SB(); Ssg.msg(shinigami.text(r,"THE CHURCH OF FORGIVENESS\n\nPALLET TOWN! Boring, crappy and small."),3); Ssg.end()
            r.w32(o+8,0x08000000+put_script(r,Ssg)); found+=1
    assert found==1
    nw=b[pev+1]; assert nw==4
    wp=r32(r,pev+8)-0x08000000
    ws=bytes(b[wp:wp+8*nw])+b''.join(struct.pack('<hhBBBB',x,15,0,3,NEWNUM,NEWGRP) for x in (7,8))+b''.join(struct.pack('<hhBBBB',x,16,0,3,NEWNUM,NEWGRP) for x in (7,8))   # doors, then the plain tiles in front of them (where people leaving the church arrive)
    b[pev+1]=8; r.w32(pev+8,0x08000000+r.alloc(ws,4))
    pl=r32(r,ph)-0x08000000; pmp=r32(r,pl+12)-0x08000000; pw=r32(r,pl)
    for x in (7,8):
        o=pmp+2*(15*pw+x); v=struct.unpack('<H',b[o:o+2])[0]; b[o:o+2]=struct.pack('<H',(v&0x3ff)|0x3000)
    # door tiles: regular warp behaviour (0x67) so stepping onto them warps
    sec=r32(r,pl+20)-0x08000000; sat=r32(r,sec+20)-0x08000000
    for x in (7,8):
        o=pmp+2*(15*pw+x); m=struct.unpack('<H',b[o:o+2])[0]&0x3ff; assert m>=640
        b[sat+4*(m-640):sat+4*(m-640)+4]=struct.pack('<I',0x20000067)
if __name__=='__main__':
    r=Rom(sys.argv[1])
    fns=build_native(r); hook_apply_killed(r,fns['apply_killed2'])
    font,fc,pi,pc=load_art()
    gid=add_priest_gfx(r,pi,pc)
    install(r,fns,gid)
    r.save(sys.argv[2]); print('priest gfx',hex(gid),'end',hex(r.cur))
