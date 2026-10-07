import sys,struct,colorsys
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
from g3 import ENC
import gfx
from PIL import Image
MM=254; PK=25; NAT=386
PAL=0x23730c; SHINY=0x2380cc; LEARN=0x25d7b4
def text(s):
    o=bytearray()
    for c in s: o.append(0xFE if c=='\n' else ENC[c])
    o.append(0xFF); return bytes(o)
def sprite(path):
    s=Image.open(path).convert('RGBA'); assert s.size==(64,64)
    uc=[]
    for y in range(64):
        for x in range(64):
            c=s.getpixel((x,y))
            if c[3]>=128 and c[:3] not in uc: uc.append(c[:3])
    assert len(uc)<=15,len(uc)
    idx=[[(uc.index(s.getpixel((x,y))[:3])+1) if s.getpixel((x,y))[3]>=128 else 0 for x in range(64)] for y in range(64)]
    return uc,gfx.pixels_to_tiles(idx)
def shiny(c):
    h,l,sat=colorsys.rgb_to_hls(*[v/255 for v in c])
    if sat>0.15: h=(h+0.55)%1.0       # yellow -> blue/violet
    return tuple(int(v*255) for v in colorsys.hls_to_rgb(h,l,sat))
def apply(r,front='/home/claude/work/mimi/front.png',back='/home/claude/work/mimi/back.png'):
    b=r.b
    def cp(table,stride,dst,src,n=None):
        n=n or stride; b[table+stride*dst:table+stride*dst+n]=b[table+stride*src:table+stride*src+n]
    assert b[0x245ee0+11*MM:0x245ee0+11*MM+2]==text('?')[:1]+b'\xff'
    # sprites (front and back are separate images; both share one palette made from both)
    ucf,tf=sprite(front); ucb,tb=sprite(back)
    allc=list(ucf)+[c for c in ucb if c not in ucf]; assert len(allc)<=15
    def remap(path):
        s=Image.open(path).convert('RGBA')
        idx=[[(allc.index(s.getpixel((x,y))[:3])+1) if s.getpixel((x,y))[3]>=128 else 0 for x in range(64)] for y in range(64)]
        return gfx.pixels_to_tiles(idx)
    tf=remap(front); tb=remap(back)
    cols=[(255,0,255)]+allc+[(0,0,0)]*(15-len(allc))
    for tbl,data in ((0x2350ac,tf),(0x23654c,tb)):
        cp(tbl,8,MM,PK); r.w32(tbl+8*MM,0x08000000+r.alloc(gfx.lz_comp(data),4)); b[tbl+8*MM+6:tbl+8*MM+8]=struct.pack('<H',MM)
    r.w32(PAL+8*MM,0x08000000+r.alloc(gfx.lz_comp(gfx.rgb_to_pal(cols)),4)); b[PAL+8*MM+4:PAL+8*MM+6]=struct.pack('<H',MM)
    sc=cols[:1]+[shiny(c) for c in cols[1:]]
    r.w32(SHINY+8*MM,0x08000000+r.alloc(gfx.lz_comp(gfx.rgb_to_pal(sc)),4)); b[SHINY+8*MM+4:SHINY+8*MM+6]=struct.pack('<H',MM+500)
    cp(0x2349cc,4,MM,PK); cp(0x235e6c,4,MM,PK)                     # sprite coordinates (Pikachu's)
    cp(0x3d37a0,4,MM,PK); b[0x3d3e80+MM]=b[0x3d3e80+PK]; b[0x23a004+MM]=b[0x23a004+PK]   # party icon, icon palette, elevation
    for t in (0x48c914,0x48db44): cp(t,12,MM-1,PK-1)               # cry (Pikachu's)
    # base stats from the Mimikyu database page: 55/90/80/50/105/96 (HP/Atk/Def/SpA/SpD/Spe); ROM order HP/Atk/Def/Spe/SpA/SpD
    cp(0x254784,28,MM,PK); o=0x254784+28*MM
    b[o:o+6]=bytes([55,90,80,96,50,105]); b[o+6]=7; b[o+7]=7        # Ghost (no Fairy type exists in this ROM)
    b[o+8]=45; b[o+9]=167; b[o+10:o+12]=struct.pack('<H',2<<10); b[o+12:o+16]=bytes(4)   # catch rate 45, base exp 167, EV yield 2 SpDef
    b[o+16]=127; b[o+17]=20; b[o+18]=50; b[o+19]=0; b[o+20]=0x0b; b[o+21]=0x0b; b[o+22]=46; b[o+23]=0   # 50% male, 20 egg cycles, friendship 50, medium fast, Amorphous, Pressure
    nm=text('MIMIKYU'); b[0x245ee0+11*MM:0x245ee0+11*MM+11]=nm+b'\xff'*(11-len(nm))
    # TM/HM compatibility = HAUNTER | PIKACHU
    for i in range(8): b[0x252bc8+8*MM+i]=b[0x252bc8+8*93+i]|b[0x252bc8+8*PK+i]
    # learnset (Gen 3 moves chosen to match the page's level-up list where a move exists)
    L=[(1,10),(1,310),(1,150),(6,101),(12,104),(18,204),(24,102),(30,109),(36,163),(42,247),(48,174),(54,194),(60,220)]
    r.w32(LEARN+4*MM,0x08000000+r.alloc(b''.join(struct.pack('<H',(l<<9)|m) for l,m in L)+b'\xff\xff',2))
    b[0x259754+40*MM:0x259754+40*MM+40]=bytes(40)                    # no evolutions
    # pokedex: national slot 386 (DEOXYS' unused page), reached via species 254
    b[0x251fee+2*(MM-1):0x251fee+2*(MM-1)+2]=struct.pack('<H',NAT)
    d=0x44e850+36*NAT; h=0x44e850+36*PK
    cat=text('DISGUISE')[:-1]; cat=cat+b'\xff'*(12-len(cat)); b[d:d+12]=cat
    b[d+12:d+16]=struct.pack('<HH',2,7)                              # height 0.2 m, weight 0.7 kg
    r.w32(d+16,0x08000000+r.alloc(text("It hides under a cloth to avoid\nsunlight. Anyone who sees what\nlies beneath falls ill."),1)); r.w32(d+20,0x08000000+r.alloc(text(''),1))
    b[d+24:d+36]=b[h+24:h+36]
if __name__=='__main__':
    r=Rom(sys.argv[1]); apply(r); r.save(sys.argv[2])
