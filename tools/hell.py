# usage: hell.py in.gba out.gba
# HELL: a lava map (group 2, map 68) reached from the Spirit Witch, with level 40-50 Dark and Fire wild Pokemon and an exit portal back to Celadon City.
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import numpy as np
from inc import *
import gfx,leg1,shinigami
from leg1 import r32,header
from shinigami import SB,put_script,add_coord
import hell_art as art
GROUPS=0x3526A8
NEWGRP,NEWNUM=2,68
W,H=22,26
START=(11,23); PORTAL=(11,3)
EXIT_TO=(3,6,30,28)               # Celadon City, beside the Spirit Witch
WILD=[(229,42,46),(126,40,44),(198,40,44),(215,42,46),(38,44,48),(78,42,46),(228,40,45),(219,44,48),(59,46,50),(197,46,50),(6,48,50),(248,48,50)]
def grid():
    g=[['~']*W for _ in range(H)]
    for x in range(W): g[0][x]=g[1][x]=g[H-1][x]=g[H-2][x]='#'
    for y in range(H): g[y][0]=g[y][1]=g[y][W-1]=g[y][W-2]='#'
    pts=[(11,23),(11,20),(5,20),(5,15),(16,15),(16,10),(8,10),(8,5),(11,5),(11,3)]
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        n=max(abs(x1-x0),abs(y1-y0))
        for i in range(n+1):
            x=x0+round((x1-x0)*i/n) if n else x0; y=y0+round((y1-y0)*i/n) if n else y0
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if 2<=x+dx<W-2 and 2<=y+dy<H-2: g[y+dy][x+dx]='.'
    # rock pillars in the lava
    for (x,y) in ((3,6),(18,6),(4,12),(18,18),(3,23),(18,22),(12,12),(13,7)):
        if g[y][x]=='~': g[y][x]='#'
    g[PORTAL[1]][PORTAL[0]]='P'
    return g
def install(r):
    b=r.b
    hh=header(r,4,0)
    # take the church interior's secondary tileset header as the base (same primary)
    ch=header(r,NEWGRP,67); clay=r32(r,ch)-0x08000000
    PRIM=r32(r,clay+16); SEC=r32(r,clay+20)-0x08000000
    tiles=[art.floor(1),art.floor(2),art.lava(1),art.lava(2),art.rock(1),art.portal()]
    def tb(a16):
        out=[]
        for ty in range(2):
            for tx in range(2):
                t=a16[ty*8:ty*8+8,tx*8:tx*8+8]; bb=bytearray(32)
                for y in range(8):
                    for x in range(4): bb[y*4+x]=int(t[y,2*x])|(int(t[y,2*x+1])<<4)
                out.append(bytes(bb))
        return out
    tl=[];mts=[]
    for a in tiles:
        base=len(tl); tl+=tb(a)
        mts.append([(7<<12)|(640+base+i) for i in range(4)]+[0,0,0,0])
    ta=r.alloc(gfx.lz_comp(b''.join(tl)),4)
    pal=bytearray(512)
    for i,c in enumerate([(0,0,0)]+art.PAL): pal[7*32+2*i:7*32+2*i+2]=gfx.rgb_to_pal([c])
    pa=r.alloc(bytes(pal),4)
    ma=r.alloc(b''.join(struct.pack('<8H',*m) for m in mts),4)
    FLOOR_ATTR=0x01000000|0x20000000    # land encounters
    at=[FLOOR_ATTR,FLOOR_ATTR,0x20000000,0x20000000,0x20000000,0x20000067|0x01000000]
    aa=r.alloc(b''.join(struct.pack('<I',a) for a in at),4)
    Hd=bytearray(b[SEC:SEC+24]); Hd[4:8]=struct.pack('<I',0x08000000+ta); Hd[8:12]=struct.pack('<I',0x08000000+pa); Hd[12:16]=struct.pack('<I',0x08000000+ma); Hd[20:24]=struct.pack('<I',0x08000000+aa)
    Hd[16:20]=bytes(4)
    sec=r.alloc(bytes(Hd),4)
    ids={'.':(640,640+1),'~':(642,643),'#':(644,),'P':(645,)}
    g=grid(); rs=np.random.RandomState(5)
    vals=[]
    for y in range(H):
        for x in range(W):
            c=g[y][x]
            if c=='.': v=(640+(rs.randint(0,2)))|0x3000
            elif c=='~': v=(642+(rs.randint(0,2)))|0x0400
            elif c=='#': v=644|0x0400
            else: v=645|0x3000
            vals.append(v)
    blocks=r.alloc(b''.join(struct.pack('<H',v) for v in vals),4)
    border=r.alloc(struct.pack('<4H',644|0x400,644|0x400,644|0x400,644|0x400),4)
    lay=r.alloc(struct.pack('<IIIIII',W,H,0x08000000+border,0x08000000+blocks,PRIM,0x08000000+sec)+bytes([2,2,0,0]),4)
    # exit portal script
    S=SB(); S.lockall(); S.msg(shinigami.text(r,"The portal drags you out of the flames."),4)
    S.raw(0x3d,EXIT_TO[0],EXIT_TO[1],0xff); S._add(struct.pack('<HH',EXIT_TO[2],EXIT_TO[3])); S.raw(0x27); S.releaseall(); S.end()
    sc=put_script(r,S)
    coord=struct.pack('<HHBBHHHI',PORTAL[0],PORTAL[1],3,0,0x40F6,0,0,0x08000000+sc)
    ca=r.alloc(coord,4)
    ev=r.alloc(bytes([0,0,1,0])+struct.pack('<IIII',0,0,0x08000000+ca,0),4)
    ms=r.alloc(b'\x00',1)
    hb=bytearray(b[ch:ch+28]); hb[0:4]=struct.pack('<I',0x08000000+lay); hb[4:8]=struct.pack('<I',0x08000000+ev); hb[8:12]=struct.pack('<I',0x08000000+ms)
    hb[20]=0xb9; hb[21]=0
    # layout id + tables
    LT=r32(r,0x55194)-0x08000000; NL=391
    for k in (383,390): lp=r32(r,LT+4*k)-0x08000000; assert 4<=r32(r,lp)<=60
    tab=r.alloc(bytes(b[LT:LT+4*NL])+struct.pack('<I',0x08000000+lay),4); r.w32(0x55194,0x08000000+tab)
    hb[18:20]=struct.pack('<H',NL+1)
    hdr=r.alloc(bytes(hb),4)
    g2=r32(r,GROUPS+8)-0x08000000
    for k in (60,67): hp=r32(r,g2+4*k)-0x08000000; assert 0x08000000<=r32(r,hp)<0x0a000000,k
    ntab=r.alloc(bytes(b[g2:g2+4*NEWNUM])+struct.pack('<I',0x08000000+hdr),4); r.w32(GROUPS+8,0x08000000+ntab)
    # map name
    r.w32(0x3f1cac+4*(0xb9-0x58),0x08000000+r.alloc(leg1.enc('HELL'),1))
    # wild encounters
    mons=r.alloc(b''.join(struct.pack('<BBH',lo,hi,sp) for sp,lo,hi in WILD),4)
    info=r.alloc(struct.pack('<BxxxI',25,0x08000000+mons),4)
    WT=r32(r,0x82990)-0x08000000; n=0
    while b[WT+20*n]!=0xff: n+=1
    assert n==132,n
    ent=struct.pack('<BBHIIII',NEWGRP,NEWNUM,0,0x08000000+info,0,0,0)
    newwt=r.alloc(bytes(b[WT:WT+20*n])+ent+bytes(b[WT+20*n:WT+20*n+20]),4)
    old=struct.pack('<I',0x08000000+WT); k=0; n_ref=0
    while True:
        k=bytes(b).find(old,k)
        if k<0: break
        if k<0x200000 and k%4==0: r.w32(k,0x08000000+newwt); n_ref+=1
        k+=1
    assert n_ref==14,n_ref
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))
